from rest_framework import serializers

from apps.inventory.models import Product, Warehouse


class ProductMovementHistoryFilterSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        required=False,
    )
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.none(),
        required=False,
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    transaction_type = serializers.ChoiceField(
        choices=["IN", "OUT", "TRANSFER"],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated and user.company_id:
            self.fields["product"].queryset = Product.objects.filter(
                company=user.company,
                is_deleted=False,
            )
            self.fields["warehouse"].queryset = Warehouse.objects.filter(
                company=user.company,
                is_deleted=False,
            )

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be greater than or equal to start date."}
            )

        return attrs


class ProductMovementHistoryRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    transaction_id = serializers.UUIDField()
    transaction_number = serializers.CharField(allow_blank=True, allow_null=True)
    reference = serializers.CharField(allow_blank=True, allow_null=True)
    transaction_type = serializers.CharField()
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    warehouse_id = serializers.UUIDField()
    warehouse_name = serializers.CharField()
    quantity_in = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity_out = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(allow_blank=True, allow_null=True)


class WarehouseBalanceFilterSerializer(serializers.Serializer):
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.none(),
        required=False,
    )
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.none(),
        required=False,
    )
    low_stock = serializers.BooleanField(required=False, allow_null=True, default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated and user.company_id:
            self.fields["warehouse"].queryset = Warehouse.objects.filter(
                company=user.company,
                is_deleted=False,
            )
            self.fields["product"].queryset = Product.objects.filter(
                company=user.company,
                is_deleted=False,
            )


class WarehouseBalanceRowSerializer(serializers.Serializer):
    warehouse_id = serializers.UUIDField()
    warehouse_name = serializers.CharField()
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    product_code = serializers.CharField(allow_blank=True, allow_null=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    reorder_point = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_low_stock = serializers.BooleanField()
    average_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    estimated_value = serializers.DecimalField(max_digits=24, decimal_places=2)
