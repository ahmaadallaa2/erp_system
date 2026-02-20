from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import StockMovement, Stock # لاحظ الـ (..) عشان إحنا جوه فولدر فرعي

@receiver(post_save, sender=StockMovement)
def update_stock_on_movement(sender, instance, created, **kwargs):
    if created:
        stock, _ = Stock.objects.get_or_create(
            product=instance.product,
            warehouse=instance.warehouse,
            defaults={'quantity': 0}
        )

        if instance.movement_type == 'IN':
            stock.quantity += instance.quantity
        elif instance.movement_type == 'OUT':
            stock.quantity -= instance.quantity
        
        stock.save()