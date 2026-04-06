# apps/accounting/models/account.py

from decimal import Decimal
from django.db import models
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel


class Account(SoftDeleteModel):
    """
    نموذج دليل الحسابات (Chart of Accounts).
    بنية شجرية للحسابات مع دعم multi-company.
    """

    # =========================================================================
    # 1. الخيارات الثابتة
    # =========================================================================
    ACCOUNT_TYPES = [
        ('asset', _('أصل (Asset)')),
        ('liability', _('دين / التزام (Liability)')),
        ('equity', _('حقوق ملكية (Equity)')),
        ('income', _('إيراد (Income/Revenue)')),
        ('expense', _('مصروف (Expense)')),
    ]

    NORMAL_BALANCE_CHOICES = [
        ('debit', _('مدين (Debit)')),
        ('credit', _('دائن (Credit)')),
    ]

    NATURAL_BALANCE_MAP = {
        'asset': 'debit',
        'expense': 'debit',
        'liability': 'credit',
        'equity': 'credit',
        'income': 'credit',
    }

    # =========================================================================
    # 2. الشركة والبيانات الأساسية
    # =========================================================================
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name=_('الشركة')
    )

    code = models.CharField(
        max_length=50,
        verbose_name=_('كود الحساب'),
        help_text=_('كود فريد داخل نفس الشركة (مثال: 1120).')
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('اسم الحساب')
    )

    # =========================================================================
    # 3. الهيكل الشجري والتصنيف
    # =========================================================================
    parent = models.ForeignKey(
        'self',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('الحساب الأب')
    )

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        verbose_name=_('نوع الحساب')
    )

    normal_balance = models.CharField(
        max_length=10,
        choices=NORMAL_BALANCE_CHOICES,
        verbose_name=_('طبيعة الحساب'),
        help_text=_('مدين للأصول والمصروفات، ودائن للخصوم وحقوق الملكية والإيرادات.')
    )

    # =========================================================================
    # 4. إعدادات العمليات المحاسبية
    # =========================================================================
    is_postable = models.BooleanField(
        default=True,
        verbose_name=_('قابل للترحيل'),
        help_text=_('إذا كان False فهو حساب تجميعي فقط ولا تُرحّل عليه قيود مباشرة.')
    )

    allow_reconciliation = models.BooleanField(
        default=False,
        verbose_name=_('يقبل التسوية'),
        help_text=_('يفعل عادةً لحسابات العملاء والموردين والبنوك.')
    )

    # =========================================================================
    # 5. الحالة
    # =========================================================================
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط')
    )

    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('دليل الحسابات')
        ordering = ['company', 'code']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                condition=Q(is_deleted=False),
                name='unique_account_code_per_company'
            )
        ]
        indexes = [
            models.Index(fields=['company', 'code']),
            models.Index(fields=['company', 'parent']),
            models.Index(fields=['company', 'account_type']),
            models.Index(fields=['company', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    # =========================================================================
    # 6. الخصائص المحسوبة
    # =========================================================================
    @property
    def level(self) -> int:
        """
        حساب عمق الحساب في الشجرة.
        """
        depth = 0
        node = self
        while node.parent_id:
            depth += 1
            node = node.parent
        return depth

    @property
    def current_balance(self) -> Decimal:
        """
        رصيد الحساب للحسابات القابلة للترحيل فقط.
        سريع وآمن لأنه يعتمد على Aggregate واحد فقط.

        ملاحظة:
        الحسابات التجميعية لا نحسب رصيدها هنا بشكل recursive حتى لا نسبب بطء.
        أرصدتها تُحسب في التقارير أو services متخصصة.
        """
        if not self.is_postable:
            return Decimal('0.00')

        totals = self.journal_items.filter(
            entry__status='posted'
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )

        debit = totals.get('total_debit') or Decimal('0.00')
        credit = totals.get('total_credit') or Decimal('0.00')

        if self.normal_balance == 'debit':
            return debit - credit
        return credit - debit

    # =========================================================================
    # 7. قواعد التحقق
    # =========================================================================
    def clean(self):
        super().clean()

        # 1) منع الحساب من أن يكون أباً لنفسه
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(_('الحساب لا يمكن أن يكون أباً لنفسه.'))

        # 2) الأب يجب أن يكون من نفس الشركة
        if self.parent and self.parent.company_id != self.company_id:
            raise ValidationError(_('الحساب الأب يجب أن يتبع نفس الشركة.'))

        # 3) نوع الحساب يجب أن يطابق نوع الحساب الأب
        if self.parent and self.parent.account_type != self.account_type:
            raise ValidationError(
                _('نوع الحساب يجب أن يطابق نوع الحساب الأب.')
            )

        # 4) منع جعل الحساب التجميعي ابناً لحساب قابل للترحيل
        if self.parent and self.parent.is_postable:
            raise ValidationError(
                _('لا يمكن إضافة حسابات فرعية تحت حساب قابل للترحيل.')
            )

        # 5) طبيعة الحساب يجب أن تطابق نوعه المحاسبي
        expected_balance = self.NATURAL_BALANCE_MAP.get(self.account_type)
        if expected_balance and self.normal_balance != expected_balance:
            raise ValidationError(
                _('طبيعة الحساب لا تتوافق مع نوع الحساب المحاسبي.')
            )

        # 6) إذا الحساب قابل للترحيل فلا يجوز أن يكون له أبناء
        if self.pk and self.is_postable and self.children.filter(is_deleted=False).exists():
            raise ValidationError(
                _('لا يمكن جعل الحساب قابلاً للترحيل لأنه يحتوي على حسابات فرعية.')
            )

        # 7) منع الحلقات الدائرية
        if self.pk and self.parent:
            self._check_circular_reference()

    def _check_circular_reference(self):
        """
        يمنع الحلقات الدائرية في الشجرة.
        """
        node = self.parent
        visited = set()

        while node is not None:
            if node.pk == self.pk:
                raise ValidationError(
                    _('اختيار هذا الأب سيؤدي إلى حلقة دائرية في شجرة الحسابات.')
                )

            if node.pk in visited:
                break

            visited.add(node.pk)
            node = node.parent

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)