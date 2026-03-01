from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.purchases.models import PurchaseOrder
# نستدعي الـ Service اللي لسه عاملينها
from apps.purchases.services.inventory_services import InventorySyncService
from apps.purchases.models import PurchaseInvoice

@receiver(post_save, sender=PurchaseInvoice)
def trigger_inventory_sync_on_approval(sender, instance, created, **kwargs):

    if instance.status == 'received':  # أو 'approved' حسب ما أنت مسمي الحالة اللي بتعبر عن استلام الفاتورة
        InventorySyncService.process_purchase_receipt(instance)