from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from .product import Product
from .stock_transaction import StockTransaction


class StockMovement(BaseModel):
    """
    سطر حركة مخزنية تابع لمستند مخزني.
    يمثل المنتج والكمية والتكلفة داخل StockTransaction.
    """

    transaction = models.ForeignKey(
        StockTransaction,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("الحركة المخزنية")
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='movements',
        verbose_name=_("المنتج")
    )

    quantity = models.DecimalField(
        _("الكمية"),
        max_digits=12,
        decimal_places=2
    )

    unit_cost = models.DecimalField(
        _("تكلفة الوحدة"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    note = models.CharField(
        _("ملاحظة"),
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("سطر حركة مخزنية")
        verbose_name_plural = _("سطور الحركات المخزنية")
        ordering = ['id']

    def __str__(self):
        tx_type = self.transaction.get_transaction_type_display()
        return f"{tx_type} - {self.product.name} ({self.quantity})"

    def clean(self):
        super().clean()

        if self.quantity is None or self.quantity <= 0:
            raise ValidationError(_("يجب أن تكون الكمية أكبر من الصفر."))

        if self.unit_cost is not None and self.unit_cost < 0:
            raise ValidationError(_("لا يمكن أن تكون تكلفة الوحدة سالبة."))

        if self.product_id and self.transaction_id:
            if self.product.company_id != self.transaction.company_id:
                raise ValidationError(_("المنتج لا يتبع نفس شركة الحركة المخزنية."))

            if self.product.product_type == 'service':
                raise ValidationError(_("الخدمات لا تنشئ حركة مخزنية."))

    def save(self, *args, **kwargs):
        if not self._state.adding and self.transaction.status == 'posted':
            raise ValidationError(_("لا يمكن تعديل سطور الحركة المخزنية بعد ترحيل المستند."))

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.transaction.status == 'posted':
            raise ValidationError(_("لا يمكن حذف سطور الحركة المخزنية بعد ترحيل المستند."))
        super().delete(*args, **kwargs)