import os
import uuid
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import SoftDeleteModel
from apps.core.models.sequences import Sequence 
from apps.core.models.company import Company 
from .category import Category
from .unit import Unit 

# دالة لتوليد مسار آمن لصور المنتجات
def product_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(f"company_{instance.company_id}/products/", filename)


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

    # =========================================================================
    # 1. الربط الأمني بالشركة والتصنيفات
    # =========================================================================
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='products', 
        verbose_name=_("الشركة")
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_("التصنيف"))
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='products', verbose_name=_("وحدة القياس"))
    
    # =========================================================================
    # 2. البيانات الأساسية
    # =========================================================================
    name = models.CharField(_("اسم المنتج"), max_length=255)
    sku = models.CharField(_("كود المنتج"), max_length=100, blank=True) 
    barcode = models.CharField(_("باركود"), max_length=100, null=True, blank=True)
    product_type = models.CharField(_("نوع المنتج"), max_length=20, choices=PRODUCT_TYPES, default='storable')
    
    # استخدام المسار الآمن للصور اللي لمحنا ليه فوق
    image = models.ImageField(_("صورة المنتج"), upload_to=product_image_path, null=True, blank=True)
    description = models.TextField(_("وصف تفصيلي"), null=True, blank=True)
    
    # =========================================================================
    # 3. بيانات التسعير والمخزون
    # =========================================================================
    cost_price = models.DecimalField(_("سعر التكلفة الافتراضي"), max_digits=12, decimal_places=2, default=0)
    average_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name=_("متوسط التكلفة"))
    sale_price = models.DecimalField(_("سعر البيع الافتراضي"), max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("حد الطلب"))
    
    # =========================================================================
    # 4. الربط المحاسبي (Accounting Links) - الإضافة الجوهرية للـ ERP
    # =========================================================================
    income_account = models.ForeignKey(
        'accounting.Account', 
        on_delete=models.RESTRICT, 
        related_name='income_products', 
        null=True, blank=True,
        verbose_name=_("حساب الإيرادات"),
        help_text=_("إذا تُرِك فارغاً، سيتم استخدام حساب الإيرادات الخاص بتصنيف المنتج.")
    )
    expense_account = models.ForeignKey(
        'accounting.Account', 
        on_delete=models.RESTRICT, 
        related_name='expense_products', 
        null=True, blank=True,
        verbose_name=_("حساب المصروفات / التكلفة"),
        help_text=_("إذا تُرِك فارغاً، سيتم استخدام حساب التكلفة الخاص بتصنيف المنتج.")
    )

    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['company', 'name']
        
        # القيد الذكي: الـ SKU لا يتكرر داخل نفس الشركة للمنتجات النشطة فقط
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'sku'],
                condition=Q(is_deleted=False),
                name='unique_active_sku_per_company'
            )
        ]

    def save(self, *args, **kwargs):
        # توليد التسلسل بشكل منفصل لكل شركة
        if not self.sku:
            seq_key = f"product_sku_comp_{self.company_id}"
            self.sku = Sequence.next_number(seq_key, prefix='PROD-', padding=6)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.name}"