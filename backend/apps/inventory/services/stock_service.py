from django.db import transaction
from django.db.models import Sum, F
from apps.inventory.models import Stock, StockMovement, Product

class StockService:
    
    @staticmethod
    def register_movement(document, product, quantity, unit_price=None, notes=None):
        """
        خدمة مطورة لربط حركات المخزون بالإذن الرئيسي وتحديث الأرصدة والتكلفة.
        """
        warehouse = document.warehouse
        # تحويل نوع الإذن (IN/OUT) من الـ Document
        movement_type = document.document_type 

        with transaction.atomic():
            # 1. إنشاء سطر الحركة وربطه بالإذن (Document)
            movement = StockMovement.objects.create(
                document=document, # الربط بالأب
                product=product,
                quantity=quantity,
                unit_price=unit_price or 0, # تخزين السعر في الحركة للتوثيق
                notes=notes
            )

            # 2. تحديث الرصيد (استخدام F() لتجنب الـ Race Conditions)
            stock_record, _ = Stock.objects.get_or_create(
                product=product, 
                warehouse=warehouse,
                defaults={'quantity': 0}
            )
            
            if movement_type == 'IN':
                stock_record.quantity = F('quantity') + quantity
            elif movement_type == 'OUT':
                stock_record.quantity = F('quantity') - quantity
            
            stock_record.save()
            # ملحوظة: نحتاج عمل refresh_from_db لو هنستخدم الـ quantity في نفس الفانكشن بعد الـ F()

            # 3. تحديث متوسط التكلفة (WAC) - فقط في حالة الوارد
            if movement_type == 'IN' and unit_price is not None:
                stock_record.refresh_from_db()
                
                # إجمالي الكمية الحالية في كل المخازن
                total_qty_data = Stock.objects.filter(product=product).aggregate(total=Sum('quantity'))
                total_current_qty = total_qty_data['total'] or 0
                
                # الكمية قبل هذه الحركة
                old_qty = total_current_qty - quantity
                
                if total_current_qty > 0:
                    # معادلة المتوسط المرجح: (الكمية القديمة * تكلفتها + الكمية الجديدة * تكلفتها) / إجمالي الكمية
                    old_total_value = old_qty * (product.average_cost or 0)
                    new_total_value = quantity * unit_price
                    new_avg_cost = (old_total_value + new_total_value) / total_current_qty
                    
                    product.average_cost = round(new_avg_cost, 4) # 4 أرقام عشرية لدقة الحسابات المالية
                    product.save(update_fields=['average_cost'])

            return movement