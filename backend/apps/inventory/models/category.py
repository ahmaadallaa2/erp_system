from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class Category(SoftDeleteModel):
    """
    تصنيف المنتجات (نظام شجري).
    مثال: ملابس -> رجالي -> قمصان
    """
    name = models.CharField(_("اسم التصنيف"), max_length=100)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
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
        ordering = ['parent__name', 'name']

    def __str__(self):
        # كود عشان يعرض المسار كامل: إلكترونيات > موبايلات
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' > '.join(full_path[::-1])