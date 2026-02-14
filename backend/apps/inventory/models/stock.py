from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .product import Product
from .warehouse import Warehouse

class Stock(BaseModel):
    """
    رصيد المخزون الحالي (Current Stock Level).
    هذا الجدول يوضح الكمية المتاحة من كل منتج في كل مخزن.
    لا يتم التعديل فيه يدوياً، بل من خلال حركات مخزنية (Transactions).
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='stock_levels',
        verbose_name=_("المنتج")
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='stock_levels',
        verbose_name=_("المخزن")
    )
    quantity = models.DecimalField(
        _("الكمية الحالية"), 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    
    # مكان التخزين الدقيق (اختياري)
    location = models.CharField(
        _("موقع التخزين (رف/ممر)"), 
        max_length=50, 
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = _("رصيد مخزون")
        verbose_name_plural = _("أرصدة المخزون")
        unique_together = ('product', 'warehouse')  # المنتج لا يتكرر في نفس المخزن مرتين

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}: {self.quantity}"