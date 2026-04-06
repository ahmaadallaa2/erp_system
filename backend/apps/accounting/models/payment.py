from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import SoftDeleteModel, Sequence


class Payment(SoftDeleteModel):
    PAYMENT_TYPES = [
        ('inbound', _('سند قبض (من عميل)')),
        ('outbound', _('سند صرف (لمورد)')),
    ]

    PAYMENT_METHODS = [
        ('cash', _('نقدي (خزينة)')),
        ('bank', _('تحويل بنكي / شيك')),
    ]

    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('posted', _('مرحّل')),
        ('cancelled', _('ملغي')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.RESTRICT,
        related_name='payments',
        verbose_name=_("الشركة")
    )

    branch = models.ForeignKey(
        'core.Branch',
        on_delete=models.RESTRICT,
        related_name='payments',
        verbose_name=_("الفرع")
    )

    voucher_number = models.CharField(
        _("رقم السند"),
        max_length=50,
        blank=True
    )

    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.RESTRICT,
        related_name='payments',
        verbose_name=_("الشريك (المورد/العميل)")
    )

    payment_type = models.CharField(
        _("نوع السند"),
        max_length=20,
        choices=PAYMENT_TYPES
    )

    payment_method = models.CharField(
        _("طريقة الدفع"),
        max_length=20,
        choices=PAYMENT_METHODS
    )

    account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='payments',
        verbose_name=_("حساب الخزينة / البنك")
    )

    amount = models.DecimalField(
        _("المبلغ"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    date = models.DateField(
        _("تاريخ السند"),
        default=timezone.now
    )

    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    reference = models.CharField(
        _("المرجع / رقم الشيك"),
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        _("البيان / الملاحظات"),
        blank=True
    )

    journal_entry = models.OneToOneField(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_payment',
        verbose_name=_("قيد اليومية المرتبط")
    )

    class Meta:
        verbose_name = _("سند قبض / صرف")
        verbose_name_plural = _("سندات القبض والصرف")
        ordering = ['-date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'voucher_number'],
                condition=Q(is_deleted=False),
                name='unique_payment_voucher_number_per_branch'
            )
        ]
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['company', 'payment_type']),
            models.Index(fields=['company', 'status']),
        ]

    def __str__(self):
        return f"{self.voucher_number} - {self.partner.name} - {self.amount}"

    def clean(self):
        super().clean()

        if self.branch and self.company and self.branch.company_id != self.company_id:
            raise ValidationError(_("الفرع لا يتبع نفس الشركة."))

        if self.partner and self.company and self.partner.company_id != self.company_id:
            raise ValidationError(_("الشريك لا يتبع نفس الشركة."))

        if self.account and self.company and self.account.company_id != self.company_id:
            raise ValidationError(_("الحساب لا يتبع نفس الشركة."))

        if self.amount is None or self.amount <= 0:
            raise ValidationError(_("يجب أن يكون المبلغ أكبر من الصفر."))

        if self.account_id and not self.account.is_postable:
            raise ValidationError(_("يجب اختيار حساب قابل للترحيل."))

        if self.account_id and self.account.account_type != 'asset':
            raise ValidationError(_("حساب السند يجب أن يكون من نوع أصل (خزينة أو بنك)."))

        if self.payment_type == 'inbound':
            if self.partner and self.partner.partner_type not in ['customer', 'both']:
                raise ValidationError(_("سند القبض يجب أن يكون مرتبطًا بعميل."))

        if self.payment_type == 'outbound':
            if self.partner and self.partner.partner_type not in ['supplier', 'both']:
                raise ValidationError(_("سند الصرف يجب أن يكون مرتبطًا بمورد."))

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            if not self.branch_id:
                raise ValueError("Payment must have a branch before generating voucher number.")

            if self.payment_type == 'inbound':
                prefix = "REC-"
                seq_key = f"receipt_branch_{self.branch_id}"
            else:
                prefix = "PAY-"
                seq_key = f"payment_branch_{self.branch_id}"

            self.voucher_number = Sequence.next_number(seq_key, prefix=prefix, padding=5)

        self.full_clean()
        super().save(*args, **kwargs)