from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, Sequence
from apps.core.models.company import Company
from .warehouse import Warehouse


class StockTransaction(BaseModel):
    """
    رأس الحركة المخزنية.
    يمثل مستندًا مخزنيًا مثل:
    - إذن إضافة
    - إذن صرف
    - إذن تحويل
    """

    TRANSACTION_TYPES = (
        ('IN', _('إذن إضافة (وارد)')),
        ('OUT', _('إذن صرف (صادر)')),
        ('TRANSFER', _('إذن تحويل داخلي')),
    )

    STATUS_CHOICES = (
        ('draft', _('مسودة')),
        ('posted', _('مرحل')),
        ('cancelled', _('ملغي')),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        verbose_name=_("الشركة")
    )

    code = models.CharField(
        _("رقم المستند"),
        max_length=50,
        blank=True
    )

    transaction_type = models.CharField(
        _("نوع الحركة"),
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        verbose_name=_("المخزن المصدر")
    )

    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='incoming_transactions',
        verbose_name=_("المخزن الوجهة")
    )

    date = models.DateField(
        _("تاريخ الحركة"),
        default=timezone.now
    )

    status = models.CharField(
        _("الحالة"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    reference = models.CharField(
        _("رقم المرجع"),
        max_length=100,
        blank=True,
        null=True
    )

    notes = models.TextField(
        _("ملاحظات"),
        blank=True,
        null=True
    )

    journal_entry = models.OneToOneField(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transaction',
        verbose_name=_("قيد اليومية المرتبط")
    )

    posted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posted_stock_transactions",
    )

    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("حركة مخزنية")
        verbose_name_plural = _("الحركات المخزنية")
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='unique_stock_transaction_code_per_company'
            )
        ]

    def __str__(self):
        return f"{self.code or '-'} - {self.get_transaction_type_display()}"

    def clean(self):
        super().clean()

        if self.source_warehouse and self.source_warehouse.company_id != self.company_id:
            raise ValidationError(_("المخزن المصدر لا يتبع نفس الشركة."))

        if self.destination_warehouse and self.destination_warehouse.company_id != self.company_id:
            raise ValidationError(_("المخزن الوجهة لا يتبع نفس الشركة."))

        if self.transaction_type == 'TRANSFER':
            if not self.destination_warehouse:
                raise ValidationError(_("يجب تحديد المخزن الوجهة في حالة التحويل الداخلي."))
            if self.source_warehouse_id == self.destination_warehouse_id:
                raise ValidationError(_("لا يمكن التحويل إلى نفس المخزن."))
        else:
            if self.destination_warehouse:
                raise ValidationError(_("المخزن الوجهة يستخدم فقط مع التحويل الداخلي."))

    def save(self, *args, **kwargs):
        if not self.code:
            if not self.company_id:
                raise ValueError("Stock transaction must have a company before generating code.")

            if self.transaction_type == 'IN':
                prefix = 'IN-'
                seq_key = f"stock_in_comp_{self.company_id}"
            elif self.transaction_type == 'OUT':
                prefix = 'OUT-'
                seq_key = f"stock_out_comp_{self.company_id}"
            else:
                prefix = 'TRF-'
                seq_key = f"stock_transfer_comp_{self.company_id}"

            self.code = Sequence.next_number(seq_key, prefix=prefix, padding=5)

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return self.items.count()

    @property
    def can_edit(self):
        return self.status == 'draft'

    @property
    def can_post(self):
        return self.status == 'draft' and self.items.exists()

    @property
    def can_cancel(self):
        return self.status in ['draft', 'posted']
