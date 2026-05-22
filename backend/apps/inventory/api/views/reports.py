from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from apps.inventory.services.reports import (
    ProductMovementHistoryReportService,
    WarehouseBalanceReportService,
)
from apps.users.api.permissions import IsCompanyMember
from apps.users.roles import has_company_wide_access
from ..serializers.reports import (
    ProductMovementHistoryFilterSerializer,
    ProductMovementHistoryRowSerializer,
    WarehouseBalanceFilterSerializer,
    WarehouseBalanceRowSerializer,
)


class ProductMovementHistoryReportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    @extend_schema(
        summary="Product movement history report",
        description=(
            "Return company-scoped stock movement history based on posted stock "
            "transactions only."
        ),
        tags=["Inventory - Reports"],
        parameters=[ProductMovementHistoryFilterSerializer],
        responses={200: ProductMovementHistoryRowSerializer(many=True)},
    )
    def get(self, request):
        filter_serializer = ProductMovementHistoryFilterSerializer(
            data=request.query_params,
            context={"request": request},
        )
        filter_serializer.is_valid(raise_exception=True)

        rows = ProductMovementHistoryReportService.rows(
            company=request.user.company,
            branch=None if has_company_wide_access(request.user) else request.user.branch,
            **filter_serializer.validated_data,
        )
        response_serializer = ProductMovementHistoryRowSerializer(rows, many=True)
        return Response(response_serializer.data)


class WarehouseBalanceReportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    @extend_schema(
        summary="Warehouse balance report",
        description=(
            "Return company-scoped current product balances per warehouse using "
            "existing stock balance data."
        ),
        tags=["Inventory - Reports"],
        parameters=[WarehouseBalanceFilterSerializer],
        responses={200: WarehouseBalanceRowSerializer(many=True)},
    )
    def get(self, request):
        filter_serializer = WarehouseBalanceFilterSerializer(
            data=request.query_params,
            context={"request": request},
        )
        filter_serializer.is_valid(raise_exception=True)

        rows = WarehouseBalanceReportService.rows(
            company=request.user.company,
            branch=None if has_company_wide_access(request.user) else request.user.branch,
            **filter_serializer.validated_data,
        )
        response_serializer = WarehouseBalanceRowSerializer(rows, many=True)
        return Response(response_serializer.data)
