# apps/accounting/models/journal.py

from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel


class Journal(SoftDeleteModel):
    """
    نموذج دفاتر اليومية.
    يُستخدم لتقسيم القيود المحاسبية حسب نوع العملية.
    """

    JOURNAL_TYPES = [
        ('sale', _('مبيعات (Sales)')),
        ('purchase', _('مشتريات (Purchases)')),
        ('cash', _('نقدية (Cash)')),
        ('bank', _('بنك (Bank)')),
        ('general', _('عمليات متنوعة (General/Miscellaneous)')),
    ]

    JOURNAL_ACCOUNT_TYPE_MAP = {
        'sale': 'income',
        'purchase': 'expense',
        'cash': 'asset',
        'bank': 'asset',
        'general': None,
    }

    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='journals',
        verbose_name=_("الشركة")
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_("اسم الدفتر")
    )

    code = models.CharField(
        max_length=10,
        verbose_name=_("الكود"),
        help_text=_("مثل: SAL, PUR, CASH, BNK")
    )

    type = models.CharField(
        max_length=20,
        choices=JOURNAL_TYPES,
        verbose_name=_("النوع")
    )

    default_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='default_journals',
        verbose_name=_("الحساب الافتراضي"),
        help_text=_(
            "يُستخدم تلقائياً عند إنشاء قيود من هذا الدفتر. "
            "يجب أن يكون حساباً قابلاً للترحيل ومتوافقاً مع نوع الدفتر."
        )
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("نشط")
    )

    class Meta:
        verbose_name = _("دفتر يومية")
        verbose_name_plural = _("دفاتر اليومية")
        ordering = ['company', 'type', 'code']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                condition=Q(is_deleted=False),
                name='unique_journal_code_per_company'
            )
        ]
        indexes = [
            models.Index(fields=['company', 'code']),
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        super().clean()

        if self.default_account:
            # الحساب الافتراضي يجب أن يتبع نفس الشركة
            if self.default_account.company_id != self.company_id:
                raise ValidationError(
                    _('الحساب الافتراضي يجب أن يتبع نفس الشركة.')
                )

            # منع استخدام الحسابات التجميعية
            if not self.default_account.is_postable:
                raise ValidationError(
                    _('الحساب الافتراضي يجب أن يكون حساباً قابلاً للترحيل، وليس حساباً تجميعياً.')
                )

            # مطابقة نوع الحساب مع نوع الدفتر
            expected_type = self.JOURNAL_ACCOUNT_TYPE_MAP.get(self.type)
            if expected_type and self.default_account.account_type != expected_type:
                raise ValidationError(
                    _(
                        f'نوع الحساب غير متوافق. '
                        f'دفتر "{self.get_type_display()}" يحتاج حساباً من نوع '
                        f'"{expected_type}"، بينما الحساب المختار من نوع '
                        f'"{self.default_account.account_type}".'
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)