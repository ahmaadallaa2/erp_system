from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounting.models import Payment, PaymentAllocation

ZERO = Decimal("0.00")

# invoice_type -> invoice model, its partner field, and the payment type that settles it
INVOICE_TYPES = {
    "sales": {
        "model": "sales.SalesInvoice",
        "partner_field": "customer_id",
        "payment_type": "inbound",
    },
    "purchase": {
        "model": "purchases.PurchaseInvoice",
        "partner_field": "supplier_id",
        "payment_type": "outbound",
    },
}

INVOICE_TYPE_BY_MODEL = {
    config["model"].split(".")[1].lower(): invoice_type
    for invoice_type, config in INVOICE_TYPES.items()
}


class PaymentAllocationService:
    @staticmethod
    @transaction.atomic
    def allocate_payment(payment_id, invoice_id, invoice_type, amount, *, company=None, branch=None):
        """
        Allocate part of a posted payment to a posted invoice of the same
        company and partner. `company` and `branch` restrict which payment and
        invoice may be used (pass the requesting user's scope).
        """
        config = INVOICE_TYPES.get(invoice_type)
        if config is None:
            raise ValidationError({"invoice_type": "Invoice type must be 'sales' or 'purchase'."})

        amount = PaymentAllocationService._parse_amount(amount)

        # Lock payment before invoice; release_for_payment uses the same order.
        payments = Payment.objects.select_for_update()
        if company is not None:
            payments = payments.filter(company=company)
        try:
            payment = payments.get(pk=payment_id)
        except (Payment.DoesNotExist, ValidationError):
            raise ValidationError({"payment": "Payment not found."})

        invoice_model = apps.get_model(config["model"])
        invoices = invoice_model.objects.select_for_update()
        if company is not None:
            invoices = invoices.filter(company=company)
        if branch is not None:
            invoices = invoices.filter(branch=branch)
        try:
            invoice = invoices.get(pk=invoice_id)
        except (invoice_model.DoesNotExist, ValidationError):
            raise ValidationError({"invoice_id": "Invoice not found."})

        if payment.status != "posted":
            raise ValidationError("Only posted payments can be allocated.")

        if invoice.status != "posted":
            raise ValidationError("Payments can only be allocated to posted invoices.")

        if payment.company_id != invoice.company_id:
            raise ValidationError("Payment and invoice must belong to the same company.")

        if payment.partner_id != getattr(invoice, config["partner_field"]):
            raise ValidationError("Payment and invoice must belong to the same partner.")

        if payment.payment_type != config["payment_type"]:
            raise ValidationError(
                "Sales invoices can only be settled by inbound payments, and "
                "purchase invoices by outbound payments."
            )

        unallocated = payment.unallocated_amount
        if amount > unallocated:
            raise ValidationError(
                {"amount": f"Amount exceeds the payment's unallocated balance ({unallocated})."}
            )

        if amount > invoice.amount_due:
            raise ValidationError(
                {"amount": f"Amount exceeds the invoice's outstanding balance ({invoice.amount_due})."}
            )

        allocation = PaymentAllocation.objects.create(
            payment=payment,
            invoice_content_type=ContentType.objects.get_for_model(invoice_model),
            invoice_object_id=invoice.pk,
            amount=amount,
        )

        invoice.amount_paid += amount
        invoice.save(update_fields=["amount_paid", "updated_at"])

        return allocation

    @staticmethod
    def invoice_type_for(allocation):
        return INVOICE_TYPE_BY_MODEL[allocation.invoice_content_type.model]

    @staticmethod
    def release_for_payment(payment):
        """Undo every allocation of a payment, e.g. when it is cancelled."""
        for allocation in payment.allocations.select_related("invoice_content_type"):
            invoice_model = allocation.invoice_content_type.model_class()
            invoice = invoice_model.objects.select_for_update().get(pk=allocation.invoice_object_id)
            invoice.amount_paid -= allocation.amount
            invoice.save(update_fields=["amount_paid", "updated_at"])
            allocation.soft_delete()

    @staticmethod
    def release_for_invoice(invoice):
        """Undo every allocation to an invoice, e.g. when it is cancelled."""
        locked = type(invoice).objects.select_for_update().get(pk=invoice.pk)
        allocations = list(locked.allocations.all())
        if not allocations:
            return

        locked.amount_paid -= sum((allocation.amount for allocation in allocations), ZERO)
        locked.save(update_fields=["amount_paid", "updated_at"])
        invoice.amount_paid = locked.amount_paid
        for allocation in allocations:
            allocation.soft_delete()

    @staticmethod
    def _parse_amount(amount):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise ValidationError({"amount": "Amount must be a number."})

        if not amount.is_finite() or amount <= ZERO:
            raise ValidationError({"amount": "Amount must be greater than zero."})

        if amount != amount.quantize(Decimal("0.01")):
            raise ValidationError({"amount": "Amount cannot have more than 2 decimal places."})

        return amount
