from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, UnitViewSet, WarehouseViewSet

router = DefaultRouter()
router.register("units", UnitViewSet, basename="units")
router.register("products", ProductViewSet, basename="products")
router.register("warehouses", WarehouseViewSet, basename="warehouses")

urlpatterns = [
    path("", include(router.urls)),
]