from rest_framework import serializers
from apps.inventory.models.product import Product
from apps.inventory.models.unit import Unit
from apps.inventory.models.warehouse import Warehouse


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "company",
            "category",
            "unit",
            "name",
            "sku",
            "barcode",
            "product_type",
            "image",
            "description",
            "cost_price",
            "average_cost",
            "sale_price",
            "reorder_point",
            "income_account",
            "expense_account",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "sku",
            "created_at",
            "updated_at",
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            "id",
            "company",
            "name",
            "code",
            "warehouse_type",
            "branch",
            "keeper",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "code",
            "created_at",
            "updated_at",
        ]