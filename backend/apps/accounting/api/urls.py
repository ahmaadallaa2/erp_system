from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .report_views import (
    BalanceSheetReportAPIView,
    GeneralLedgerReportAPIView,
    IncomeStatementReportAPIView,
    TrialBalanceReportAPIView,
)
from .views import AccountLookupViewSet, JournalEntryViewSet, PaymentViewSet

router = DefaultRouter()
router.register("accounts", AccountLookupViewSet, basename="accounts")
router.register("journal-entries", JournalEntryViewSet, basename="journal-entries")
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path(
        "reports/general-ledger/",
        GeneralLedgerReportAPIView.as_view(),
        name="general-ledger-report",
    ),
    path(
        "reports/trial-balance/",
        TrialBalanceReportAPIView.as_view(),
        name="trial-balance-report",
    ),
    path(
        "reports/income-statement/",
        IncomeStatementReportAPIView.as_view(),
        name="income-statement-report",
    ),
    path(
        "reports/balance-sheet/",
        BalanceSheetReportAPIView.as_view(),
        name="balance-sheet-report",
    ),
    path("", include(router.urls)),
]
