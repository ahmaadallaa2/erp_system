from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .product import Product
from .warehouse import Warehouse

class StockMovement(BaseModel):
    MOVEMENT_TYPES = (
        ('IN', _('وارد (إضافة)')),
        ('OUT', _('صادر (صرف)')),
    )

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements', verbose_name=_("المنتج"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='movements', verbose_name=_("المخزن"))
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES, verbose_name=_("نوع الحركة"))
    quantity = models.DecimalField(_("الكمية"), max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم الفاتورة/المرجع"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات"))

    class Meta:
        verbose_name = _("حركة مخزنية")
        verbose_name_plural = _("حركات المخازن")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(_("يجب أن تكون الكمية رقماً موجباً أكبر من الصفر."))

    def save(self, *args, **kwargs):
        # منع التعديل على الحركات المحفوظة سابقاً
        if not self._state.adding:
            raise ValidationError(_("لا يمكن تعديل الحركات المخزنية بعد تسجيلها."))
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("ممنوع حذف الحركات المخزنية للحفاظ على نزاهة النظام."))