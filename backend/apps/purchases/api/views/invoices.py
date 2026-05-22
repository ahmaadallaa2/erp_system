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

from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.purchases.models.purchase_invoice_item import PurchaseInvoiceItem
from apps.purchases.services.purchase_service import PurchaseService
from apps.users.api.permissions import (
    CanCancelPurchaseInvoice,
    CanPostPurchaseInvoice,
    HasBranchAccess,
    IsCompanyMember,
)
from apps.users.roles import scope_queryset_to_user_branch
from ..serializers import PurchaseInvoiceSerializer, PurchaseInvoiceItemSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List purchase invoices",
        description=(
            "Retrieve purchase invoices for the authenticated user's company. "
            "Results can be filtered by invoice status, supplier, warehouse, and date range."
        ),
        tags=["Purchase Invoices"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["draft", "posted", "cancelled"],
                description="Filter purchase invoices by status.",
            ),
            OpenApiParameter(
                name="supplier",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter purchase invoices by supplier ID.",
            ),
            OpenApiParameter(
                name="warehouse",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter purchase invoices by warehouse ID.",
            ),
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter invoices with invoice date greater than or equal to this value.",
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter invoices with invoice date less than or equal to this value.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve purchase invoice",
        description="Retrieve a single purchase invoice by ID.",
        tags=["Purchase Invoices"],
    ),
    create=extend_schema(
        summary="Create purchase invoice",
        description=(
            "Create a new purchase invoice in draft status for the authenticated "
            "user's company and branch."
        ),
        tags=["Purchase Invoices"],
    ),
    update=extend_schema(
        summary="Update purchase invoice",
        description="Update an existing purchase invoice. Only draft purchase invoices can be updated.",
        tags=["Purchase Invoices"],
    ),
    partial_update=extend_schema(
        summary="Partially update purchase invoice",
        description="Partially update an existing purchase invoice. Only draft purchase invoices can be updated.",
        tags=["Purchase Invoices"],
    ),
    destroy=extend_schema(
        summary="Delete purchase invoice",
        description="Delete a draft purchase invoice only.",
        tags=["Purchase Invoices"],
    ),
)
class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsCompanyMember, HasBranchAccess]
        if self.action == "post_invoice":
            permission_classes.append(CanPostPurchaseInvoice)
        elif self.action == "cancel_invoice":
            permission_classes.append(CanCancelPurchaseInvoice)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        qs = PurchaseInvoice.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("-invoice_date", "-id")
        qs = scope_queryset_to_user_branch(qs, user, "branch_id")

        status_param = self.request.query_params.get("status")
        if status_param in ["draft", "posted", "cancelled"]:
            qs = qs.filter(status=status_param)

        supplier_id = self.request.query_params.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)

        warehouse_id = self.request.query_params.get("warehouse")
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(invoice_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(invoice_date__lte=date_to)

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
            raise ValidationError("Only draft purchase invoices can be updated.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != "draft":
            raise ValidationError("Only draft purchase invoices can be deleted.")

        instance.delete()

    @extend_schema(
        summary="Post purchase invoice",
        description=(
            "Post a draft purchase invoice using the purchase service. "
            "This may create stock transactions and update stock balances."
        ),
        tags=["Purchase Invoices"],
        responses={200: PurchaseInvoiceSerializer},
    )
    @action(detail=True, methods=["post"], url_path="post")
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()

        try:
            PurchaseService.post_invoice(invoice, user=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc))

        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancel purchase invoice",
        description=(
            "Cancel a posted purchase invoice by creating reversing stock and "
            "journal entries. Draft and already cancelled invoices are rejected."
        ),
        tags=["Purchase Invoices"],
        responses={200: PurchaseInvoiceSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_invoice(self, request, pk=None):
        invoice = self.get_object()
        reason = request.data.get("cancellation_reason", "")

        try:
            PurchaseService.cancel_invoice(invoice, user=request.user, reason=reason)
        except ValueError as exc:
            raise ValidationError(str(exc))
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)

        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List purchase invoice items",
        description=(
            "Retrieve purchase invoice items for the authenticated user's company. "
            "Results can be filtered by invoice ID."
        ),
        tags=["Purchase Invoice Items"],
        parameters=[
            OpenApiParameter(
                name="invoice",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by purchase invoice ID.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve purchase invoice item",
        description="Retrieve a single purchase invoice item by ID.",
        tags=["Purchase Invoice Items"],
    ),
    create=extend_schema(
        summary="Create purchase invoice item",
        description="Create a new item for a draft purchase invoice.",
        tags=["Purchase Invoice Items"],
    ),
    update=extend_schema(
        summary="Update purchase invoice item",
        description="Update an item belonging to a draft purchase invoice.",
        tags=["Purchase Invoice Items"],
    ),
    partial_update=extend_schema(
        summary="Partially update purchase invoice item",
        description="Partially update an item belonging to a draft purchase invoice.",
        tags=["Purchase Invoice Items"],
    ),
    destroy=extend_schema(
        summary="Delete purchase invoice item",
        description="Delete an item belonging to a draft purchase invoice.",
        tags=["Purchase Invoice Items"],
    ),
)
class PurchaseInvoiceItemViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseInvoiceItemSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [
            permission()
            for permission in [IsAuthenticated, IsCompanyMember, HasBranchAccess]
        ]

    def get_queryset(self):
        user = self.request.user

        qs = PurchaseInvoiceItem.objects.filter(
            invoice__company=user.company
        ).select_related("invoice", "product").order_by("id")
        qs = scope_queryset_to_user_branch(qs, user, "invoice__branch_id")

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
            raise ValidationError(
                "Items can only be added to draft purchase invoices."
            )

        serializer.save()

    def perform_update(self, serializer):
        item = self.get_object()

        if item.invoice.status != "draft":
            raise ValidationError(
                "Only items of draft purchase invoices can be updated."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if instance.invoice.status != "draft":
            raise ValidationError(
                "Only items of draft purchase invoices can be deleted."
            )

        instance.delete()
