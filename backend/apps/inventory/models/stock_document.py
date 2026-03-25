# apps/inventory/models/stock_document.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .warehouse import Warehouse
from django.utils import timezone

class StockDocument(BaseModel):
    """إذن المخزن (رأس المستند) - Stock Picking/Document"""
    DOC_TYPES = (
        ('IN', _('إذن إضافة (وارد)')),
        ('OUT', _('إذن صرف (صادر)')),
        ('TRANSFER', _('إذن تحويل داخلي')),
    )

    document_type = models.CharField(max_length=10, choices=DOC_TYPES, verbose_name=_("نوع الإذن"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='documents', verbose_name=_("المخزن"))
    date = models.DateField(_("تاريخ الإذن"), default=timezone.now)
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("رقم الفاتورة/المرجع"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات"))

    # الربط المحاسبي للإذن بالكامل (قيد واحد لكل إذن)
    journal_entry = models.OneToOneField(
        'accounting.JournalEntry',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stock_document',
        verbose_name=_("قيد اليومية المرتبط")
    )

    class Meta:
        verbose_name = _("إذن مخزني")
        verbose_name_plural = _("أذونات المخازن")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.warehouse.name} ({self.date})"