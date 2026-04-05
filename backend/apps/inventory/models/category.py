from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel
from apps.core.models.company import Company


class Category(SoftDeleteModel):
    """
    تصنيف المنتجات (نظام شجري).
    مثال: ملابس -> رجالي -> قمصان
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_("الشركة")
    )

    name = models.CharField(_("اسم التصنيف"), max_length=100)

    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_("التصنيف الأب")
    )

    description = models.TextField(_("وصف"), null=True, blank=True)
    is_active = models.BooleanField(_("نشطة"), default=True)
    icon = models.ImageField(_("أيقونة"), upload_to='categories/', null=True, blank=True)

    class Meta:
        verbose_name = _("تصنيف منتج")
        verbose_name_plural = _("تصنيفات المنتجات")
        ordering = ['company', 'parent__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name', 'parent'],
                condition=Q(is_deleted=False),
                name='unique_category_name_per_parent_per_company'
            )
        ]

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' > '.join(full_path[::-1])

    def clean(self):
        super().clean()

        if self.parent:
            if self.parent_id == self.id:
                raise ValidationError(_("لا يمكن أن يكون التصنيف أبًا لنفسه."))

            if self.parent.company_id != self.company_id:
                raise ValidationError(_("التصنيف الأب يجب أن يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)