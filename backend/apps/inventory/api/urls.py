from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    UnitViewSet,
    WarehouseViewSet,
    StockTransactionViewSet,
    StockMovementViewSet,
    StockBalanceViewSet,
)

router = DefaultRouter()
router.register("units", UnitViewSet, basename="units")
router.register("products", ProductViewSet, basename="products")
router.register("warehouses", WarehouseViewSet, basename="warehouses")
router.register("stock-transactions", StockTransactionViewSet, basename="stock-transactions")
router.register("stock-movements", StockMovementViewSet, basename="stock-movements")
router.register("stock-balances", StockBalanceViewSet, basename="stock-balances")

urlpatterns = [
    path("", include(router.urls)),
]