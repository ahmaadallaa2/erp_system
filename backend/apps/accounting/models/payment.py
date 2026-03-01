from django.db import models
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

    # رقم السند (يتولد تلقائياً، مثلاً PAY-0001)
    name = models.CharField(_("رقم السند"), max_length=50, unique=True, blank=True)
    
    partner = models.ForeignKey(
        'partners.Partner', 
        on_delete=models.RESTRICT, 
        related_name='payments', 
        verbose_name=_("الشريك (المورد/العميل)")
    )
    
    payment_type = models.CharField(_("نوع السند"), max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField(_("طريقة الدفع"), max_length=20, choices=PAYMENT_METHODS)
    
    amount = models.DecimalField(_("المبلغ"), max_digits=12, decimal_places=2)
    date = models.DateField(_("تاريخ السند"), default=timezone.now)
    
    reference = models.CharField(_("المرجع / رقم الشيك"), max_length=100, blank=True)
    notes = models.TextField(_("البيان / الملاحظات"), blank=True)
    
    # ارتباط السند بقيد اليومية اللي هيتكريت أوتوماتيك
    journal_entry = models.OneToOneField(
        'accounting.JournalEntry', 
        on_delete=models.RESTRICT, 
        null=True, 
        blank=True, 
        related_name='linked_payment',
        verbose_name=_("قيد اليومية المرتبط")
    )

    class Meta:
        verbose_name = _("سند دفع / قبض")
        verbose_name_plural = _("سندات الدفع والقبض")
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.name} - {self.partner.name} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.name:
            prefix = "REC-" if self.payment_type == 'inbound' else "PAY-"
            self.name = Sequence.next_number('payment_sequence', prefix=prefix, padding=5)
        super().save(*args, **kwargs)