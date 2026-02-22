from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F

from apps.inventory.models import StockMovement
from apps.inventory.models import Stock

@receiver(post_save, sender=StockMovement)
def update_stock_on_movement(sender, instance, created, **kwargs):
    """
    مستمع (Signal) يعمل تلقائياً فور حفظ أي حركة مخزنية جديدة.
    وظيفته تحديث رصيد المخزون (Stock) بناءً على نوع الحركة.
    """
    # created = True تعني أن هذه حركة جديدة وليست تعديلاً
    if created:
        with transaction.atomic():
            # 1. جلب الرصيد الحالي أو إنشاؤه، وقفله مؤقتاً (select_for_update) لمنع التداخل
            stock_record, _ = Stock.objects.select_for_update().get_or_create(
                product=instance.product,
                warehouse=instance.warehouse,
                defaults={
                    'quantity': 0, 
                    # جلب الـ company_id من الفرع التابع له المخزن
                    'company_id': instance.warehouse.branch.company_id 
                }
            )

            # 2. تطبيق المعادلة المخزنية
            if instance.movement_type == 'IN':
                stock_record.quantity = F('quantity') + instance.quantity
            elif instance.movement_type == 'OUT':
                stock_record.quantity = F('quantity') - instance.quantity
            
            # 3. حفظ التحديث
            stock_record.save(update_fields=['quantity'])