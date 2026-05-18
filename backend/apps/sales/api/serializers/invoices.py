from rest_framework import serializers

from apps.sales.models import SalesInvoice, SalesInvoiceItem


class SalesInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItem
        fields = [
            "id",
            "invoice",
            "product",
            "quantity",
            "unit_price",
            "line_total",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "line_total",
            "created_at",
            "updated_at",
        ]

    def validate_invoice(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected invoice does not belong to the user's company."
            )

        if value.status != "draft":
            raise serializers.ValidationError(
                "Items can only be added to draft invoices."
            )

        return value

    def validate_product(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected product does not belong to the user's company."
            )

        return value


class SalesInvoiceSerializer(serializers.ModelSerializer):
    items = SalesInvoiceItemSerializer(many=True, read_only=True)
    journal_entry_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = SalesInvoice
        fields = [
            "id",
            "company",
            "branch",
            "invoice_number",
            "customer",
            "warehouse",
            "date",
            "status",
            "total_amount",
            "journal_entry",
            "journal_entry_id",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "branch",
            "invoice_number",
            "status",
            "total_amount",
            "journal_entry",
            "journal_entry_id",
            "created_at",
            "updated_at",
        ]

    def validate_customer(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected customer does not belong to the user's company."
            )

        if value.partner_type not in ["customer", "both"]:
            raise serializers.ValidationError(
                "Selected partner is not a customer."
            )

        return value

    def validate_warehouse(self, value):
        if value is None:
            return value

        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected warehouse does not belong to the user's company."
            )

        return value
