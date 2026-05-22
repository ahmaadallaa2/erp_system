from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import SoftDeleteModel, Sequence


class SalesInvoice(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('posted', _('مرحلة')),
        ('cancelled', _('ملغاة')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.RESTRICT,
        related_name='sales_invoices',
        verbose_name=_("الشركة")
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.RESTRICT,
        related_name='sales_invoices',
        verbose_name=_("الفرع")
    )

    invoice_number = models.CharField(
        _("رقم الفاتورة"),
        max_length=50,
        blank=True
    )

    customer = models.ForeignKey(
        'partners.Partner',
        on_delete=models.RESTRICT,
        related_name='sales_invoices',
        verbose_name=_("العميل"),
        limit_choices_to={'partner_type__in': ['customer', 'both']}
    )

    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='sales_invoices',
        verbose_name=_("المخزن (يُصرف منه)"),
        null=True,
        blank=True,
    )

    date = models.DateField(
        _("تاريخ الفاتورة"),
        default=timezone.now
    )

    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    total_amount = models.DecimalField(
        _("إجمالي الفاتورة"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    journal_entry = models.OneToOneField(
        "accounting.JournalEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sales_invoice",
    )

    posted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_sales_invoices",
    )

    posted_at = models.DateTimeField(null=True, blank=True)

    cancelled_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_sales_invoices",
    )

    cancelled_at = models.DateTimeField(null=True, blank=True)

    cancellation_reason = models.TextField(blank=True)

    notes = models.TextField(
        _("ملاحظات"),
        blank=True
    )

    class Meta:
        verbose_name = _("فاتورة مبيعات")
        verbose_name_plural = _("فواتير المبيعات")
        ordering = ['-date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'invoice_number'],
                condition=Q(is_deleted=False),
                name='unique_sales_invoice_number_per_branch'
            )
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    def clean(self):
        super().clean()

        if self.branch and self.company and self.branch.company_id != self.company_id:
            raise ValidationError(_("الفرع لا يتبع نفس الشركة."))

        if self.customer and self.company and self.customer.company_id != self.company_id:
            raise ValidationError(_("العميل لا يتبع نفس الشركة."))

        if self.warehouse and self.company and self.warehouse.company_id != self.company_id:
            raise ValidationError(_("المخزن لا يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            if not self.branch_id:
                raise ValueError("Sales invoice must have a branch before generating invoice number.")

            seq_key = f"sinv_branch_{self.branch_id}"
            self.invoice_number = Sequence.next_number(seq_key, prefix='SINV-', padding=5)

        self.full_clean()
        super().save(*args, **kwargs)
