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

from apps.inventory.models import StockTransaction, StockMovement
from apps.inventory.services.stock_service import StockService
from ..serializers import StockTransactionSerializer, StockMovementSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List stock transactions",
        description="Retrieve stock transactions for the authenticated user's company.",
        tags=["Inventory - Transactions"],
        parameters=[
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["IN", "OUT", "TRANSFER"],
                description="Filter by transaction type.",
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["draft", "posted", "cancelled"],
                description="Filter by transaction status.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve stock transaction",
        description="Retrieve a single stock transaction by ID.",
        tags=["Inventory - Transactions"],
    ),
    create=extend_schema(
        summary="Create stock transaction",
        description="Create a new stock transaction in draft status.",
        tags=["Inventory - Transactions"],
    ),
    update=extend_schema(
        summary="Update stock transaction",
        description="Update a draft stock transaction only.",
        tags=["Inventory - Transactions"],
    ),
    partial_update=extend_schema(
        summary="Partially update stock transaction",
        description="Partially update a draft stock transaction only.",
        tags=["Inventory - Transactions"],
    ),
    destroy=extend_schema(
        summary="Delete stock transaction",
        description="Delete a draft stock transaction only.",
        tags=["Inventory - Transactions"],
    ),
)
class StockTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = StockTransaction.objects.filter(
            company=user.company,
        ).order_by("-date", "-created_at")

        tx_type = self.request.query_params.get("type")
        if tx_type:
            qs = qs.filter(transaction_type=tx_type)

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("User has no company.")

        serializer.save(company=user.company)

    def perform_update(self, serializer):
        obj = self.get_object()

        if obj.status != "draft":
            raise ValidationError("Only draft transactions can be updated.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != "draft":
            raise ValidationError("Only draft transactions can be deleted.")

        instance.delete()

    @extend_schema(
        summary="Post stock transaction",
        description="Post a draft stock transaction using the stock service and update stock balances.",
        tags=["Inventory - Transactions"],
        responses={200: StockTransactionSerializer},
    )
    @action(detail=True, methods=["post"], url_path="post")
    def post_transaction(self, request, pk=None):
        tx = self.get_object()

        try:
            StockService.post_transaction(tx)
        except ValueError as exc:
            raise ValidationError(str(exc))

        tx.refresh_from_db()
        serializer = self.get_serializer(tx)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List stock movements",
        description="Retrieve stock movement lines for the authenticated user's company.",
        tags=["Inventory - Transactions"],
        parameters=[
            OpenApiParameter(
                name="transaction",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by stock transaction ID.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve stock movement",
        description="Retrieve a single stock movement by ID.",
        tags=["Inventory - Transactions"],
    ),
    create=extend_schema(
        summary="Create stock movement",
        description="Create a stock movement line for a draft stock transaction.",
        tags=["Inventory - Transactions"],
    ),
    update=extend_schema(
        summary="Update stock movement",
        description="Update a stock movement line belonging to a draft stock transaction.",
        tags=["Inventory - Transactions"],
    ),
    partial_update=extend_schema(
        summary="Partially update stock movement",
        description="Partially update a stock movement line belonging to a draft stock transaction.",
        tags=["Inventory - Transactions"],
    ),
    destroy=extend_schema(
        summary="Delete stock movement",
        description="Delete a stock movement line belonging to a draft stock transaction.",
        tags=["Inventory - Transactions"],
    ),
)
class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = StockMovement.objects.filter(
            transaction__company=user.company
        ).select_related("transaction", "product")

        tx_id = self.request.query_params.get("transaction")
        if tx_id:
            qs = qs.filter(transaction_id=tx_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        tx = serializer.validated_data["transaction"]
        product = serializer.validated_data["product"]

        if tx.company_id != user.company_id:
            raise ValidationError(
                "Cannot add items to a stock transaction outside your company."
            )

        if product.company_id != user.company_id:
            raise ValidationError(
                "Cannot add a product outside your company."
            )

        if tx.status != "draft":
            raise ValidationError("Cannot add items to a non-draft transaction.")

        serializer.save()

    def perform_update(self, serializer):
        obj = self.get_object()

        if obj.transaction.status != "draft":
            raise ValidationError("Cannot update items after posting.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.transaction.status != "draft":
            raise ValidationError("Cannot delete items after posting.")

        instance.delete()
