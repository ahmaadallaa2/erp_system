from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import BaseModel
from apps.core.models.company import Company
from .product import Product
from .warehouse import Warehouse


class StockBalance(BaseModel):
    """
    رصيد المخزون الحالي.
    يتم تحديثه برمجياً فقط عبر حركات المخزون.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='stock_balances',
        verbose_name=_("الشركة")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_balances',
        verbose_name=_("المنتج")
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='stock_balances',
        verbose_name=_("المخزن")
    )

    quantity = models.DecimalField(
        _("الكمية الفعلية"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    reserved_quantity = models.DecimalField(
        _("الكمية المحجوزة"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    location = models.CharField(
        _("موقع التخزين (رف/ممر)"),
        max_length=50,
        null=True,
        blank=True
    )

    reorder_point = models.DecimalField(
        _("حد الطلب"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    class Meta:
        verbose_name = _("رصيد مخزون")
        verbose_name_plural = _("أرصدة المخزون")
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'product', 'warehouse'],
                name='unique_product_per_warehouse_per_company'
            )
        ]

    def __str__(self):
        return f"{self.product.name} | {self.warehouse.name}: {self.quantity}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def clean(self):
        super().clean()

        if self.product and self.company and self.product.company_id != self.company_id:
            raise ValidationError(_("المنتج لا يتبع نفس الشركة."))

        if self.warehouse and self.company and self.warehouse.company_id != self.company_id:
            raise ValidationError(_("المخزن لا يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        if not self.company_id and self.warehouse_id:
            self.company_id = self.warehouse.company_id

        self.full_clean()
        super().save(*args, **kwargs)