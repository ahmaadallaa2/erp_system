from rest_framework import serializers
from apps.partners.models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    current_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Calculated current balance for the partner.",
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
        extra_kwargs = {
            "partner_type": {
                "help_text": "Type of partner: customer, supplier, or both.",
            },
            "name": {
                "help_text": "Partner display name.",
            },
            "phone": {
                "help_text": "Primary phone number.",
            },
            "mobile": {
                "help_text": "Mobile number.",
            },
            "email": {
                "help_text": "Email address.",
            },
            "website": {
                "help_text": "Website URL.",
            },
            "address": {
                "help_text": "Street address.",
            },
            "city": {
                "help_text": "City name.",
            },
            "tax_number": {
                "help_text": "Tax registration number.",
            },
            "commercial_record": {
                "help_text": "Commercial registration number.",
            },
            "credit_limit": {
                "help_text": "Maximum allowed credit limit for the partner.",
            },
            "initial_balance": {
                "help_text": "Opening balance for the partner.",
            },
            "is_active": {
                "help_text": "Indicates whether the partner is active.",
            },
            "notes": {
                "help_text": "Internal notes about the partner.",
            },
            "responsible": {
                "help_text": "Responsible employee/user for this partner.",
            },
        }