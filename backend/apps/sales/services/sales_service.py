# apps/sales/services/sales_service.py

from django.db import transaction
from apps.inventory.models import StockMovement, Stock
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

class SalesService:
    @staticmethod
    def process_sales_invoice(invoice):
        """
        خدمة ترحيل فاتورة المبيعات:
        1. خصم البضاعة من المخزن (موديل Stock).
        2. إنشاء قيد يومية (من ح/ العملاء إلى ح/ المبيعات).
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

            # 1. حركة المخازن (صرف البضاعة وتحديث الأرصدة)
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

            # 2. الترحيل المحاسبي
            journal, _ = Journal.objects.get_or_create(
                code='SAL', 
                defaults={'name': 'دفتر المبيعات', 'type': 'sale'}
            )
            
            try:
                customer_acc = Account.objects.get(code='1003') 
                sales_revenue_acc = Account.objects.get(code='4001') 
            except Account.DoesNotExist:
                return False, "فشل: يرجى التأكد من وجود حساب العملاء (1003) وحساب الإيرادات (4001)."

            entry = JournalEntry.objects.create(
                journal=journal,
                date=invoice.date,
                reference=invoice.invoice_number,
                status='posted',
                notes=f"إثبات مبيعات فاتورة {invoice.invoice_number}"
            )

            total = invoice.total_amount
            JournalItem.objects.create(entry=entry, account=customer_acc, partner=invoice.customer, debit=total, credit=0.00, description="قيمة فاتورة مبيعات")
            JournalItem.objects.create(entry=entry, account=sales_revenue_acc, debit=0.00, credit=total, description="إيرادات مبيعات")

            return True, "تم سحب البضاعة من المخزن وإنشاء القيد المحاسبي بنجاح."