from django.db import transaction
from apps.inventory.models import StockMovement
from apps.inventory.services.stock_service import StockService

class InventorySyncService:
    
    @staticmethod
    def process_purchase_receipt(invoice):
        with transaction.atomic():
            # 1. Idempotency Check: التأكد من عدم تكرار الفاتورة
            movement_exists = StockMovement.objects.filter(reference=invoice.invoice_number).exists()
            if movement_exists:
                return False, "تم إدخال هذه الفاتورة للمخزن مسبقاً."
            
            # 2. المرور على عناصر الفاتورة وإرسالها لخدمة المخازن
            for item in invoice.items.all():
                # السحر الحلال هنا: استدعاء خدمة المخازن المركزية
                StockService.register_movement(
                    product=item.product,
                    warehouse=invoice.warehouse,
                    movement_type='IN', # وارد
                    quantity=item.quantity,
                    reference=invoice.invoice_number,
                    notes=f"وارد مشتريات تلقائي من فاتورة رقم: {invoice.invoice_number}",
                    unit_price=item.unit_price # بنبعت السعر عشان يحسب متوسط التكلفة
                )
                    
            return True, "تم تحديث المخزون بنجاح."