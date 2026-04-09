from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SalesInvoiceViewSet, SalesInvoiceItemViewSet

router = DefaultRouter()
router.register("invoices", SalesInvoiceViewSet, basename="sales-invoices")
router.register("invoice-items", SalesInvoiceItemViewSet, basename="sales-invoice-items")

urlpatterns = [
    path("", include(router.urls)),
]