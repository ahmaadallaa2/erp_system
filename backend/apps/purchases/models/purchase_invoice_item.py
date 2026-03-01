from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

# ==========================================
# Purchase Invoice Item Model (Lines)
# ==========================================
class PurchaseInvoiceItem(SoftDeleteModel):
    # links the item to the parent invoice using string reference 'purchases.PurchaseInvoice'
    invoice = models.ForeignKey(
        'purchases.PurchaseInvoice', 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name=_("الفاتورة")
    )

    # string reference to the product model to prevent circular imports
    product = models.ForeignKey(
        'inventory.Product', 
        on_delete=models.RESTRICT, 
        related_name='purchase_invoice_items', 
        verbose_name=_("المنتج")
    )

    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_("الكمية")
    )

    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_("سعر الوحدة")
    )

    total_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False, 
        verbose_name=_("التكلفة الإجمالية")
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("ملاحظات")
    )

    class Meta:
        verbose_name = _("عنصر فاتورة المشتريات")
        verbose_name_plural = _("عناصر فاتورة المشتريات")
        unique_together = ('invoice', 'product') 

    def __str__(self):
        return f"{self.product.name if self.product else 'بدون منتج'} - {self.quantity} Units"
    
    def save(self, *args, **kwargs):
        # 1. Calculate the line total
        self.total_cost = self.quantity * self.unit_price
        
        # 2. Save the item
        super().save(*args, **kwargs)
        
        # 3. Update parent invoice total
        self.update_invoice_total()

    def delete(self, *args, **kwargs):
        # Keep a reference before deleting to update the parent total
        invoice_reference = self.invoice
        super().delete(*args, **kwargs)
        
        # Recalculate total after deletion
        total = invoice_reference.items.aggregate(total=models.Sum('total_cost'))['total'] or 0
        invoice_reference.total_amount = total
        invoice_reference.save(update_fields=['total_amount'])

    def update_invoice_total(self):
        # Helper function to recalculate the parent invoice total amount
        total = self.invoice.items.aggregate(total=models.Sum('total_cost'))['total'] or 0
        self.invoice.total_amount = total
        self.invoice.save(update_fields=['total_amount'])