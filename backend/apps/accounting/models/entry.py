from decimal import Decimal

from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel, BaseModel, Sequence


class JournalEntry(SoftDeleteModel):
    """
    قيد اليومية (رأس القيد).
    """

    STATUS_CHOICES = [
        ('draft', _('مسودة (Draft)')),
        ('posted', _('مُرحّل (Posted)')),
        ('cancelled', _('ملغي (Cancelled)')),
    ]

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='journal_entries',
        verbose_name=_("الشركة")
    )

    journal = models.ForeignKey(
        'accounting.Journal',
        on_delete=models.RESTRICT,
        related_name='entries',
        verbose_name=_("دفتر اليومية")
    )

    entry_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("رقم القيد"),
        help_text=_("يتم توليده تلقائياً بناءً على كود الدفتر.")
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name=_("تاريخ القيد")
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("رقم المرجع")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_("الحالة")
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("البيان / الملاحظات")
    )

    class Meta:
        verbose_name = _("قيد يومية")
        verbose_name_plural = _("قيود اليومية")
        ordering = ['-date', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'entry_number'],
                condition=Q(is_deleted=False),
                name='unique_journal_entry_number_per_company'
            )
        ]
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'reference']),
        ]

    def __str__(self):
        return f"{self.entry_number} - {self.reference or 'بدون مرجع'}"

    @property
    def total_debit(self) -> Decimal:
        return self.items.aggregate(total=Sum('debit')).get('total') or Decimal('0.00')

    @property
    def total_credit(self) -> Decimal:
        return self.items.aggregate(total=Sum('credit')).get('total') or Decimal('0.00')

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit and self.total_debit > Decimal('0.00')

    def clean(self):
        super().clean()

        # journal لازم يتبع نفس الشركة
        if self.journal_id and self.company_id and self.journal.company_id != self.company_id:
            raise ValidationError(_('دفتر اليومية لا يتبع نفس الشركة.'))

        # حماية القيود المُرحّلة والملغاة من التعديل
        if self.pk:
            original = (
                JournalEntry.objects
                .filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )
            if original in ('posted', 'cancelled'):
                if self.status == original:
                    raise ValidationError(
                        _('لا يمكن تعديل بيانات قيد مُرحّل أو ملغي. يجب إنشاء قيد عكسي للتصحيح.')
                    )

        # عند الترحيل: لازم القيد يكون متوازن
        if self.status == 'posted':
            self.validate_balanced()

    def validate_balanced(self):
        if not self.pk or not self.items.exists():
            raise ValidationError(_('لا يمكن ترحيل قيد فارغ لا يحتوي على أسطر.'))

        totals = self.items.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )

        total_debit = totals.get('total_debit') or Decimal('0.00')
        total_credit = totals.get('total_credit') or Decimal('0.00')

        if total_debit != total_credit:
            raise ValidationError(
                _(f'القيد غير متوازن: إجمالي المدين ({total_debit}) لا يساوي إجمالي الدائن ({total_credit}).')
            )

        if total_debit == Decimal('0.00'):
            raise ValidationError(_('لا يمكن ترحيل قيد بقيمة صفر.'))

    def post(self):
        if self.status != 'draft':
            raise ValidationError(_('يمكن ترحيل المسودات فقط.'))

        self.status = 'posted'
        self.full_clean()
        super().save(update_fields=['status', 'updated_at'])

    def cancel(self):
        if self.status == 'cancelled':
            raise ValidationError(_('القيد ملغي بالفعل.'))

        if self.status == 'posted':
            raise ValidationError(
                _('لا يمكن إلغاء قيد مُرحّل مباشرةً. يجب إنشاء قيد عكسي أولاً.')
            )

        self.status = 'cancelled'
        self.full_clean()
        super().save(update_fields=['status', 'updated_at'])

    def save(self, *args, **kwargs):
        if not self.entry_number:
            if not self.journal_id:
                raise ValueError("Journal entry must have a journal before generating entry number.")

            seq_key = f"journal_{self.company_id}_{self.journal.code}"
            self.entry_number = Sequence.next_number(
                seq_key,
                prefix=f"{self.journal.code}-",
                padding=4
            )

        self.full_clean()
        super().save(*args, **kwargs)


class JournalItem(BaseModel):
    """
    سطر القيد.
    """

    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("قيد اليومية")
    )

    account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='journal_items',
        verbose_name=_("الحساب")
    )

    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_items',
        verbose_name=_("الشريك (عميل / مورد)")
    )

    description = models.CharField(
        max_length=255,
        verbose_name=_("البيان")
    )

    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("مدين")
    )

    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("دائن")
    )

    class Meta:
        verbose_name = _("سطر القيد")
        verbose_name_plural = _("سطور القيود")
        ordering = ['id']

    def __str__(self):
        return f"{self.account.name} - مدين: {self.debit} | دائن: {self.credit}"

    def clean(self):
        super().clean()

        # حماية سطور القيود المُرحلة أو الملغاة
        if self.entry_id:
            entry_status = (
                JournalEntry.objects
                .filter(pk=self.entry_id)
                .values_list('status', flat=True)
                .first()
            )
            if entry_status in ('posted', 'cancelled'):
                raise ValidationError(_('لا يمكن تعديل سطور قيد مُرحّل أو ملغي.'))

        if self.debit < 0 or self.credit < 0:
            raise ValidationError(_('لا يمكن إدخال قيم سالبة.'))

        if self.debit > 0 and self.credit > 0:
            raise ValidationError(_('السطر الواحد يجب أن يكون مدينًا أو دائنًا، وليس الاثنين معًا.'))

        if self.debit == Decimal('0.00') and self.credit == Decimal('0.00'):
            raise ValidationError(_('لا يمكن حفظ سطر بقيمتين صفريتين.'))

        if self.account_id:
            if not self.account.is_postable:
                raise ValidationError(_('لا يمكن الترحيل على حساب تجميعي. اختر حسابًا قابلاً للترحيل.'))

            if self.entry_id and self.account.company_id != self.entry.company_id:
                raise ValidationError(_('الحساب لا يتبع نفس شركة القيد.'))

            if self.partner and self.entry_id and self.partner.company_id != self.entry.company_id:
                raise ValidationError(_('الشريك لا يتبع نفس شركة القيد.'))

            if self.partner and not self.account.allow_reconciliation:
                raise ValidationError(
                    _('لا يمكن تحديد شريك لحساب لا يقبل التسوية.')
                )

            if self.account.allow_reconciliation and not self.partner:
                raise ValidationError(
                    _('هذا الحساب يقبل التسوية، لذلك تحديد الشريك إلزامي.')
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)