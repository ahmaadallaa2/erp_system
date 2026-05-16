from rest_framework import serializers

from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment


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


class PaymentSerializer(serializers.ModelSerializer):
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
            "date",
            "status",
            "reference",
            "notes",
            "journal_entry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "voucher_number",
            "status",
            "journal_entry",
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
