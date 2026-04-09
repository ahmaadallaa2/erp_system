from rest_framework import serializers
from apps.partners.models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    current_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Partner
        fields = [
            "id",
            "company",
            "code",
            "partner_type",
            "name",
            "phone",
            "mobile",
            "email",
            "website",
            "address",
            "city",
            "tax_number",
            "commercial_record",
            "credit_limit",
            "initial_balance",
            "current_balance",
            "is_active",
            "notes",
            "responsible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "code",
            "current_balance",
            "created_at",
            "updated_at",
        ]