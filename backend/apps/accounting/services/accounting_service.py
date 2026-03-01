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