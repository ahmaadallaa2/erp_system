from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class Category(SoftDeleteModel):
    """
    تصنيف المنتجات (نظام شجري).
    مثال: ملابس -> رجالي -> قمصان
    """
    name = models.CharField(_("اسم الفئة"), max_length=100)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories', 
        verbose_name=_("الفئة الأب")
    )
    description = models.TextField(_("وصف"), null=True, blank=True)
    icon = models.ImageField(_("أيقونة"), upload_to='categories/', null=True, blank=True)

    class Meta:
        verbose_name = _("فئة منتج")
        verbose_name_plural = _("فئات المنتجات")
        ordering = ['name']

    def __str__(self):
        # كود عشان يعرض المسار كامل: إلكترونيات > موبايلات
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' > '.join(full_path[::-1])