from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel


class Unit(SoftDeleteModel):
    name = models.CharField(_("اسم الوحدة"), max_length=50)
    short_name = models.CharField(_("الرمز"), max_length=10)
    is_active = models.BooleanField(_("نشطة"), default=True)

    class Meta:
        verbose_name = _("وحدة قياس")
        verbose_name_plural = _("وحدات القياس")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=Q(is_deleted=False),
                name='unique_active_unit_name'
            ),
            models.UniqueConstraint(
                fields=['short_name'],
                condition=Q(is_deleted=False),
                name='unique_active_unit_short_name'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_name})"