from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.sales.models import SalesInvoice, SalesInvoiceItem
from .serializers import SalesInvoiceSerializer, SalesInvoiceItemSerializer


class SalesInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = SalesInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = SalesInvoice.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("-date", "-created_at")

        status_param = self.request.query_params.get("status")
        if status_param in ["draft", "posted", "cancelled"]:
            qs = qs.filter(status=status_param)

        customer_id = self.request.query_params.get("customer")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        if not user.branch:
            raise ValidationError("Authenticated user is not assigned to a branch.")

        serializer.save(
            company=user.company,
            branch=user.branch,
        )

    def perform_update(self, serializer):
        invoice = self.get_object()

        if invoice.status != "draft":
            raise ValidationError("Only draft invoices can be updated.")

        serializer.save()

    @action(detail=True, methods=["post"], url_path="post")
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()

        if invoice.status != "draft":
            return Response(
                {"detail": "Only draft invoices can be posted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not invoice.items.exists():
            return Response(
                {"detail": "Invoice must have at least one item before posting."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invoice.total_amount <= 0:
            return Response(
                {"detail": "Invoice total must be greater than zero before posting."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = "posted"
        invoice.save(update_fields=["status", "updated_at"])

        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SalesInvoiceItemViewSet(viewsets.ModelViewSet):
    serializer_class = SalesInvoiceItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = SalesInvoiceItem.objects.filter(
            invoice__company=user.company
        ).select_related("invoice", "product").order_by("id")

        invoice_id = self.request.query_params.get("invoice")
        if invoice_id:
            qs = qs.filter(invoice_id=invoice_id)

        return qs

    def perform_create(self, serializer):
        invoice = serializer.validated_data["invoice"]

        if invoice.status != "draft":
            raise ValidationError("Items can only be added to draft invoices.")

        serializer.save()

    def perform_update(self, serializer):
        item = self.get_object()

        if item.invoice.status != "draft":
            raise ValidationError("Only items of draft invoices can be updated.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.invoice.status != "draft":
            raise ValidationError("Only items of draft invoices can be deleted.")

        instance.delete()