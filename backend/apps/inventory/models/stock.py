from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import BaseModel
from apps.core.models.company import Company # الربط الأمني لتحسين الأداء
from .product import Product
from .warehouse import Warehouse

class Stock(BaseModel):
    """
    رصيد المخزون الحالي (Current Stock Level / Quant).
    يتم تحديثه برمجياً فقط عبر حركات المخزون (Stock Moves).
    """
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='stock_levels',
        verbose_name=_("الشركة")
    )
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
    
    # الكمية الفيزيائية الموجودة فعلياً على الرف
    quantity = models.DecimalField(
        _("الكمية الفعلية"), 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    
    # الكمية المحجوزة لفواتير مبيعات أو أوامر تصنيع لم تُسلم بعد
    reserved_quantity = models.DecimalField(
        _("الكمية المحجوزة"), 
        max_digits=12, 
        decimal_places=2, 
        default=0
    )

    # مكان التخزين الدقيق لتسهيل عمل أمين المخزن
    location = models.CharField(
        _("موقع التخزين (رف/ممر)"), 
        max_length=50, 
        null=True, 
        blank=True
    )
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = _("رصيد مخزون")
        verbose_name_plural = _("أرصدة المخزون")
        
        # التحديث الهندسي لمنع التكرار
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'warehouse'], 
                name='unique_product_per_warehouse'
            )
        ]

    def __str__(self):
        return f"{self.product.name} | {self.warehouse.name}: {self.quantity}"

    @property
    def available_quantity(self):
        """
        دالة مساعدة (Property) تحسب الكمية الحقيقية المتاحة للبيع الآن.
        """
        return self.quantity - self.reserved_quantity

    def save(self, *args, **kwargs):
        # ملء حقل الشركة تلقائياً من المستودع لتخفيف العبء على المبرمج لاحقاً
        if not self.company_id and self.warehouse_id:
            self.company_id = self.warehouse.branch.company_id
            
        super().save(*args, **kwargs)