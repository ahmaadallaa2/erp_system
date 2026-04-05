from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel, Branch, Sequence
from apps.core.models.company import Company
from apps.users.models import User


class Warehouse(SoftDeleteModel):
    WAREHOUSE_TYPES = [
        ('main', _('مخزن رئيسي (Main)')),
        ('sub', _('مخزن فرعي / معرض (Showroom)')),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name=_("الشركة")
    )

    name = models.CharField(_("اسم المخزن"), max_length=100)

    code = models.CharField(
        _("كود المخزن"),
        max_length=20,
        blank=True
    )

    warehouse_type = models.CharField(
        _("نوع المخزن"),
        max_length=20,
        choices=WAREHOUSE_TYPES,
        default='sub'
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='warehouses',
        verbose_name=_("الفرع التابع له")
    )

    keeper = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        verbose_name=_("أمين المخزن")
    )

    address = models.CharField(_("العنوان التفصيلي"), max_length=255, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("مخزن")
        verbose_name_plural = _("المخازن")
        ordering = ['company', 'branch', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'name'],
                condition=Q(is_deleted=False),
                name='unique_active_warehouse_name_per_branch'
            ),
            models.UniqueConstraint(
                fields=['company', 'code'],
                condition=Q(is_deleted=False),
                name='unique_active_warehouse_code_per_company'
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_warehouse_type_display()} ({self.branch.name})"

    def clean(self):
        super().clean()

        if self.branch and self.company and self.branch.company_id != self.company_id:
            raise ValidationError(_("الفرع المختار لا يتبع نفس الشركة."))

        if self.keeper and getattr(self.keeper, 'company_id', None):
            if self.company_id and self.keeper.company_id != self.company_id:
                raise ValidationError(_("أمين المخزن يجب أن يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        if not self.code:
            if not self.company_id:
                raise ValueError("Warehouse must have a company before generating code.")

            seq_key = f"warehouse_code_comp_{self.company_id}"
            self.code = Sequence.next_number(seq_key, prefix='WH-', padding=4)

        self.full_clean()
        super().save(*args, **kwargs)