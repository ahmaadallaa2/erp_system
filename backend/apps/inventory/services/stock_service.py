from django.db import transaction
from django.db.models import Sum
from apps.inventory.models import Stock, StockMovement

class StockService:
    
    @staticmethod
    def register_movement(product, warehouse, movement_type, quantity, reference, notes, unit_price=None):
        """
        خدمة مركزية لتسجيل حركات المخزون، تحديث الرصيد، وحساب متوسط التكلفة.
        """
        with transaction.atomic():
            # 1. إنشاء حركة المخزون (تسجيل في دفتر الصنف)
            movement = StockMovement.objects.create(
                product=product,
                warehouse=warehouse,
                movement_type=movement_type,
                quantity=quantity,
                reference=reference,
                notes=notes
            )

            # 2. تحديث الرصيد في المخزن المحدد
            stock_record, _ = Stock.objects.get_or_create(
                product=product, 
                warehouse=warehouse,
                defaults={'quantity': 0}
            )
            
            if movement_type == 'IN':
                stock_record.quantity += quantity
            elif movement_type == 'OUT':
                stock_record.quantity -= quantity
            
            stock_record.save(update_fields=['quantity'])

            # 3. تحديث متوسط التكلفة (WAC) فقط في حالة الوارد ووجود سعر
            if movement_type == 'IN' and unit_price is not None:
                # نحسب إجمالي الكمية في كل المخازن للصنف ده
                total_current_qty = Stock.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
                
                # الكمية قبل هذه الحركة
                old_qty = total_current_qty - quantity
                
                if total_current_qty > 0:
                    old_value = old_qty * product.average_cost
                    new_value = quantity * unit_price
                    new_avg_cost = (old_value + new_value) / total_current_qty
                    
                    product.average_cost = round(new_avg_cost, 2)
                    product.save(update_fields=['average_cost'])

            return movement