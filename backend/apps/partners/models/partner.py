from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel, Sequence
from apps.core.models.company import Company


class Partner(SoftDeleteModel):
    class PartnerType(models.TextChoices):
        CUSTOMER = 'customer', _('عميل')
        SUPPLIER = 'supplier', _('مورد')
        BOTH = 'both', _('عميل ومورد')

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='partners',
        verbose_name=_("الشركة")
    )

    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("كود العميل/المورد"),
        help_text=_("يترك فارغاً للتوليد التلقائي")
    )

    partner_type = models.CharField(
        max_length=20,
        choices=PartnerType.choices,
        default=PartnerType.CUSTOMER,
        verbose_name=_("النوع")
    )

    name = models.CharField(
        max_length=150,
        verbose_name=_("الاسم التجاري / الكامل")
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("رقم الهاتف")
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("رقم الجوال (إضافي)")
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("البريد الإلكتروني")
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("الموقع الإلكتروني")
    )

    address = models.TextField(
        blank=True,
        verbose_name=_("العنوان التفصيلي")
    )
    city = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("المدينة")
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("الرقم الضريبي (VAT)")
    )
    commercial_record = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("السجل التجاري")
    )

    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("حد الائتمان")
    )

    initial_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("الرصيد الافتتاحي")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط")
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("ملاحظات داخلية")
    )

    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='partners',
        verbose_name=_("الموظف المسؤول")
    )

    class Meta:
        verbose_name = _("شريك")
        verbose_name_plural = _("الشركاء")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                condition=Q(is_deleted=False),
                name='unique_partner_code_per_company'
            )
        ]

    def __str__(self):
        return f"[{self.code}] {self.name} - {self.get_partner_type_display()}"

    def save(self, *args, **kwargs):
        if not self.code:
            if not self.company_id:
                raise ValueError("Partner must have a company before generating code.")

            if self.partner_type == self.PartnerType.CUSTOMER:
                prefix = 'CUST-'
                seq_key = f"customer_code_comp_{self.company_id}"
            elif self.partner_type == self.PartnerType.SUPPLIER:
                prefix = 'SUP-'
                seq_key = f"supplier_code_comp_{self.company_id}"
            else:
                prefix = 'PRT-'
                seq_key = f"partner_code_both_comp_{self.company_id}"

            self.code = Sequence.next_number(seq_key, prefix=prefix, padding=5)

        super().save(*args, **kwargs)

    @property
    def current_balance(self):
        """
        حساب الرصيد الحالي من القيود اليومية المعتمدة فقط.
        """
        totals = self.journal_items.filter(
            entry__status='posted'
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )

        debit = totals.get('total_debit') or Decimal('0.00')
        credit = totals.get('total_credit') or Decimal('0.00')
        init_balance = self.initial_balance or Decimal('0.00')

        if self.partner_type == self.PartnerType.CUSTOMER:
            return init_balance + debit - credit

        # supplier or both
        return init_balance + credit - debit