from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from apps.accounting.services.reports import GeneralLedgerReportService
from apps.users.api.permissions import CanViewAccountingReports, IsCompanyMember
from apps.users.roles import has_company_wide_access
from .report_serializers import (
    GeneralLedgerFilterSerializer,
    GeneralLedgerRowSerializer,
)


class GeneralLedgerReportAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsCompanyMember,
        CanViewAccountingReports,
    ]

    @extend_schema(
        summary="General ledger report",
        description=(
            "Return company-scoped general ledger rows based on posted journal "
            "items only."
        ),
        tags=["Accounting Reports"],
        parameters=[GeneralLedgerFilterSerializer],
        responses={200: GeneralLedgerRowSerializer(many=True)},
    )
    def get(self, request):
        filter_serializer = GeneralLedgerFilterSerializer(
            data=request.query_params,
            context={"request": request},
        )
        filter_serializer.is_valid(raise_exception=True)

        rows = GeneralLedgerReportService.rows(
            company=request.user.company,
            branch=None if has_company_wide_access(request.user) else request.user.branch,
            **filter_serializer.validated_data,
        )
        response_serializer = GeneralLedgerRowSerializer(rows, many=True)
        return Response(response_serializer.data)
