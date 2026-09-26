from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounting.models import Journal, JournalEntry, JournalItem, Account


class AccountingService:
    @staticmethod
    def _get_or_create_journal(company, code, name, journal_type):
        journal, _ = Journal.objects.get_or_create(
            company=company,
            code=code,
            defaults={
                'name': name,
                'type': journal_type,
            }
        )
        return journal

    @staticmethod
    def _get_account_by_code(company, code):
        return Account.objects.get(
            company=company,
            code=code,
            is_deleted=False
        )

    @staticmethod
    @transaction.atomic
    def create_purchase_invoice_entry(
        invoice,
        inventory_account_code='1004',
        payable_account_code='2001'
    ):
        """
        إنشاء قيد محاسبي لفاتورة مشتريات:
        - مدين: المخزون
        - دائن: المورد
        """

        if getattr(invoice, 'journal_entry_id', None):
            return invoice.journal_entry

        journal = AccountingService._get_or_create_journal(
            company=invoice.company,
            code='PUR',
            name='دفتر المشتريات',
            journal_type='purchase'
        )

        if JournalEntry.objects.filter(
            company=invoice.company,
            reference=invoice.invoice_number,
            journal=journal,
            is_deleted=False
        ).exists():
            raise ValidationError("تم إنشاء قيد لهذه الفاتورة مسبقًا.")

        total_purchase_amount = Decimal(invoice.total_amount or Decimal('0.00'))
        if total_purchase_amount <= Decimal('0.00'):
            raise ValidationError("لا يمكن إنشاء قيد لفاتورة مشتريات بإجمالي صفر.")

        inventory_acc = AccountingService._get_account_by_code(invoice.company, inventory_account_code)
        payable_acc = AccountingService._get_account_by_code(invoice.company, payable_account_code)

        entry = JournalEntry.objects.create(
            company=invoice.company,
            journal=journal,
            date=invoice.invoice_date,
            reference=invoice.invoice_number,
            notes=f"إثبات فاتورة مشتريات رقم {invoice.invoice_number} - المورد: {invoice.supplier.name}",
            status='draft',
        )

        JournalItem.objects.create(
            entry=entry,
            account=inventory_acc,
            description=f"إثبات مخزون من فاتورة مشتريات {invoice.invoice_number}",
            debit=total_purchase_amount,
            credit=Decimal('0.00')
        )

        JournalItem.objects.create(
            entry=entry,
            account=payable_acc,
            partner=invoice.supplier,
            description=f"استحقاق على المورد - فاتورة {invoice.invoice_number}",
            debit=Decimal('0.00'),
            credit=total_purchase_amount
        )

        entry.post()

        return entry

    @staticmethod
    @transaction.atomic
    def create_sales_invoice_entry(
        invoice,
        receivable_account_code='1003',
        revenue_account_code='4001',
        cogs_account_code='5001',
        inventory_account_code='1004'
    ):
        """
        إنشاء قيد محاسبي لفاتورة مبيعات آجل:
        - مدين: العملاء
        - دائن: الإيرادات
        """

        if getattr(invoice, 'journal_entry_id', None):
            return invoice.journal_entry

        journal = AccountingService._get_or_create_journal(
            company=invoice.company,
            code='SAL',
            name='دفتر المبيعات',
            journal_type='sale'
        )

        if JournalEntry.objects.filter(
            company=invoice.company,
            reference=invoice.invoice_number,
            journal=journal,
            is_deleted=False
        ).exists():
            raise ValidationError("تم إنشاء قيد لهذه الفاتورة مسبقًا.")

        receivable_acc = AccountingService._get_account_by_code(invoice.company, receivable_account_code)
        revenue_acc = AccountingService._get_account_by_code(invoice.company, revenue_account_code)
        cogs_acc = AccountingService._get_account_by_code(invoice.company, cogs_account_code)
        inventory_acc = AccountingService._get_account_by_code(invoice.company, inventory_account_code)

        total_sales_amount = Decimal(invoice.total_amount or Decimal('0.00'))
        if total_sales_amount <= Decimal('0.00'):
            raise ValidationError("لا يمكن إنشاء قيد لفاتورة مبيعات بإجمالي صفر.")

        total_cogs = Decimal('0.00')
        for item in invoice.items.select_related('product'):
            if item.product and item.product.product_type != 'service':
                unit_cost = Decimal(item.product.average_cost or Decimal('0.00'))
                quantity = Decimal(item.quantity or Decimal('0.00'))
                total_cogs += quantity * unit_cost
        total_cogs = total_cogs.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        entry = JournalEntry.objects.create(
            company=invoice.company,
            journal=journal,
            date=invoice.date,
            reference=invoice.invoice_number,
            notes=f"إثبات فاتورة مبيعات رقم {invoice.invoice_number} - العميل: {invoice.customer.name}",
            status='draft',
        )

        JournalItem.objects.create(
            entry=entry,
            account=receivable_acc,
            partner=invoice.customer,
            description=f"مستحقات عميل - فاتورة {invoice.invoice_number}",
            debit=total_sales_amount,
            credit=Decimal('0.00')
        )

        JournalItem.objects.create(
            entry=entry,
            account=revenue_acc,
            description=f"إيراد مبيعات - فاتورة {invoice.invoice_number}",
            debit=Decimal('0.00'),
            credit=total_sales_amount
        )

        if total_cogs > Decimal('0.00'):
            JournalItem.objects.create(
                entry=entry,
                account=cogs_acc,
                description=f"تكلفة بضاعة مباعة - فاتورة {invoice.invoice_number}",
                debit=total_cogs,
                credit=Decimal('0.00')
            )

            JournalItem.objects.create(
                entry=entry,
                account=inventory_acc,
                description=f"خفض المخزون - فاتورة {invoice.invoice_number}",
                debit=Decimal('0.00'),
                credit=total_cogs
            )

        entry.post()

        return entry

    @staticmethod
    @transaction.atomic
    def create_payment_journal_entry(
        payment,
        receivable_account_code='1003',
        payable_account_code='2001'
    ):
        """
        إنشاء القيد المحاسبي فقط للسند المالي:
        inbound  = قبض من عميل
        outbound = صرف لمورد
        """

        if payment.journal_entry_id:
            raise ValidationError("يوجد قيد يومية مرتبط بهذا السند بالفعل.")

        journal_type = 'cash' if payment.payment_method == 'cash' else 'bank'
        journal_code = 'CSH' if payment.payment_method == 'cash' else 'BNK'
        journal_name = 'دفتر الخزينة' if payment.payment_method == 'cash' else 'دفتر البنك'

        journal = AccountingService._get_or_create_journal(
            company=payment.company,
            code=journal_code,
            name=journal_name,
            journal_type=journal_type
        )

        cash_or_bank_acc = payment.account

        if cash_or_bank_acc.company_id != payment.company_id:
            raise ValidationError("حساب السند لا يتبع نفس الشركة.")

        if not cash_or_bank_acc.is_postable:
            raise ValidationError("يجب أن يكون حساب الخزينة/البنك قابلاً للترحيل.")

        if cash_or_bank_acc.account_type != 'asset':
            raise ValidationError("حساب السند يجب أن يكون من نوع أصل.")

        partner_acc_code = payable_account_code if payment.payment_type == 'outbound' else receivable_account_code
        partner_acc = AccountingService._get_account_by_code(payment.company, partner_acc_code)

        if payment.payment_type == 'outbound':
            current_cash_balance = cash_or_bank_acc.current_balance
            if Decimal(payment.amount) > current_cash_balance:
                raise ValidationError(
                    f"رصيد الحساب المالي ({current_cash_balance}) لا يكفي لصرف المبلغ المطلوب ({payment.amount})."
                )

        entry = JournalEntry.objects.create(
            company=payment.company,
            journal=journal,
            date=payment.date,
            reference=payment.voucher_number,
            notes=payment.notes or f"سند {payment.get_payment_type_display()} - {payment.partner.name}",
            status='draft',
        )

        if payment.payment_type == 'outbound':
            JournalItem.objects.create(
                entry=entry,
                account=partner_acc,
                partner=payment.partner,
                description="سداد للمورد",
                debit=Decimal(payment.amount),
                credit=Decimal('0.00')
            )
            JournalItem.objects.create(
                entry=entry,
                account=cash_or_bank_acc,
                description="صرف من الخزينة / البنك",
                debit=Decimal('0.00'),
                credit=Decimal(payment.amount)
            )
        else:
            JournalItem.objects.create(
                entry=entry,
                account=cash_or_bank_acc,
                description="تحصيل إلى الخزينة / البنك",
                debit=Decimal(payment.amount),
                credit=Decimal('0.00')
            )
            JournalItem.objects.create(
                entry=entry,
                account=partner_acc,
                partner=payment.partner,
                description="تحصيل من العميل",
                debit=Decimal('0.00'),
                credit=Decimal(payment.amount)
            )

        entry.post()
        return entry
