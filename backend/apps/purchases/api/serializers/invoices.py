from rest_framework import serializers

from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.purchases.models.purchase_invoice_item import PurchaseInvoiceItem
from apps.users.roles import user_can_access_branch_id


class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceItem
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
                "Items can only be added to draft purchase invoices."
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


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True, read_only=True)
    journal_entry_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            "id",
            "company",
            "invoice_number",
            "branch",
            "supplier",
            "warehouse",
            "status",
            "invoice_date",
            "vendor_bill_number",
            "total_amount",
            "journal_entry",
            "journal_entry_id",
            "posted_by",
            "posted_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "shipping_cost",
            "clearance_cost",
            "commission_percentage",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "invoice_number",
            "branch",
            "status",
            "total_amount",
            "journal_entry",
            "journal_entry_id",
            "posted_by",
            "posted_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
            "updated_at",
        ]

    def validate_supplier(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected supplier does not belong to the user's company."
            )

        if value.partner_type not in ["supplier", "both"]:
            raise serializers.ValidationError(
                "Selected partner is not a supplier."
            )

        return value

    def validate_branch(self, value):
        request = self.context["request"]
        user = request.user

        if user.company and value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected branch does not belong to the user's company."
            )

        if not user_can_access_branch_id(user, value.id):
            raise serializers.ValidationError(
                "Selected branch is outside the user's branch access."
            )

        return value

    def validate_warehouse(self, value):
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
