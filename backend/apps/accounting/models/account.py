# apps/accounting/models/account.py

from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel


class Account(SoftDeleteModel):
    """
    نموذج دليل الحسابات (Chart of Accounts).
    يعتمد على بنية شجرية (Hierarchical Structure) لتمثيل الحسابات الرئيسية والفرعية.
    """

    # =========================================================================
    # 1. الخيارات الثابتة (Choices)
    # =========================================================================
    ACCOUNT_TYPES = [
        ('asset',     _('أصل (Asset)')),
        ('liability', _('دين / التزام (Liability)')),
        ('equity',    _('حقوق ملكية (Equity)')),
        ('income',    _('إيراد (Income/Revenue)')),
        ('expense',   _('مصروف (Expense)')),
    ]
    NORMAL_BALANCE_CHOICES = [
        ('debit',  _('مدين (Debit)')),
        ('credit', _('دائن (Credit)')),
    ]

    # الربط بين نوع الحساب وطبيعته المحاسبية الصحيحة
    NATURAL_BALANCE_MAP = {
        'asset':     'debit',
        'expense':   'debit',
        'liability': 'credit',
        'equity':    'credit',
        'income':    'credit',
    }

    # =========================================================================
    # 2. البيانات الأساسية للحساب (Core Information)
    # =========================================================================
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('كود الحساب'),
        help_text=_('كود فريد يحدد موقع الحساب في الدليل (مثال: 1120).')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('اسم الحساب')
    )

    # =========================================================================
    # 3. الهيكل الشجري والتصنيف (Tree Structure & Classification)
    # =========================================================================
    parent = models.ForeignKey(
        'self',
        on_delete=models.RESTRICT,  # نمنع حذف حساب أب لو تحته حسابات فرعية
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
        default='debit',
        verbose_name=_('طبيعة الحساب'),
        help_text=_('يحدد إذا كان الحساب بطبيعته مديناً (كالأصول) أو دائناً (كالخصوم).')
    )

    # =========================================================================
    # 4. إعدادات العمليات المحاسبية (Accounting Configuration)
    # =========================================================================
    is_leaf = models.BooleanField(
        default=True,
        verbose_name=_('قابل للترحيل (حساب فرعي)'),
        help_text=_(
            'إذا كان مفعّلاً، يمكن رمي قيود يومية عليه مباشرةً. '
            'إذا كان معطّلاً، فهو حساب تجميعي (أب) يجمع أرصدة أولاده فقط.'
        )
    )
    allow_reconciliation = models.BooleanField(
        default=False,
        verbose_name=_('يقبل التسوية (Reconciliation)'),
        help_text=_(
            'يُفعل لحسابات العملاء والموردين والبنوك لربط الفواتير بالمدفوعات (مطابقة الأرصدة).'
        )
    )

    # =========================================================================
    # 5. حالة الحساب (Status)
    # =========================================================================
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط'),
        help_text=_('تعطيل الحساب يمنع استخدامه في المعاملات الجديدة دون حذفه من النظام.')
    )

    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('دليل الحسابات')
        ordering = ['code']  # ترتيب الحسابات تصاعدياً بناءً على الكود

    def __str__(self):
        return f"{self.code} - {self.name}"

    # =========================================================================
    # 6. الخصائص المحسوبة (Properties)
    # =========================================================================
    @property
    def level(self) -> int:
        """
        يحسب عمق الحساب في الشجرة (Level).
        الجذر (بدون أب) = 0، الابن الأول = 1، وهكذا.
        مفيد جداً في تصميم التقارير وعرض الشجرة في الواجهة.
        """
        depth, node = 0, self
        while node.parent_id:
            depth += 1
            node = node.parent
        return depth

    @property
    def current_balance(self) -> Decimal:
        """
        يحسب رصيد الحساب اللحظي بناءً على القيود المُرحّلة (Posted) فقط.

        ⚠️ تحذير: استخدام هذه الخاصية على مستوى الشجرة كاملة سيُسبب N+1 Query Problem.
        للتقارير وميزان المراجعة، استخدم: Account.objects.with_balances()  (قيد التطوير)
        """
        # 1. لو الحساب "تجميعي": نجمع أرصدة كل أبنائه النشطين بشكل recursive
        if not self.is_leaf:
            return sum(
                (child.current_balance for child in self.children.filter(is_active=True)),
                Decimal('0.00')
            )

        # 2. لو الحساب "ختامي/فرعي": نجمع إجمالي المدين والدائن من سطور القيود
        totals = self.journal_items.filter(
            entry__status='posted'
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        debit  = totals.get('total_debit')  or Decimal('0.00')
        credit = totals.get('total_credit') or Decimal('0.00')

        # 3. استخراج الرصيد بناءً على طبيعة الحساب — ديناميكي 100%
        if self.normal_balance == 'debit':
            return debit - credit   # المدين يزيده والدائن ينقصه
        else:
            return credit - debit   # الدائن يزيده والمدين ينقصه

    # =========================================================================
    # 7. قواعد التحقق (Validation Rules)
    # =========================================================================
    def clean(self):
        """
        دالة التحقق المدمجة في Django. تضمن عدم حفظ أي بيانات متعارضة محاسبياً.
        """
        # 1. منع الحساب من أن يكون أباً لنفسه
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(_('خطأ: الحساب لا يمكن أن يكون أباً لنفسه.'))

        # 2. ضمان توحيد شجرة التصنيف (أصول تحت أصول، التزامات تحت التزامات)
        if self.parent and self.parent.account_type != self.account_type:
            raise ValidationError(
                _(f'خطأ محاسبي: نوع الحساب يجب أن يطابق نوع الحساب الأب '
                  f'("{self.parent.get_account_type_display()}").')
            )

        # 3. التحقق من أن طبيعة الحساب تتوافق مع نوعه المحاسبي
        expected_balance = self.NATURAL_BALANCE_MAP.get(self.account_type)
        if expected_balance and self.normal_balance != expected_balance:
            raise ValidationError(
                _(f'طبيعة الحساب يجب أن تكون '
                  f'"{dict(self.NORMAL_BALANCE_CHOICES)[expected_balance]}" '
                  f'لنوع "{self.get_account_type_display()}".')
            )

        # 4. التفرقة الصارمة بين الحساب التجميعي والفرعي
        if self.pk and self.is_leaf and self.children.exists():
            raise ValidationError(
                _('لا يمكن تحديد هذا الحساب كـ "قابل للترحيل" لأنه يحتوي على حسابات فرعية. '
                  'يجب أن يكون حساباً تجميعياً.')
            )

        # 5. منع الحلقات الدائرية (Circular Reference) في الشجرة
        if self.pk and self.parent:
            self._check_circular_reference()

    def _check_circular_reference(self):
        """
        يتتبع شجرة الآباء للأعلى للتأكد من أن الحساب الحالي ليس جزءاً من سلسلة آبائه.
        يمنع حدوث Infinite Loop في قواعد البيانات.
        """
        node, visited = self.parent, set()
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError(
                    _('اختيار هذا الأب سيُنشئ حلقة دائرية (Circular Reference) في الشجرة.')
                )
            if node.pk in visited:
                break  # حماية إضافية لو الداتابيز فيها حلقة قديمة بالفعل
            visited.add(node.pk)
            node = node.parent