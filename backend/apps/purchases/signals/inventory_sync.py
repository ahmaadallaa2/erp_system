# apps/purchases/signals/inventory_sync.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.purchases.models.order import PurchaseOrder
# نستدعي الـ Service اللي لسه عاملينها
from apps.purchases.services.inventory_services import InventorySyncService

@receiver(post_save, sender=PurchaseOrder)
def trigger_inventory_sync_on_approval(sender, instance, created, **kwargs):

    if instance.status == 'approved':
        InventorySyncService.process_purchase_receipt(instance)