from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class Unit(SoftDeleteModel):
    name = models.CharField(_("اسم الوحدة"), max_length=50) # قطعة
    short_name = models.CharField(_("الرمز"), max_length=10) # PCS, KG, M
    is_active = models.BooleanField(_("نشطة"), default=True)
    
    # معامل التحويل (مستقبلاً لو حبيت تعمل: الكرتونة = 12 قطعة)
    # factor = models.PositiveIntegerField(default=1) 

    class Meta:
        verbose_name = _("وحدة قياس")
        verbose_name_plural = _("وحدات القياس")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.short_name})"