from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .report_views import GeneralLedgerReportAPIView
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
    path("", include(router.urls)),
]
