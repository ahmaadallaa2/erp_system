from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel

from .payment import Payment


class PaymentAllocation(SoftDeleteModel):
    """
    الجزء من سند القبض/الصرف المخصص لسداد فاتورة مبيعات أو مشتريات محددة.
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="allocations",
        verbose_name=_("السند"),
    )

    invoice_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        limit_choices_to=(
            Q(app_label="sales", model="salesinvoice")
            | Q(app_label="purchases", model="purchaseinvoice")
        ),
        verbose_name=_("نوع الفاتورة"),
    )
    invoice_object_id = models.UUIDField(_("معرّف الفاتورة"))
    invoice = GenericForeignKey("invoice_content_type", "invoice_object_id")

    amount = models.DecimalField(
        _("المبلغ المخصص"),
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        verbose_name = _("تخصيص سند")
        verbose_name_plural = _("تخصيصات السندات")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invoice_content_type", "invoice_object_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_allocation_amount_positive",
            ),
        ]

    def __str__(self):
        voucher = self.payment.voucher_number if self.payment_id else "-"
        return f"{voucher} -> {self.invoice_object_id}: {self.amount}"

    def clean(self):
        super().clean()

        if self.amount is not None and self.amount <= Decimal("0.00"):
            raise ValidationError(_("يجب أن يكون المبلغ المخصص أكبر من الصفر."))
