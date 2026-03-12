# apps/sales/services/sales_service.py

from decimal import Decimal
from django.db import transaction
from apps.inventory.models import StockMovement, Stock
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

class SalesService:
    @staticmethod
    def process_sales_invoice(invoice):
        """
        خدمة ترحيل فاتورة المبيعات:
        1. خصم البضاعة من المخزن (موديل Stock وتحديث حركات المخازن).
        2. إنشاء قيد يومية مزدوج: 
           - (إيرادات المبيعات) بناءً على طريقة الدفع كاش/آجل.
           - (تكلفة البضاعة المباعة) لضبط جرد المخزن وحساب الأرباح.
        """
        # حائط الصد: التأكد من عدم تكرار القيد لنفس الفاتورة
        if JournalEntry.objects.filter(reference=invoice.invoice_number).exists():
            return False, "الفاتورة تم ترحيلها مسبقاً ولا يمكن تكرار القيد."

        # التأكد من وجود منتجات في الفاتورة
        if not invoice.items.exists():
            return False, "لا يمكن تأكيد فاتورة فارغة بدون منتجات."

        with transaction.atomic():
            # الاعتماد على المخزن المحدد في الفاتورة نفسها
            if not invoice.warehouse:
                return False, "فشل: يرجى تحديد المخزن الذي سيتم صرف البضاعة منه في الفاتورة."

            # ==========================================
            # 1. حركة المخازن (صرف البضاعة وتحديث الأرصدة)
            # ==========================================
            for item in invoice.items.all():
                # أ. تسجيل حركة الصرف في الدفاتر
                StockMovement.objects.create(
                    warehouse=invoice.warehouse,
                    product=item.product,
                    movement_type='OUT', 
                    quantity=item.quantity,
                    reference=invoice.invoice_number,
                    notes=f"صرف مبيعات للعميل: {invoice.customer.name}"
                )
                
                # ب. تحديث رصيد المخزن الفعلي في موديل الأرصدة (Stock)
                stock_record, created = Stock.objects.get_or_create(
                    product=item.product,
                    warehouse=invoice.warehouse,
                    defaults={'quantity': 0}
                )
                
                # قفل الأمان الصارم: منع البيع لو الرصيد لا يكفي
                if stock_record.quantity < item.quantity:
                    return False, f"مرفوض أمنياً! رصيد المنتج '{item.product.name}' في المخزن لا يكفي. المتاح: {stock_record.quantity}"
                
                # خصم الكمية وحفظها
                stock_record.quantity -= item.quantity
                stock_record.save(update_fields=['quantity'])

            # ==========================================
            # 2. الترحيل المحاسبي المزدوج (بيع وتكلفة)
            # ==========================================
            journal, _ = Journal.objects.get_or_create(
                code='SAL', 
                defaults={'name': 'دفتر المبيعات', 'type': 'sale'}
            )
            
            try:
                # حسابات قيد الإيرادات
                sales_revenue_acc = Account.objects.get(code='4001') 
                # حسابات قيد التكلفة (الجديد)
                cogs_acc = Account.objects.get(code='5001')          # تكلفة البضاعة المباعة
                inventory_acc = Account.objects.get(code='1004')     # حساب المخزون كأصل
                
                # تحديد الطرف المدين بناءً على طريقة الدفع
                if getattr(invoice, 'payment_type', 'credit') == 'cash':
                    if not invoice.treasury_account:
                        return False, "فشل: يرجى تحديد حساب الخزينة لفاتورة الكاش."
                    debit_account = invoice.treasury_account
                    partner_link = None # الفلوس في الخزنة، مفيش مديونية على العميل
                    desc = "مبيعات نقدية (كاش)"
                else:
                    debit_account = Account.objects.get(code='1003') # حساب العملاء
                    partner_link = invoice.customer
                    desc = "مبيعات آجلة (على الحساب)"
                    
            except Account.DoesNotExist:
                return False, "فشل: يرجى التأكد من إعدادات شجرة الحسابات (العملاء 1003، الإيرادات 4001، التكلفة 5001، المخزون 1004، والخزينة)."

            # إنشاء رأس القيد
            entry = JournalEntry.objects.create(
                journal=journal,
                date=invoice.date,
                reference=invoice.invoice_number,
                status='posted',
                notes=f"إثبات فاتورة مبيعات {invoice.get_payment_type_display() if hasattr(invoice, 'get_payment_type_display') else ''} رقم {invoice.invoice_number}"
            )

            # -----------------------------------------------------------------
            # أ. قيد الإيرادات (بسعر البيع)
            # -----------------------------------------------------------------
            total_sales = Decimal(str(invoice.total_amount))
            zero_decimal = Decimal('0.00')
            
            # الطرف المدين (إما الخزينة أو العميل)
            JournalItem.objects.create(entry=entry, account=debit_account, partner=partner_link, debit=total_sales, credit=zero_decimal, description=desc)
            
            # الطرف الدائن (إيرادات المبيعات)
            JournalItem.objects.create(entry=entry, account=sales_revenue_acc, debit=zero_decimal, credit=total_sales, description="إيرادات مبيعات")

            # -----------------------------------------------------------------
            # ب. قيد التكلفة (بسعر الشراء/المتوسط المرجح من كارت الصنف)
            # -----------------------------------------------------------------
            total_cogs = Decimal('0.00')
            for item in invoice.items.all():
                quantity = Decimal(str(item.quantity))
                # نفترض أن حقل التكلفة في موديل المنتج اسمه cost_price
                cost_price = Decimal(str(item.product.cost_price)) 
                total_cogs += (quantity * cost_price)
            
            if total_cogs > zero_decimal:
                # الطرف المدين: المصروفات (تكلفة البضاعة) زادت
                JournalItem.objects.create(entry=entry, account=cogs_acc, debit=total_cogs, credit=zero_decimal, description="تكلفة البضاعة المباعة")
                # الطرف الدائن: الأصول (المخزون) قل
                JournalItem.objects.create(entry=entry, account=inventory_acc, debit=zero_decimal, credit=total_cogs, description="خفض قيمة المخزون المباع")

            return True, f"تم سحب البضاعة وإنشاء القيد المحاسبي المزدوج (بيع وتكلفة) بنجاح."