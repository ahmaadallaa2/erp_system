# apps/purchases/services/inventory_service.py

from django.db import transaction
from django.db.models import Sum
from apps.inventory.models import Stock, StockMovement

class InventorySyncService:
    
    @staticmethod
    def process_purchase_receipt(purchase_order):
        """
        Service to handle inventory updates and WAC calculations 
        when a Purchase Order is approved/received.
        """
        with transaction.atomic():
            # 1. Idempotency Check: Prevent duplicate processing
            movement_exists = StockMovement.objects.filter(reference=purchase_order.po_number).exists()
            if movement_exists:
                return False, "تم إدخال هذه الفاتورة للمخزن مسبقاً."
            
            # 2. Process each item in the purchase order
            for item in purchase_order.items.all():
                product = item.product
                warehouse = purchase_order.warehouse
                quantity = item.quantity
                unit_price = item.unit_price

                # A. Create a Stock Movement (Inbound)
                # A. Create a Stock Movement (Inbound)
                StockMovement.objects.create(
                    product=product,
                    warehouse=warehouse,
                    # هنا التعديل: اكتب القيمة اللي متسجلة عندك في الموديل بتاع المخازن كـ "وارد"
                    # لو الموديل بيقبل كلمة 'وارد' مباشرة حطها، ولو عاملها كـ Choices زي 'IN' حطها 'IN'
                    movement_type='IN',  # أو 'in' سمول لو أنت كاتبها سمول في الموديل  # أو 'IN' حسب تعريفك في الموديل
                    quantity=quantity,
                    reference=purchase_order.po_number,
                    # بالمرة نخلي الملاحظة التلقائية تظهر بالعربي بشياكة
                    notes=f"وارد مشتريات تلقائي من أمر الشراء رقم: {purchase_order.po_number}" 
                )

                # B. Update or Create Stock Record
                stock_record, _ = Stock.objects.get_or_create(
                    product=product, 
                    warehouse=warehouse,
                    defaults={'quantity': 0}
                )
                stock_record.quantity += quantity
                stock_record.save(update_fields=['quantity'])

                # C. Calculate and Update Weighted Average Cost (WAC)
                total_current_qty = Stock.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
                old_qty = total_current_qty - quantity
                
                if total_current_qty > 0:
                    old_value = old_qty * product.average_cost
                    new_value = quantity * unit_price
                    new_avg_cost = (old_value + new_value) / total_current_qty
                    
                    product.average_cost = round(new_avg_cost, 2)
                    product.save(update_fields=['average_cost'])
                    
            return True, "تم تحديث المخزون بنجاح."