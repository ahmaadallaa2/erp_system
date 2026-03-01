# apps/accounting/models/entry.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import SoftDeleteModel, Sequence

class JournalEntry(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', _('مسودة (Draft)')),
        ('posted', _('مُرحّل (Posted)')),
        ('cancelled', _('ملغي (Cancelled)')),
    ]

    journal = models.ForeignKey(
        'accounting.Journal', 
        on_delete=models.RESTRICT, 
        related_name='entries',
        verbose_name=_("دفتر اليومية")
    )
    
    # رقم القيد (يتم توليده تلقائياً بناءً على كود الدفتر)
    entry_number = models.CharField(_("رقم القيد"), max_length=50, unique=True, blank=True)
    
    date = models.DateField(_("تاريخ القيد"), default=timezone.now)
    
    # المرجع (Reference) - ده اللي هنربط بيه القيد بفاتورة المشتريات أو المبيعات (مثال: PINV-00001)
    reference = models.CharField(_("رقم المرجع (رقم الفاتورة)"), max_length=100, blank=True, null=True)
    
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(_("البيان / الملاحظات"), blank=True)

    class Meta:
        verbose_name = _("قيد يومية")
        verbose_name_plural = _("قيود اليومية")
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.entry_number} - {self.reference or 'بدون مرجع'}"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            # لو الدفتر كوده PUR، الرقم هيكون PUR-0001
            seq_key = f"journal_{self.journal.code}"
            self.entry_number = Sequence.next_number(seq_key, prefix=f"{self.journal.code}-", padding=4)
        super().save(*args, **kwargs)


class JournalItem(SoftDeleteModel):
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
    
    # حقل في غاية الأهمية! لو الحساب ده حساب مورد أو عميل، لازم نحدد مين هو عشان كشف الحساب بتاعه
    partner = models.ForeignKey(
        'partners.Partner', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='journal_items',
        verbose_name=_("الشريك (مورد / عميل)")
    )
    
    description = models.CharField(_("البيان"), max_length=255)
    
    debit = models.DecimalField(_("مدين (Debit)"), max_digits=12, decimal_places=2, default=0.00)
    credit = models.DecimalField(_("دائن (Credit)"), max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = _("سطر القيد")
        verbose_name_plural = _("سطور القيد")

    def __str__(self):
        return f"{self.account.name} - مدين: {self.debit} | دائن: {self.credit}"

    def clean(self):
        # قاعدة محاسبية: السطر الواحد يا مدين يا دائن، مينفعش الاتنين ومينفعش سوالب
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("لا يمكن أن تكون القيم بالسالب.")
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("السطر الواحد يجب أن يكون إما مدين أو دائن، وليس كلاهما.")