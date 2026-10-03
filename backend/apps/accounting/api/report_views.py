from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from apps.accounting.services.reports import (
    FinancialReportService,
    GeneralLedgerReportService,
)
from apps.users.api.permissions import CanViewAccountingReports, IsCompanyMember
from apps.users.roles import has_company_wide_access
from .report_serializers import (
    BalanceSheetSerializer,
    GeneralLedgerFilterSerializer,
    GeneralLedgerRowSerializer,
    IncomeStatementSerializer,
    ReportDateRangeFilterSerializer,
    TrialBalanceSerializer,
)


def report_branch(user):
    """Branch to restrict report data to, or None for company-wide users."""
    if has_company_wide_access(user):
        return None
    if not user.branch_id:
        raise PermissionDenied("A branch must be assigned to view branch-scoped reports.")
    return user.branch


class AccountingReportAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsCompanyMember,
        CanViewAccountingReports,
    ]


class GeneralLedgerReportAPIView(AccountingReportAPIView):
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
            branch=report_branch(request.user),
            **filter_serializer.validated_data,
        )
        response_serializer = GeneralLedgerRowSerializer(rows, many=True)
        return Response(response_serializer.data)


class FinancialReportAPIView(AccountingReportAPIView):
    report_name = None
    response_serializer_class = None

    def get(self, request):
        filter_serializer = ReportDateRangeFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        build_report = getattr(FinancialReportService, self.report_name)
        report = build_report(
            company=request.user.company,
            branch=report_branch(request.user),
            **filter_serializer.validated_data,
        )
        return Response(self.response_serializer_class(report).data)


class TrialBalanceReportAPIView(FinancialReportAPIView):
    report_name = "trial_balance"
    response_serializer_class = TrialBalanceSerializer

    @extend_schema(
        summary="Trial balance",
        description=(
            "Debit and credit totals per account for posted journal items in "
            "the date range, grouped by account type."
        ),
        tags=["Accounting Reports"],
        parameters=[ReportDateRangeFilterSerializer],
        responses={200: TrialBalanceSerializer},
    )
    def get(self, request):
        return super().get(request)


class IncomeStatementReportAPIView(FinancialReportAPIView):
    report_name = "income_statement"
    response_serializer_class = IncomeStatementSerializer

    @extend_schema(
        summary="Income statement",
        description=(
            "Income and expense account balances for the date range and the "
            "resulting net profit (negative for a loss)."
        ),
        tags=["Accounting Reports"],
        parameters=[ReportDateRangeFilterSerializer],
        responses={200: IncomeStatementSerializer},
    )
    def get(self, request):
        return super().get(request)


class BalanceSheetReportAPIView(FinancialReportAPIView):
    report_name = "balance_sheet"
    response_serializer_class = BalanceSheetSerializer

    @extend_schema(
        summary="Balance sheet",
        description=(
            "Asset, liability and equity balances as of end_date. Equity "
            "includes retained earnings (profit before start_date) and net "
            "profit for the period, so assets equal liabilities plus equity."
        ),
        tags=["Accounting Reports"],
        parameters=[ReportDateRangeFilterSerializer],
        responses={200: BalanceSheetSerializer},
    )
    def get(self, request):
        return super().get(request)
