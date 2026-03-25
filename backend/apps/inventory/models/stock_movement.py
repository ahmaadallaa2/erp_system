# apps/inventory/models/stock_movement.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .product import Product
from .stock_document import StockDocument # استدعاء الأب

class StockMovement(BaseModel):
    """حركة الصنف (سطور المستند) - Stock Move Line"""
    
    # الربط بالإذن المخزني (لو الإذن اتمسح، السطور تتمسح معاه CASCADE)
    document = models.ForeignKey(
        StockDocument, 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name=_("الإذن المخزني")
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='movements', 
        verbose_name=_("المنتج")
    )
    
    quantity = models.DecimalField(_("الكمية"), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _("حركة صنف")
        verbose_name_plural = _("حركات الأصناف (كارت الصنف)")
        ordering = ['document__created_at']

    def __str__(self):
        # بنقرا نوع الحركة (IN/OUT) من الأب مباشرة
        move_type = self.document.get_document_type_display()
        return f"{move_type} - {self.product.name} ({self.quantity})"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(_("يجب أن تكون الكمية رقماً موجباً أكبر من الصفر."))

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(_("لا يمكن تعديل الحركات المخزنية بعد تسجيلها."))
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("ممنوع حذف الحركات المخزنية للحفاظ على نزاهة النظام."))