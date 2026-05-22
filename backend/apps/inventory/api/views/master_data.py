from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.inventory.models.product import Product
from apps.inventory.models.unit import Unit
from apps.inventory.models.warehouse import Warehouse
from apps.users.api.permissions import IsCompanyMember
from ..serializers import ProductSerializer, UnitSerializer, WarehouseSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List units",
        description="Retrieve units.",
        tags=["Inventory - Master Data"],
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search by unit name.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve unit",
        description="Retrieve a single unit by ID.",
        tags=["Inventory - Master Data"],
    ),
    create=extend_schema(
        summary="Create unit",
        description="Create a new unit.",
        tags=["Inventory - Master Data"],
    ),
    update=extend_schema(
        summary="Update unit",
        description="Update an existing unit.",
        tags=["Inventory - Master Data"],
    ),
    partial_update=extend_schema(
        summary="Partially update unit",
        description="Partially update an existing unit.",
        tags=["Inventory - Master Data"],
    ),
    destroy=extend_schema(
        summary="Delete unit",
        description="Delete an existing unit.",
        tags=["Inventory - Master Data"],
    ),
)
class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Unit.objects.filter(is_deleted=False).order_by("name")

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Retrieve products for the authenticated user's company.",
        tags=["Inventory - Master Data"],
        parameters=[
            OpenApiParameter(
                name="product_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["storable", "service", "consumable"],
                description="Filter by product type.",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by category ID.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search by product name.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve product",
        description="Retrieve a single product by ID.",
        tags=["Inventory - Master Data"],
    ),
    create=extend_schema(
        summary="Create product",
        description="Create a new product for the authenticated user's company.",
        tags=["Inventory - Master Data"],
    ),
    update=extend_schema(
        summary="Update product",
        description="Update an existing product.",
        tags=["Inventory - Master Data"],
    ),
    partial_update=extend_schema(
        summary="Partially update product",
        description="Partially update an existing product.",
        tags=["Inventory - Master Data"],
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Delete an existing product.",
        tags=["Inventory - Master Data"],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [permission() for permission in [IsAuthenticated, IsCompanyMember]]

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


@extend_schema_view(
    list=extend_schema(
        summary="List warehouses",
        description="Retrieve warehouses for the authenticated user's company.",
        tags=["Inventory - Master Data"],
        parameters=[
            OpenApiParameter(
                name="branch",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter by branch ID.",
            ),
            OpenApiParameter(
                name="warehouse_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["main", "sub"],
                description="Filter by warehouse type.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search by warehouse name.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve warehouse",
        description="Retrieve a single warehouse by ID.",
        tags=["Inventory - Master Data"],
    ),
    create=extend_schema(
        summary="Create warehouse",
        description="Create a new warehouse for the authenticated user's company.",
        tags=["Inventory - Master Data"],
    ),
    update=extend_schema(
        summary="Update warehouse",
        description="Update an existing warehouse.",
        tags=["Inventory - Master Data"],
    ),
    partial_update=extend_schema(
        summary="Partially update warehouse",
        description="Partially update an existing warehouse.",
        tags=["Inventory - Master Data"],
    ),
    destroy=extend_schema(
        summary="Delete warehouse",
        description="Delete an existing warehouse.",
        tags=["Inventory - Master Data"],
    ),
)
class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [permission() for permission in [IsAuthenticated, IsCompanyMember]]

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
            raise ValidationError(
                {"branch": "Selected branch does not belong to the user's company."}
            )

        serializer.save(
            company=user.company,
            branch=branch,
        )
