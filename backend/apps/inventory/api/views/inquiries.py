from django.db.models import F
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.inventory.models.stock_balance import StockBalance
from apps.users.api.permissions import HasBranchAccess, IsCompanyMember
from apps.users.roles import scope_queryset_to_user_branch
from ..serializers import StockBalanceSerializer


@extend_schema(tags=["Inventory - Reports"])
class StockBalanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [
            permission()
            for permission in [IsAuthenticated, IsCompanyMember, HasBranchAccess]
        ]

    @extend_schema(
        summary="List stock balances",
        description="Get current stock balances per product per warehouse.",
        parameters=[
            OpenApiParameter(
                name="product",
                description="Filter by product ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="warehouse",
                description="Filter by warehouse ID.",
                required=False,
                type=OpenApiTypes.UUID,
            ),
            OpenApiParameter(
                name="search",
                description="Search by product name.",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="low_stock",
                description="Filter low stock items.",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve stock balance",
        description="Get stock balance details by ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        qs = StockBalance.objects.filter(
            company=user.company,
        ).select_related("product", "warehouse").order_by(
            "warehouse__name", "product__name"
        )
        qs = scope_queryset_to_user_branch(qs, user, "warehouse__branch_id")

        product_id = self.request.query_params.get("product")
        if product_id:
            qs = qs.filter(product_id=product_id)

        warehouse_id = self.request.query_params.get("warehouse")
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)

        low_stock = self.request.query_params.get("low_stock")
        if low_stock in ["1", "true", "True"]:
            qs = qs.filter(quantity__lte=F("reorder_point"))

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(product__name__icontains=search)

        return qs
