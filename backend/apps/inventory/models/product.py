from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel, Sequence  # هنحتاج Sequence للـ SKU
from .category import Category
from .unit import Unit

class Product(SoftDeleteModel):
    """
    المنتج الرئيسي.
    """
    PRODUCT_TYPES = (
        ('storable', _('منتج مخزني')),   # له رصيد وجرد (موبايل)
        ('service', _('خدمة')),          # ليس له مخزون (صيانة، توصيل)
        ('consumable', _('مستهلك')),     # يشترى ولا يباع (أدوات نظافة، بنزين)
    )

    name = models.CharField(_("اسم المنتج"), max_length=255)
    
    # SKU: Stock Keeping Unit (كود فريد للمنتج)
    sku = models.CharField(_("SKU"), max_length=100, unique=True, blank=True)
    barcode = models.CharField(_("باركود"), max_length=100, null=True, blank=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_("الفئة"))
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='products', verbose_name=_("وحدة القياس"))
    
    product_type = models.CharField(_("نوع المنتج"), max_length=20, choices=PRODUCT_TYPES, default='storable')
    
    # التسعير المبدئي (قائمة الأسعار)
    cost_price = models.DecimalField(_("سعر التكلفة التقديري"), max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(_("سعر البيع"), max_digits=12, decimal_places=2, default=0)
    
    image = models.ImageField(_("صورة المنتج"), upload_to='products/', null=True, blank=True)
    description = models.TextField(_("وصف تفصيلي"), null=True, blank=True)

    # هل المنتج نشط للبيع والشراء؟
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['name']

    def save(self, *args, **kwargs):
        # توليد SKU تلقائي لو المستخدم مدخلهوش
        if not self.sku:
            self.sku = Sequence.next_number('product_sku', prefix='PROD-', padding=6)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.sku}] {self.name}"