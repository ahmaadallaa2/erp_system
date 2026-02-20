from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from .product import Product
from .warehouse import Warehouse

class StockMovement(BaseModel):
    # تعريف أنواع الحركة
    MOVEMENT_TYPES = (
        ('IN', 'وارد (إضافة)'),
        ('OUT', 'صادر (صرف)'),
    )

    # الربط مع الموديلات التانية
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='movements',
        verbose_name="المنتج"
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.CASCADE, 
        related_name='movements',
        verbose_name="المخزن"
    )
    
    # تفاصيل الحركة
    movement_type = models.CharField(
        max_length=3, 
        choices=MOVEMENT_TYPES, 
        verbose_name="نوع الحركة"
    )
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    
    # بيانات إضافية للتوثيق والرقابة
    reference = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="رقم الفاتورة/المرجع"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    
    # الربط مع تطبيق اليوزرز بتاعك بطريقة احترافية
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="بواسطة"
    )

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"

    class Meta:
        verbose_name = "حركة مخزنية"
        verbose_name_plural = "حركات المخازن"
        ordering = ['-created_at'] # عشان الأحدث يظهر الأول في التقارير