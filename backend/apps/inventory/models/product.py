import os
import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import SoftDeleteModel
from apps.core.models.sequences import Sequence
from apps.core.models.company import Company
from .category import Category
from .unit import Unit


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
        ('storable', _('منتج مخزني')),
        ('service', _('خدمة')),
        ('consumable', _('مستهلك')),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("الشركة")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("التصنيف")
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_("وحدة القياس")
    )

    name = models.CharField(_("اسم المنتج"), max_length=255)
    sku = models.CharField(_("كود المنتج"), max_length=100, blank=True)
    barcode = models.CharField(_("باركود"), max_length=100, null=True, blank=True)
    product_type = models.CharField(
        _("نوع المنتج"),
        max_length=20,
        choices=PRODUCT_TYPES,
        default='storable'
    )

    image = models.ImageField(_("صورة المنتج"), upload_to=product_image_path, null=True, blank=True)
    description = models.TextField(_("وصف تفصيلي"), null=True, blank=True)

    cost_price = models.DecimalField(_("سعر التكلفة الافتراضي"), max_digits=12, decimal_places=2, default=Decimal("0.00"))
    average_cost = models.DecimalField(_("متوسط التكلفة"), max_digits=12, decimal_places=2, default=Decimal("0.00"))
    sale_price = models.DecimalField(_("سعر البيع الافتراضي"), max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reorder_point = models.DecimalField(_("حد الطلب"), max_digits=10, decimal_places=2, default=Decimal("0.00"))

    income_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='income_products',
        null=True,
        blank=True,
        verbose_name=_("حساب الإيرادات"),
        help_text=_("إذا تُرِك فارغاً، سيتم استخدام حساب الإيرادات الخاص بتصنيف المنتج.")
    )
    expense_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='expense_products',
        null=True,
        blank=True,
        verbose_name=_("حساب المصروفات / التكلفة"),
        help_text=_("إذا تُرِك فارغاً، سيتم استخدام حساب التكلفة الخاص بتصنيف المنتج.")
    )

    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("منتج")
        verbose_name_plural = _("المنتجات")
        ordering = ['company', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'sku'],
                condition=Q(is_deleted=False),
                name='unique_active_sku_per_company'
            )
        ]

    def __str__(self):
        return f"[{self.sku}] {self.name}"

    def clean(self):
        super().clean()

        if self.category and self.category.company_id != self.company_id:
            raise ValidationError(_("التصنيف المختار لا يتبع نفس الشركة."))

        # فعّل السطور دي لو الحسابات مرتبطة بشركة
        if self.income_account and hasattr(self.income_account, 'company_id'):
            if self.income_account.company_id != self.company_id:
                raise ValidationError(_("حساب الإيرادات لا يتبع نفس الشركة."))

        if self.expense_account and hasattr(self.expense_account, 'company_id'):
            if self.expense_account.company_id != self.company_id:
                raise ValidationError(_("حساب المصروفات لا يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        if not self.sku:
            if not self.company_id:
                raise ValueError("Product must have a company before generating SKU.")

            seq_key = f"product_sku_comp_{self.company_id}"
            self.sku = Sequence.next_number(seq_key, prefix='PROD-', padding=6)

        self.full_clean()
        super().save(*args, **kwargs)