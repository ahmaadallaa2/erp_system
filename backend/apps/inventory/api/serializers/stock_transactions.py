from rest_framework import serializers

from apps.inventory.models.stock_movement import StockMovement
from apps.inventory.models.stock_transaction import StockTransaction


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id",
            "transaction",
            "product",
            "quantity",
            "unit_cost",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class StockTransactionSerializer(serializers.ModelSerializer):
    items = StockMovementSerializer(many=True, read_only=True)

    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "company",
            "code",
            "transaction_type",
            "source_warehouse",
            "destination_warehouse",
            "date",
            "status",
            "reference",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "code",
            "status",
            "created_at",
            "updated_at",
        ]