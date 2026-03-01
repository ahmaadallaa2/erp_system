# apps/accounting/models/journal.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class Journal(SoftDeleteModel):
    JOURNAL_TYPES = [
        ('sale', _('مبيعات (Sales)')),
        ('purchase', _('مشتريات (Purchases)')),
        ('cash', _('نقدية (Cash)')),
        ('bank', _('بنك (Bank)')),
        ('general', _('عمليات متنوعة (General/Miscellaneous)')),
    ]

    name = models.CharField(_("اسم الدفتر"), max_length=100)
    
    # كود قصير بيظهر في رقم القيد (مثال: PUR للمشتريات، SAL للمبيعات)
    code = models.CharField(_("الكود"), max_length=10, unique=True)
    
    type = models.CharField(_("النوع"), max_length=20, choices=JOURNAL_TYPES)
    
    # الحساب الافتراضي للدفتر ده (مثلاً لو دفتر نقدية، يبقى حسابه الافتراضي هو حساب الخزنة)
    default_account = models.ForeignKey(
        'accounting.Account', 
        on_delete=models.RESTRICT, 
        null=True, 
        blank=True, 
        related_name='default_journals',
        verbose_name=_("الحساب الافتراضي")
    )

    class Meta:
        verbose_name = _("دفتر يومية")
        verbose_name_plural = _("دفاتر اليومية")

    def __str__(self):
        return f"{self.name} ({self.code})"