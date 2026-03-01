from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel
from django.db.models import Sum

class Account(SoftDeleteModel):
    ACCOUNT_TYPES = [
        ('asset', _('أصل (Asset)')),
        ('liability', _('دين / التزام (Liability)')),
        ('equity', _('حقوق ملكية (Equity)')),
        ('income', _('إيراد (Income/Revenue)')),
        ('expense', _('مصروف (Expense)')),
    ]
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('كود الحساب')
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('اسم الحساب')
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        verbose_name=_('نوع الحساب')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('الحساب الأب')
    )

    allow_reconciliation = models.BooleanField(
        _("يقبل التسوية (Reconciliation)"), 
        default=False,
        help_text=_("يُفعل لحسابات المديونيات (العملاء والموردين) لربط الفواتير بالمدفوعات.")
    )
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("يُستخدم لتعطيل الحسابات دون حذفها، مما يمنع استخدامها في المعاملات الجديدة.")
    )
    class Meta:
        verbose_name = _('حساب')
        verbose_name_plural = _('الحسابات')
        ordering = ['code']
    def __str__(self):
        return f"{self.code} - {self.name}"
    @property
    def current_balance(self):
        """
        حساب الرصيد الفعلي للحساب بناءً على القيود المُرحلة (Posted) فقط،
        وطبقاً لطبيعة الحساب (مدين أو دائن).
        """
        # 1. تجميع إجمالي المدين والدائن من القيود المُرحلة فقط
        totals = self.journal_items.filter(
            entry__status='posted'
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        total_debit = totals.get('total_debit') 
        total_credit = totals.get('total_credit') 
        # الأصول والمصروفات (طبيعتها مدينة)
        if self.account_type in ['asset', 'expense']:
            return total_debit - total_credit
        
        # الخصوم، حقوق الملكية، والإيرادات (طبيعتها دائنة)
        elif self.account_type in ['liability', 'equity', 'income']:
            return total_credit - total_debit
            
        return 0.00