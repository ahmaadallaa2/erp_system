from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class PurchaseOrderItem(SoftDeleteModel):
    # this is the purchase order that the item belongs to, it uses a string reference 'purchases.PurchaseOrder' to avoid circular imports in Django.
    # CASCADE means if the purchase order is deleted, all its items will be deleted automatically to maintain data integrity.
    purchase_order = models.ForeignKey(
        'purchases.PurchaseOrder', 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name=_("أمر الشراء")
    )

    # this is the product that is being purchased, it uses RESTRICT to prevent deleting a product that has been used in purchase orders to keep financial records intact.
    product = models.ForeignKey(
        'inventory.Product', 
        on_delete=models.RESTRICT, 
        related_name='purchase_order_items', 
        verbose_name=_("المنتج")
    )

    # this is the quantity of the item ordered, it uses DecimalField to support fractional units if needed.
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_("الكمية")
    )

    # this is the purchasing price per unit at the time of the order.
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_("سعر الوحدة")
    )

    # this is the total cost of the line item (quantity * unit_price), it is calculated automatically.
    # we set editable=False to prevent manual tampering and ensure strict financial calculations.
    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False, 
        verbose_name=_("التكلفة الإجمالية")
    )

    # optional notes for this specific line item (e.g., "requires special packaging" or "urgent delivery").
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("ملاحظات")
    )

    # this is the class meta of the item model, it is used to define the verbose names and to prevent adding the exact same product twice to the same purchase order.
    class Meta:
        verbose_name = _("منتج أمر الشراء")
        verbose_name_plural = _("منتجات أمر الشراء")
        unique_together = ('purchase_order', 'product') 

    # This method is used to return the string representation of the item, it is used in the admin panel and in the views to display the item in a readable format.
    def __str__(self):
        return f"{self.product.name if self.product else 'بدون منتج'} - {self.quantity} Units"
    
    # this is the save method of the item model, it calculates the total cost of the item before saving, and then triggers the update for the parent order's total amount.
    def save(self, *args, **kwargs):
        # 1. Calculate the line total
        self.total_cost = self.quantity * self.unit_price
        
        # 2. Save the item to the database
        super().save(*args, **kwargs)
        
        # 3. Trigger the update for the parent order
        self.update_order_total()

    # this delete method ensures that if an item is removed from the order, the parent order's total amount is recalculated correctly.
    def delete(self, *args, **kwargs):
        # We need to keep a reference to the order before deleting the item
        order_reference = self.purchase_order
        
        # Delete the item
        super().delete(*args, **kwargs)
        
        # Recalculate the order total using the reference
        total = order_reference.items.aggregate(total=models.Sum('total_cost'))['total'] or 0
        order_reference.total_amount = total
        order_reference.save(update_fields=['total_amount'])

    # a helper method to recalculate the parent order's total amount by summing up the total_cost of all its items.
    def update_order_total(self):
        total = self.purchase_order.items.aggregate(total=models.Sum('total_cost'))['total'] or 0
        self.purchase_order.total_amount = total
        self.purchase_order.save(update_fields=['total_amount'])