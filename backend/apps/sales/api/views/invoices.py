from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.sales.models import SalesInvoice, SalesInvoiceItem
from apps.sales.services.sales_service import SalesService
from ..serializers import SalesInvoiceSerializer, SalesInvoiceItemSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List sales invoices",
        description=(
            "Retrieve sales invoices for the authenticated user's company. "
            "Results can be filtered by invoice status, customer, and date range."
        ),
        tags=["Sales Invoices"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["draft", "posted", "cancelled"],
                description="Filter invoices by status.",
            ),
            OpenApiParameter(
                name="customer",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter invoices by customer ID.",
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter invoices with date greater than or equal to this value.",
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter invoices with date less than or equal to this value.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve sales invoice",
        description="Retrieve a single sales invoice by ID.",
        tags=["Sales Invoices"],
    ),
    create=extend_schema(
        summary="Create sales invoice",
        description=(
            "Create a new sales invoice in draft status for the authenticated "
            "user's company and branch."
        ),
        tags=["Sales Invoices"],
    ),
    update=extend_schema(
        summary="Update sales invoice",
        description="Update an existing sales invoice. Only draft invoices can be updated.",
        tags=["Sales Invoices"],
    ),
    partial_update=extend_schema(
        summary="Partially update sales invoice",
        description="Partially update an existing sales invoice. Only draft invoices can be updated.",
        tags=["Sales Invoices"],
    ),
    destroy=extend_schema(
        summary="Delete sales invoice",
        description="Delete a draft sales invoice only.",
        tags=["Sales Invoices"],
    ),
)
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

    def perform_destroy(self, instance):
        if instance.status != "draft":
            raise ValidationError("Only draft invoices can be deleted.")

        instance.delete()

    @extend_schema(
        summary="Post sales invoice",
        description=(
            "Post a draft sales invoice using the sales service. "
            "Stock movements may be created for stock items."
        ),
        tags=["Sales Invoices"],
        responses={200: SalesInvoiceSerializer},
    )
    @action(detail=True, methods=["post"], url_path="post")
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()

        try:
            SalesService.post_invoice(invoice)
        except ValueError as exc:
            raise ValidationError(str(exc))

        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancel sales invoice",
        description=(
            "Cancel a posted sales invoice by creating reversing stock and "
            "journal entries. Draft and already cancelled invoices are rejected."
        ),
        tags=["Sales Invoices"],
        responses={200: SalesInvoiceSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_invoice(self, request, pk=None):
        invoice = self.get_object()

        try:
            SalesService.cancel_invoice(invoice)
        except ValueError as exc:
            raise ValidationError(str(exc))
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)

        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List sales invoice items",
        description=(
            "Retrieve sales invoice items for the authenticated user's company. "
            "Results can be filtered by invoice ID."
        ),
        tags=["Sales Invoice Items"],
        parameters=[
            OpenApiParameter(
                name="invoice",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by sales invoice ID.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve sales invoice item",
        description="Retrieve a single sales invoice item by ID.",
        tags=["Sales Invoice Items"],
    ),
    create=extend_schema(
        summary="Create sales invoice item",
        description="Create a new item for a draft sales invoice.",
        tags=["Sales Invoice Items"],
    ),
    update=extend_schema(
        summary="Update sales invoice item",
        description="Update an item belonging to a draft sales invoice.",
        tags=["Sales Invoice Items"],
    ),
    partial_update=extend_schema(
        summary="Partially update sales invoice item",
        description="Partially update an item belonging to a draft sales invoice.",
        tags=["Sales Invoice Items"],
    ),
    destroy=extend_schema(
        summary="Delete sales invoice item",
        description="Delete an item belonging to a draft sales invoice.",
        tags=["Sales Invoice Items"],
    ),
)
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
        user = self.request.user
        invoice = serializer.validated_data["invoice"]

        if invoice.company_id != user.company_id:
            raise ValidationError(
                "You cannot add items to an invoice outside your company."
            )

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
