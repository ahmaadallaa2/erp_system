from decimal import Decimal

from rest_framework import serializers

from apps.accounting.models.entry import JournalEntry, JournalItem
from apps.accounting.models.journal import Journal
from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.accounting.models.payment_allocation import PaymentAllocation
from apps.accounting.services.payment_allocation_service import (
    INVOICE_TYPES,
    PaymentAllocationService,
)


class AccountLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "code",
            "name",
            "account_type",
            "normal_balance",
            "is_postable",
            "is_active",
        ]
        read_only_fields = fields


class JournalBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = [
            "id",
            "code",
            "name",
            "type",
        ]
        read_only_fields = fields


class JournalItemLineSerializer(serializers.ModelSerializer):
    account_id = serializers.UUIDField(source="account.id", read_only=True)
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    partner_id = serializers.UUIDField(source="partner.id", read_only=True)
    partner_name = serializers.CharField(source="partner.name", read_only=True)

    class Meta:
        model = JournalItem
        fields = [
            "id",
            "account_id",
            "account_code",
            "account_name",
            "partner_id",
            "partner_name",
            "debit",
            "credit",
            "description",
        ]
        read_only_fields = fields


class JournalEntryDetailSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="notes", read_only=True)
    journal = JournalBasicSerializer(read_only=True)
    total_debit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    total_credit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    items = JournalItemLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "entry_number",
            "date",
            "status",
            "reference",
            "description",
            "journal",
            "total_debit",
            "total_credit",
            "items",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    journal_entry_id = serializers.UUIDField(read_only=True)
    allocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    unallocated_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "company",
            "branch",
            "voucher_number",
            "partner",
            "payment_type",
            "payment_method",
            "account",
            "amount",
            "allocated_amount",
            "unallocated_amount",
            "date",
            "status",
            "reference",
            "notes",
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
        read_only_fields = [
            "id",
            "voucher_number",
            "status",
            "journal_entry",
            "journal_entry_id",
            "posted_by",
            "posted_at",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "company",
            "branch",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if not user.company:
            raise serializers.ValidationError(
                "Authenticated user is not assigned to a company."
            )

        if not user.branch:
            raise serializers.ValidationError(
                "Authenticated user is not assigned to a branch."
            )

        return attrs

    def validate_partner(self, value):
        request = self.context["request"]
        user = request.user

        if value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected partner does not belong to the user's company."
            )

        return value

    def validate_account(self, value):
        request = self.context["request"]
        user = request.user

        if value.company_id != user.company_id:
            raise serializers.ValidationError(
                "Selected account does not belong to the user's company."
            )

        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        validated_data["company"] = user.company
        validated_data["branch"] = user.branch

        return super().create(validated_data)


class PaymentAllocationRequestSerializer(serializers.Serializer):
    invoice_id = serializers.UUIDField()
    invoice_type = serializers.ChoiceField(choices=list(INVOICE_TYPES))
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )


class PaymentAllocationSerializer(serializers.ModelSerializer):
    invoice_type = serializers.SerializerMethodField()
    invoice_id = serializers.UUIDField(source="invoice_object_id", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    invoice_amount_paid = serializers.DecimalField(
        source="invoice.amount_paid", max_digits=12, decimal_places=2, read_only=True
    )
    invoice_amount_due = serializers.DecimalField(
        source="invoice.amount_due", max_digits=12, decimal_places=2, read_only=True
    )
    invoice_payment_status = serializers.CharField(source="invoice.payment_status", read_only=True)
    payment_unallocated_amount = serializers.DecimalField(
        source="payment.unallocated_amount", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = PaymentAllocation
        fields = [
            "id",
            "payment",
            "invoice_type",
            "invoice_id",
            "invoice_number",
            "amount",
            "invoice_amount_paid",
            "invoice_amount_due",
            "invoice_payment_status",
            "payment_unallocated_amount",
            "created_at",
        ]
        read_only_fields = fields

    def get_invoice_type(self, obj) -> str:
        return PaymentAllocationService.invoice_type_for(obj)
