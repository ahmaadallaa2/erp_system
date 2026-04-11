from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PurchaseInvoiceViewSet, PurchaseInvoiceItemViewSet

router = DefaultRouter()
router.register("invoices", PurchaseInvoiceViewSet, basename="purchase-invoices")
router.register("invoice-items", PurchaseInvoiceItemViewSet, basename="purchase-invoice-items")

urlpatterns = [
    path("", include(router.urls)),
]