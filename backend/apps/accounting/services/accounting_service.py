from django.db import transaction
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

from django.db import transaction
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

class AccountingService:

    @staticmethod
    def create_purchase_invoice_entry(invoice, inventory_account_code='1004', payable_account_code='2001', bank_account_code='1002'):
        """
        خدمة لإنشاء قيد يومية أوتوماتيكي مركب عند استلام فاتورة مشتريات.
        يتم إثبات قيمة البضاعة للمورد، وخصم مصاريف الشحن والجمارك من البنك، وتحميل الإجمالي على المخزون.
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

            # ==========================================
            # 3. حساب القيم (البضاعة الأساسية vs المصاريف)
            # ==========================================
            total_goods_value = invoice.total_amount # قيمة البضاعة الأساسية للمورد
            
            # جلب المصاريف الإضافية (بنتأكد إنها موجودة بـ getattr عشان ميتعملش إيرور)
            shipping = getattr(invoice, 'shipping_cost', 0)
            clearance = getattr(invoice, 'clearance_cost', 0)
            commission_pct = getattr(invoice, 'commission_percentage', 0)
            
            # حساب التكلفة الكلية للمصاريف
            commission_value = float(total_goods_value) * (float(commission_pct) / 100)
            total_expenses = float(shipping) + float(clearance) + commission_value
            
            # المخزون هيشيل الليلة كلها (البضاعة + المصاريف)
            total_inventory_value = float(total_goods_value) + total_expenses

            # 4. جلب الحسابات المحاسبية
            try:
                inventory_acc = Account.objects.get(code=inventory_account_code)
                payable_acc = Account.objects.get(code=payable_account_code)
                bank_acc = Account.objects.get(code=bank_account_code) # حساب البنك للمصاريف
            except Account.DoesNotExist:
                return False, f"فشل: تأكد من وجود حساب المخزون ({inventory_account_code}) والموردين ({payable_account_code}) والبنك ({bank_account_code}) في شجرة الحسابات."

            # 5. إنشاء رأس القيد (مُرحل مباشرة لتسميع الرصيد)
            entry = JournalEntry.objects.create(
                journal=journal,
                date=invoice.invoice_date,
                reference=invoice.invoice_number,
                status='posted',
                notes=f"إثبات مديونية وتكلفة لفاتورة المشتريات رقم {invoice.invoice_number} - المورد: {invoice.supplier.name}"
            )

            # ==========================================
            # 6. إنشاء سطور القيد (القيد المركب)
            # ==========================================
            
            # الطرف المدين (Debit): المخزون زاد (بإجمالي القيمة شاملة المصاريف)
            JournalItem.objects.create(
                entry=entry,
                account=inventory_acc,
                description=f"استلام بضاعة (شاملة التكلفة الإضافية) - فاتورة {invoice.invoice_number}",
                debit=total_inventory_value,
                credit=0.00
            )

            # الطرف الدائن 1 (Credit): المديونية للمورد زادت (بقيمة البضاعة فقط)
            JournalItem.objects.create(
                entry=entry,
                account=payable_acc,
                partner=invoice.supplier,  # ربطنا المورد هنا عشان كشف حسابه!
                description=f"استحقاق بضاعة فاتورة {invoice.invoice_number}",
                debit=0.00,
                credit=total_goods_value
            )

            # الطرف الدائن 2 (Credit): خروج فلوس من البنك (بقيمة المصاريف الإضافية)
            if total_expenses > 0:
                JournalItem.objects.create(
                    entry=entry,
                    account=bank_acc,
                    description=f"تحويل بنكي: مصاريف شحن وتخليص وعمولة - فاتورة {invoice.invoice_number}",
                    debit=0.00,
                    credit=total_expenses
                )

            return True, "تم إنشاء القيد المحاسبي المركب بنجاح."
        
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