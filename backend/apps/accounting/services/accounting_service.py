from django.db import transaction
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

class AccountingService:

    @staticmethod
    def create_purchase_invoice_entry(invoice, inventory_account_code='1001', payable_account_code='2001'):
        """
        خدمة لإنشاء قيد يومية أوتوماتيكي عند استلام فاتورة مشتريات.
        """
        with transaction.atomic():
            # 1. التأكد من وجود دفتر المشتريات (أو إنشاؤه تلقائياً)
            journal, _ = Journal.objects.get_or_create(
                code='PUR',
                defaults={'name': 'دفتر المشتريات', 'type': 'purchase'}
            )

            # 2. فحص التكرار (Idempotency): منع إنشاء قيدين لنفس الفاتورة
            if JournalEntry.objects.filter(reference=invoice.invoice_number, journal=journal).exists():
                return False, "تم إنشاء قيد لهذه الفاتورة مسبقاً."

            # 3. جلب الحسابات المحاسبية
            try:
                inventory_acc = Account.objects.get(code=inventory_account_code)
                payable_acc = Account.objects.get(code=payable_account_code)
            except Account.DoesNotExist:
                return False, f"فشل: يجب إنشاء حساب المخزون (كود {inventory_account_code}) وحساب الموردين (كود {payable_account_code}) في شجرة الحسابات أولاً."

            # 4. إنشاء رأس القيد (مُرحل مباشرة لتسميع الرصيد)
            entry = JournalEntry.objects.create(
                journal=journal,
                date=invoice.invoice_date,
                reference=invoice.invoice_number,
                status='posted',
                notes=f"إثبات مديونية لفاتورة المشتريات رقم {invoice.invoice_number} - المورد: {invoice.supplier.name}"
            )

            # 5. إنشاء سطور القيد (المدين والدائن)
            
            # الطرف المدين (Debit): المخزون زاد
            JournalItem.objects.create(
                entry=entry,
                account=inventory_acc,
                description=f"استلام بضاعة - فاتورة {invoice.invoice_number}",
                debit=invoice.total_amount,
                credit=0.00
            )

            # الطرف الدائن (Credit): المديونية للمورد زادت
            JournalItem.objects.create(
                entry=entry,
                account=payable_acc,
                partner=invoice.supplier,  # ربطنا المورد هنا عشان كشف حسابه!
                description=f"استحقاق فاتورة {invoice.invoice_number}",
                debit=0.00,
                credit=invoice.total_amount
            )

            return True, "تم إنشاء القيد المحاسبي بنجاح."
        
    @staticmethod
    def create_payment_entry(payment, cash_account_code='1002', payable_account_code='2001', receivable_account_code='1003'):
        """
        خدمة لإنشاء قيد يومية أوتوماتيكي عند عمل سند صرف أو قبض.
        """
        with transaction.atomic():
            # 1. تحديد دفتر النقدية
            journal, _ = Journal.objects.get_or_create(
                code='CSH',
                defaults={'name': 'دفتر الخزينة / النقدية', 'type': 'cash'}
            )

            # 2. جلب الحسابات
            try:
                cash_acc = Account.objects.get(code=cash_account_code)
                partner_acc = Account.objects.get(code=payable_account_code if payment.payment_type == 'outbound' else receivable_account_code)
            except Account.DoesNotExist:
                return False, f"فشل: تأكد من وجود حساب الخزينة ({cash_account_code}) وحساب الشريك في شجرة الحسابات."

            # -----------------------------------------------------
            # 🔒 قفل الأمان الصارم: منع السحب على المكشوف من الخزينة
            # -----------------------------------------------------
            if payment.payment_type == 'outbound':
                current_cash = cash_acc.current_balance
                if payment.amount > current_cash:
                    return False, f"مرفوض أمنياً! رصيد الخزينة الفعلي ({current_cash}) لا يكفي لصرف المبلغ المطلوب ({payment.amount}). يجب إثبات توريد نقدية للخزنة أولاً."
            # -----------------------------------------------------

            # 3. إنشاء رأس القيد
            entry = JournalEntry.objects.create(
                journal=journal,
                date=payment.date,
                reference=payment.name,
                status='posted',
                notes=payment.notes or f"سداد من/إلى {payment.partner.name}"
            )

            # 4. توجيه السطور
            if payment.payment_type == 'outbound':
                JournalItem.objects.create(entry=entry, account=partner_acc, partner=payment.partner, description=f"سداد دفعة للمورد", debit=payment.amount, credit=0.00)
                JournalItem.objects.create(entry=entry, account=cash_acc, description=f"صرف نقدية", debit=0.00, credit=payment.amount)
            else:
                JournalItem.objects.create(entry=entry, account=cash_acc, description=f"استلام نقدية", debit=payment.amount, credit=0.00)
                JournalItem.objects.create(entry=entry, account=partner_acc, partner=payment.partner, description=f"تحصيل دفعة من العميل", debit=0.00, credit=payment.amount)

            # 5. ربط القيد بالسند
            payment.journal_entry = entry
            payment.save(update_fields=['journal_entry'])

            return True, "تم السداد وإنشاء القيد بنجاح."