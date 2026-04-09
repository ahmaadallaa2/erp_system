from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from apps.inventory.models.product import Product
from apps.inventory.models.unit import Unit
from apps.inventory.models.warehouse import Warehouse
from .serializers import ProductSerializer, UnitSerializer, WarehouseSerializer


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Unit.objects.filter(is_deleted=False).order_by("name")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = Product.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("name")

        product_type = self.request.query_params.get("product_type")
        if product_type in ["storable", "service", "consumable"]:
            qs = qs.filter(product_type=product_type)

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        serializer.save(company=user.company)


class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = Warehouse.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("branch__name", "name")

        branch_id = self.request.query_params.get("branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        warehouse_type = self.request.query_params.get("warehouse_type")
        if warehouse_type in ["main", "sub"]:
            qs = qs.filter(warehouse_type=warehouse_type)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        branch = serializer.validated_data.get("branch") or user.branch

        if not branch:
            raise ValidationError({"branch": "Branch is required."})

        if branch.company_id != user.company_id:
            raise ValidationError({"branch": "Selected branch does not belong to the user's company."})

        serializer.save(
            company=user.company,
            branch=branch,
        )