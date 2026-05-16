from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import SoftDeleteModel, Sequence


class PurchaseInvoice(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('posted', _('مرحلة')),
        ('cancelled', _('ملغاة')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.RESTRICT,
        related_name='purchase_invoices',
        verbose_name=_("الشركة")
    )

    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("رقم الفاتورة")
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.RESTRICT,
        related_name='purchase_invoices',
        verbose_name=_("الفرع")
    )

    supplier = models.ForeignKey(
        'partners.Partner',
        on_delete=models.RESTRICT,
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        related_name='purchase_invoices',
        verbose_name=_("المورد")
    )

    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='purchase_invoices',
        verbose_name=_("مخزن الاستلام")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_("الحالة")
    )

    invoice_date = models.DateField(
        default=timezone.now,
        verbose_name=_("تاريخ الفاتورة")
    )

    vendor_bill_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("رقم فاتورة المورد")
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("إجمالي الفاتورة"),
        editable=False
    )

    journal_entry = models.OneToOneField(
        "accounting.JournalEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_invoice",
    )

    shipping_cost = models.DecimalField(
        _("تكلفة الشحن الداخلي"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    clearance_cost = models.DecimalField(
        _("تكلفة الأرضيات والتخليص"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    commission_percentage = models.DecimalField(
        _("نسبة عمولة المورد (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00")
    )

    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))

    class Meta:
        verbose_name = _("فاتورة مشتريات")
        verbose_name_plural = _("فواتير المشتريات")
        ordering = ['-invoice_date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'invoice_number'],
                condition=Q(is_deleted=False),
                name='unique_purchase_invoice_number_per_branch'
            )
        ]

    def __str__(self):
        return f"[{self.invoice_number}] {self.supplier.name if self.supplier else 'بدون مورد'}"

    def clean(self):
        super().clean()

        if self.branch and self.company and self.branch.company_id != self.company_id:
            raise ValidationError(_("الفرع لا يتبع نفس الشركة."))

        if self.warehouse and self.company and self.warehouse.company_id != self.company_id:
            raise ValidationError(_("المخزن لا يتبع نفس الشركة."))

        if self.supplier and self.company and self.supplier.company_id != self.company_id:
            raise ValidationError(_("المورد لا يتبع نفس الشركة."))

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            if not self.branch_id:
                raise ValueError("Purchase invoice must have a branch before generating invoice number.")

            seq_key = f"pinv_branch_{self.branch_id}"
            self.invoice_number = Sequence.next_number(seq_key, prefix='PINV-', padding=5)

        self.full_clean()
        super().save(*args, **kwargs)
