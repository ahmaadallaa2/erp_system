from django.urls import path

from .dashboard import DashboardSummaryAPIView

urlpatterns = [
    path(
        "dashboard/summary/",
        DashboardSummaryAPIView.as_view(),
        name="dashboard-summary",
    ),
]
