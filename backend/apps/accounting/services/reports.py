from decimal import Decimal

from django.db.models import Case, IntegerField, When

from apps.accounting.models.entry import JournalItem


class GeneralLedgerReportService:
    @staticmethod
    def rows(company, start_date=None, end_date=None, account=None, partner=None):
        queryset = (
            JournalItem.objects.filter(
                entry__company=company,
                entry__status="posted",
                entry__is_deleted=False,
            )
            .select_related("entry", "account", "partner")
            .annotate(
                line_side_order=Case(
                    When(debit__gt=Decimal("0.00"), then=0),
                    default=1,
                    output_field=IntegerField(),
                )
            )
            .order_by(
                "entry__date",
                "entry__entry_number",
                "entry__reference",
                "line_side_order",
                "account__code",
                "id",
            )
        )

        if start_date:
            queryset = queryset.filter(entry__date__gte=start_date)

        if end_date:
            queryset = queryset.filter(entry__date__lte=end_date)

        if account:
            queryset = queryset.filter(account=account)

        if partner:
            queryset = queryset.filter(partner=partner)

        running_balances = {}
        rows = []

        for item in queryset:
            account_id = item.account_id
            previous_balance = running_balances.get(account_id, Decimal("0.00"))

            if item.account.normal_balance == "credit":
                movement = item.credit - item.debit
            else:
                movement = item.debit - item.credit

            running_balance = previous_balance + movement
            running_balances[account_id] = running_balance

            rows.append(
                {
                    "date": item.entry.date,
                    "journal_entry_id": item.entry_id,
                    "entry_number": item.entry.entry_number,
                    "reference": item.entry.reference,
                    "account_code": item.account.code,
                    "account_name": item.account.name,
                    "partner": item.partner.name if item.partner else None,
                    "debit": item.debit,
                    "credit": item.credit,
                    "running_balance": running_balance,
                }
            )

        return rows
