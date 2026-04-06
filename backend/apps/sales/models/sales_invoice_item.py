from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class SalesInvoiceItem(BaseModel):
    """
    سطور فاتورة المبيعات.
    """

    invoice = models.ForeignKey(
        'sales.SalesInvoice',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("الفاتورة")
    )

    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.RESTRICT,
        related_name='sales_invoice_items',
        verbose_name=_("المنتج")
    )

    quantity = models.DecimalField(
        _("الكمية"),
        max_digits=10,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        _("سعر الوحدة"),
        max_digits=10,
        decimal_places=2
    )

    line_total = models.DecimalField(
        _("إجمالي السطر"),
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00")
    )

    notes = models.TextField(
        _("ملاحظات"),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("عنصر فاتورة مبيعات")
        verbose_name_plural = _("عناصر فواتير المبيعات")
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name if self.product else 'بدون منتج'} - {self.quantity}"

    def clean(self):
        super().clean()

        if self.quantity is None or self.quantity <= 0:
            raise ValidationError(_("يجب أن تكون الكمية أكبر من الصفر."))

        if self.unit_price is None or self.unit_price < 0:
            raise ValidationError(_("لا يمكن أن يكون سعر الوحدة سالبًا."))

        if self.product_id and self.invoice_id:
            if self.product.company_id != self.invoice.company_id:
                raise ValidationError(_("المنتج لا يتبع نفس شركة الفاتورة."))

        if not self._state.adding and self.invoice.status == 'posted':
            raise ValidationError(_("لا يمكن تعديل سطور فاتورة المبيعات بعد ترحيلها."))

    def save(self, *args, **kwargs):
        raw_total = (self.quantity or Decimal("0.00")) * (self.unit_price or Decimal("0.00"))
        self.line_total = raw_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        self.full_clean()
        super().save(*args, **kwargs)
        self.update_invoice_total()

    def delete(self, *args, **kwargs):
        if self.invoice.status == 'posted':
            raise ValidationError(_("لا يمكن حذف سطور فاتورة المبيعات بعد ترحيلها."))

        invoice_reference = self.invoice
        super().delete(*args, **kwargs)
        self._recalculate_invoice_total(invoice_reference)

    def update_invoice_total(self):
        self._recalculate_invoice_total(self.invoice)

    @staticmethod
    def _recalculate_invoice_total(invoice):
        total = invoice.items.aggregate(total=Sum('line_total')).get('total') or Decimal("0.00")
        invoice.total_amount = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        invoice.save(update_fields=['total_amount', 'updated_at'])