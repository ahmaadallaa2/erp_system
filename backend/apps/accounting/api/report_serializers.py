from rest_framework import serializers

from apps.accounting.models.account import Account
from apps.partners.models import Partner


def report_amount():
    # Sums across many lines can exceed the 12 digits of the model fields.
    return serializers.DecimalField(max_digits=20, decimal_places=2)


class ReportDateRangeFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be greater than or equal to start date."}
            )

        return attrs


class GeneralLedgerFilterSerializer(ReportDateRangeFilterSerializer):
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


class ReportAccountLineSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    balance = report_amount()


class ReportSectionSerializer(serializers.Serializer):
    account_type = serializers.CharField()
    label = serializers.CharField()
    accounts = ReportAccountLineSerializer(many=True)
    total = report_amount()


class TrialBalanceAccountSerializer(ReportAccountLineSerializer):
    normal_balance = serializers.CharField()
    total_debit = report_amount()
    total_credit = report_amount()
    debit_balance = report_amount()
    credit_balance = report_amount()


class TrialBalanceTotalsSerializer(serializers.Serializer):
    total_debit = report_amount()
    total_credit = report_amount()
    debit_balance = report_amount()
    credit_balance = report_amount()


class TrialBalanceSectionSerializer(TrialBalanceTotalsSerializer):
    account_type = serializers.CharField()
    label = serializers.CharField()
    accounts = TrialBalanceAccountSerializer(many=True)


class TrialBalanceGrandTotalsSerializer(TrialBalanceTotalsSerializer):
    is_balanced = serializers.BooleanField()


class TrialBalanceSerializer(serializers.Serializer):
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    sections = TrialBalanceSectionSerializer(many=True)
    totals = TrialBalanceGrandTotalsSerializer()


class IncomeStatementSerializer(serializers.Serializer):
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    income = ReportSectionSerializer()
    expenses = ReportSectionSerializer()
    net_profit = report_amount()


class EquitySectionSerializer(ReportSectionSerializer):
    retained_earnings = report_amount()
    net_profit = report_amount()


class BalanceSheetSerializer(serializers.Serializer):
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    assets = ReportSectionSerializer()
    liabilities = ReportSectionSerializer()
    equity = EquitySectionSerializer()
    total_liabilities_and_equity = report_amount()
    is_balanced = serializers.BooleanField()
