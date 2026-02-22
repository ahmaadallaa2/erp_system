import os
import uuid
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from apps.core.models.base import SoftDeleteModel
from apps.core.models.sequences import Sequence 
from apps.core.models.company import Company # الربط بالشركة ضروري جداً
from .category import Category
from .unit import Unit # تأكد من أن الاسم يطابق ما كتبناه في ملف unit.py

def get_product_image_path(instance, filename):
    """دالة لتوليد اسم آمن لصور المنتجات على السيرفرات السحابية"""
    ext = os.path.splitext(filename)[1].lower()
    return f"products/company_{instance.company_id}/{uuid.uuid4().hex}{ext}"

class Product(SoftDeleteModel):
    """
    بطاقة المنتج الرئيسية.
    تعمل كـ Master Data لحركات المخزون والمبيعات.
    """
    PRODUCT_TYPES = (
        ('storable', _('منتج مخزني')),   # له رصيد وجرد (مثل الأجهزة الإلكترونية)
        ('service', _('خدمة')),          # ليس له مخزون (مثل صيانة، شحن)
        ('consumable', _('مستهلك')),     # يشترى ويستخدم داخلياً (مثل أدوات التغليف)
    )

    # 1. الربط الأمني بالشركة
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='products', 
        verbose_name=_("الشركة")
    )

    name = models.CharField(_("اسم المنتج"), max_length=255)
    # أزلنا unique=True من هنا لحل مشكلة الحذف الناعم
    sku = models.CharField(_("SKU"), max_length=100, blank=True) 
    barcode = models.CharField(_("باركود"), max_length=100, null=True, blank=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_("التصنيف"))
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='products', verbose_name=_("وحدة القياس"))
    product_type = models.CharField(_("نوع المنتج"), max_length=20, choices=PRODUCT_TYPES, default='storable')
    
    cost_price = models.DecimalField(_("سعر التكلفة الافتراضي"), max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(_("سعر البيع الافتراضي"), max_digits=12, decimal_places=2, default=0)
    
    # استخدام المسار الآمن للصور
    image = models.ImageField(_("صورة المنتج"), upload_to=get_product_image_path, null=True, blank=True)
    description = models.TextField(_("وصف تفصيلي"), null=True, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['company', 'name']
        
        # 2. القيد الذكي: الـ SKU لا يتكرر داخل نفس الشركة للمنتجات النشطة فقط
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'sku'],
                condition=Q(is_deleted=False),
                name='unique_active_sku_per_company'
            )
        ]

    def save(self, *args, **kwargs):
        # 3. توليد التسلسل بشكل منفصل لكل شركة
        if not self.sku:
            # مثال: العداد الخاص بالشركة رقم 1 سيكون key="product_sku_comp_1"
            seq_key = f"product_sku_comp_{self.company_id}"
            self.sku = Sequence.next_number(seq_key, prefix='PROD-', padding=6)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.name}"