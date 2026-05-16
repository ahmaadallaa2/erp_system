from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.accounting.services.payment_service import PaymentService
from .serializers import AccountLookupSerializer, PaymentSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List account lookup options",
        description=(
            "Retrieve active postable accounts for the authenticated user's company. "
            "Supports account_type filtering and simple code/name search."
        ),
        tags=["Accounts"],
        parameters=[
            OpenApiParameter(
                name="account_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["asset", "liability", "equity", "income", "expense"],
                description="Filter accounts by type.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search accounts by code or name.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve account lookup option",
        description="Retrieve one active postable account for the authenticated user's company.",
        tags=["Accounts"],
    ),
)
class AccountLookupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountLookupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = Account.objects.filter(
            is_deleted=False,
            company=user.company,
            is_active=True,
            is_postable=True,
        ).order_by("code")

        account_type = self.request.query_params.get("account_type")
        if account_type in ["asset", "liability", "equity", "income", "expense"]:
            qs = qs.filter(account_type=account_type)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

        return qs


@extend_schema_view(
    list=extend_schema(
        summary="List payments",
        description=(
            "Retrieve payments for the authenticated user's company. "
            "Results can be filtered by status, payment type, payment method, and partner."
        ),
        tags=["Payments"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["draft", "posted", "cancelled"],
                description="Filter payments by status.",
            ),
            OpenApiParameter(
                name="payment_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["inbound", "outbound"],
                description="Filter by payment type.",
            ),
            OpenApiParameter(
                name="payment_method",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["cash", "bank"],
                description="Filter by payment method.",
            ),
            OpenApiParameter(
                name="partner",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by partner ID.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve payment",
        description="Retrieve a single payment by ID.",
        tags=["Payments"],
    ),
    create=extend_schema(
        summary="Create payment",
        description=(
            "Create a draft payment for the authenticated user's company and branch."
        ),
        tags=["Payments"],
    ),
    update=extend_schema(
        summary="Update payment",
        description="Update an existing draft payment only.",
        tags=["Payments"],
    ),
    partial_update=extend_schema(
        summary="Partially update payment",
        description="Partially update an existing draft payment only.",
        tags=["Payments"],
    ),
    destroy=extend_schema(
        summary="Delete payment",
        description="Delete a draft payment only.",
        tags=["Payments"],
    ),
)
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = Payment.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("-date", "-created_at")

        status_param = self.request.query_params.get("status")
        if status_param in ["draft", "posted", "cancelled"]:
            qs = qs.filter(status=status_param)

        payment_type = self.request.query_params.get("payment_type")
        if payment_type in ["inbound", "outbound"]:
            qs = qs.filter(payment_type=payment_type)

        payment_method = self.request.query_params.get("payment_method")
        if payment_method in ["cash", "bank"]:
            qs = qs.filter(payment_method=payment_method)

        partner_id = self.request.query_params.get("partner")
        if partner_id:
            qs = qs.filter(partner_id=partner_id)

        return qs

    def perform_update(self, serializer):
        payment = self.get_object()

        if payment.status != "draft":
            raise ValidationError("Only draft payments can be updated.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != "draft":
            raise ValidationError("Only draft payments can be deleted.")

        instance.delete()

    @extend_schema(
        summary="Post payment",
        description=(
            "Post a draft payment using the payment service. "
            "This creates and links the related journal entry."
        ),
        tags=["Payments"],
        responses={200: PaymentSerializer},
    )
    @action(detail=True, methods=["post"], url_path="post")
    def post_payment(self, request, pk=None):
        payment = self.get_object()

        if payment.status != "draft":
            raise ValidationError("Only draft payments can be posted.")

        try:
            PaymentService.post_payment(payment)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc

        payment.refresh_from_db()
        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
