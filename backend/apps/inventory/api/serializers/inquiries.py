from rest_framework import serializers

from apps.inventory.models.stock_balance import StockBalance


class StockBalanceSerializer(serializers.ModelSerializer):
    available_quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = StockBalance
        fields = [
            "id",
            "company",
            "product",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "location",
            "reorder_point",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "product",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "location",
            "reorder_point",
            "created_at",
            "updated_at",
        ]