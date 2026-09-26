from rest_framework import serializers

from apps.accounting.models.account import Account
from apps.partners.models import Partner


class GeneralLedgerFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.none(),
        required=False,
    )
    partner = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.none(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated and user.company_id:
            self.fields["account"].queryset = Account.objects.filter(
                company=user.company,
                is_deleted=False,
            )
            self.fields["partner"].queryset = Partner.objects.filter(
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


class GeneralLedgerRowSerializer(serializers.Serializer):
    date = serializers.DateField()
    journal_entry_id = serializers.UUIDField()
    entry_number = serializers.CharField()
    reference = serializers.CharField(allow_blank=True, allow_null=True)
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    partner = serializers.CharField(allow_null=True)
    debit = serializers.DecimalField(max_digits=12, decimal_places=2)
    credit = serializers.DecimalField(max_digits=12, decimal_places=2)
    running_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
