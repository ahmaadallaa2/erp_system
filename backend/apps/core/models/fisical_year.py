from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import SoftDeleteModel


class FiscalYear(SoftDeleteModel):
    """
    موديل السنة المالية.
    يستخدم لتحديد الفترات المالية الخاصة بكل شركة.
    """

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='fiscal_years',
        verbose_name=_("الشركة")
    )

    name = models.CharField(
        _("اسم السنة المالية"),
        max_length=100,
        help_text=_("مثال: FY2026 أو 2026")
    )

    start_date = models.DateField(
        _("تاريخ البداية")
    )

    end_date = models.DateField(
        _("تاريخ النهاية")
    )

    is_active = models.BooleanField(
        _("نشطة حالياً"),
        default=False,
        help_text=_("هل هذه هي السنة المالية المستخدمة حالياً؟")
    )

    is_closed = models.BooleanField(
        _("مقفلة"),
        default=False,
        help_text=_("إذا تم قفلها، لا يُسمح بإضافة حركات محاسبية جديدة عليها.")
    )

    class Meta:
        verbose_name = _("السنة المالية")
        verbose_name_plural = _("السنوات المالية")
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'name'],
                condition=Q(is_deleted=False),
                name='unique_active_fiscal_year_name_per_company'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    def clean(self):
        super().clean()

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("تاريخ البداية يجب أن يكون قبل أو يساوي تاريخ النهاية."))

        # منع وجود أكثر من سنة مالية نشطة لنفس الشركة
        if self.is_active:
            qs = FiscalYear.objects.filter(
                company=self.company,
                is_active=True,
                is_deleted=False
            )

            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError(_("لا يمكن أن يكون هناك أكثر من سنة مالية نشطة لنفس الشركة."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
