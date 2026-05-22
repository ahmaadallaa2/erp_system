from rest_framework import serializers

from apps.inventory.models.stock_movement import StockMovement
from apps.inventory.models.stock_transaction import StockTransaction
from apps.users.roles import user_can_access_branch_id


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
            "posted_by",
            "posted_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "code",
            "status",
            "posted_by",
            "posted_at",
            "created_at",
            "updated_at",
        ]

    def validate_source_warehouse(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected warehouse does not belong to the user's company."
            )

        if not user_can_access_branch_id(user, value.branch_id):
            raise serializers.ValidationError(
                "Selected warehouse is outside the user's branch access."
            )

        return value

    def validate_destination_warehouse(self, value):
        if value is None:
            return value

        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected destination warehouse does not belong to the user's company."
            )

        if not user_can_access_branch_id(user, value.branch_id):
            raise serializers.ValidationError(
                "Selected destination warehouse is outside the user's branch access."
            )

        return value
