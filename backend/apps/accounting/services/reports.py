from datetime import timedelta
from decimal import Decimal

from django.db.models import Case, IntegerField, Q, Sum, When

from apps.accounting.models.account import Account
from apps.accounting.models.entry import JournalEntry, JournalItem

ZERO = Decimal("0.00")

ACCOUNT_TYPE_LABELS = dict(Account.ACCOUNT_TYPES)
ACCOUNT_TYPE_ORDER = ("asset", "liability", "equity", "income", "expense")


def branch_entry_q(branch, prefix=""):
    """Journal entries attributed to a branch through their source document."""
    return (
        Q(**{f"{prefix}linked_payment__branch": branch})
        | Q(**{f"{prefix}sales_invoice__branch": branch})
        | Q(**{f"{prefix}purchase_invoice__branch": branch})
        | Q(**{f"{prefix}stock_transaction__source_warehouse__branch": branch})
        | Q(**{f"{prefix}stock_transaction__destination_warehouse__branch": branch})
    )


class GeneralLedgerReportService:
    @staticmethod
    def rows(
        company,
        start_date=None,
        end_date=None,
        account=None,
        partner=None,
        branch=None,
    ):
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

        if branch:
            queryset = queryset.filter(branch_entry_q(branch, prefix="entry__")).distinct()

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


class FinancialReportService:
    """
    Trial balance, income statement and balance sheet built from posted
    journal items only. Balances are signed by each account's normal balance,
    so a negative balance means the account is on its contra side.
    """

    @classmethod
    def trial_balance(cls, company, start_date=None, end_date=None, branch=None):
        rows = cls._account_rows(
            ACCOUNT_TYPE_ORDER,
            company=company,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        sections = []
        for account_type in ACCOUNT_TYPE_ORDER:
            accounts = [row for row in rows if row["account_type"] == account_type]
            sections.append(
                {
                    "account_type": account_type,
                    "label": str(ACCOUNT_TYPE_LABELS[account_type]),
                    "accounts": accounts,
                    **cls._trial_balance_totals(accounts),
                }
            )

        totals = cls._trial_balance_totals(rows)
        totals["is_balanced"] = totals["total_debit"] == totals["total_credit"]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "sections": sections,
            "totals": totals,
        }

    @classmethod
    def income_statement(cls, company, start_date=None, end_date=None, branch=None):
        rows = cls._account_rows(
            ("income", "expense"),
            company=company,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        income = cls._section("income", rows)
        expenses = cls._section("expense", rows)

        return {
            "start_date": start_date,
            "end_date": end_date,
            "income": income,
            "expenses": expenses,
            "net_profit": income["total"] - expenses["total"],
        }

    @classmethod
    def balance_sheet(cls, company, start_date=None, end_date=None, branch=None):
        # Balance sheet accounts are cumulative up to end_date. Profit before
        # start_date is shown as retained earnings and profit inside the period
        # as net profit, so Assets = Liabilities + Equity holds either way.
        rows = cls._account_rows(
            ("asset", "liability", "equity"),
            company=company,
            end_date=end_date,
            branch=branch,
        )
        assets = cls._section("asset", rows)
        liabilities = cls._section("liability", rows)
        equity = cls._section("equity", rows)

        net_profit = cls.income_statement(
            company,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )["net_profit"]

        retained_earnings = ZERO
        if start_date:
            retained_earnings = cls.income_statement(
                company,
                end_date=start_date - timedelta(days=1),
                branch=branch,
            )["net_profit"]

        equity["retained_earnings"] = retained_earnings
        equity["net_profit"] = net_profit
        equity["total"] += retained_earnings + net_profit

        total_liabilities_and_equity = liabilities["total"] + equity["total"]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_liabilities_and_equity": total_liabilities_and_equity,
            "is_balanced": assets["total"] == total_liabilities_and_equity,
        }

    @staticmethod
    def _account_rows(account_types, company, start_date=None, end_date=None, branch=None):
        queryset = JournalItem.objects.filter(
            entry__company=company,
            entry__status="posted",
            entry__is_deleted=False,
            account__account_type__in=account_types,
        )

        if start_date:
            queryset = queryset.filter(entry__date__gte=start_date)

        if end_date:
            queryset = queryset.filter(entry__date__lte=end_date)

        if branch:
            # Subquery instead of joins so the per-account sums are never
            # multiplied by the branch lookups.
            queryset = queryset.filter(
                entry__in=JournalEntry.objects.filter(branch_entry_q(branch)).values("pk")
            )

        totals = (
            queryset.values(
                "account_id",
                "account__code",
                "account__name",
                "account__account_type",
                "account__normal_balance",
            )
            .annotate(total_debit=Sum("debit"), total_credit=Sum("credit"))
            .order_by("account__code")
        )

        rows = []
        for total in totals:
            debit = total["total_debit"] or ZERO
            credit = total["total_credit"] or ZERO
            net_debit = debit - credit

            if total["account__normal_balance"] == "credit":
                balance = -net_debit
            else:
                balance = net_debit

            rows.append(
                {
                    "account_id": total["account_id"],
                    "code": total["account__code"],
                    "name": total["account__name"],
                    "account_type": total["account__account_type"],
                    "normal_balance": total["account__normal_balance"],
                    "total_debit": debit,
                    "total_credit": credit,
                    "debit_balance": max(net_debit, ZERO),
                    "credit_balance": max(-net_debit, ZERO),
                    "balance": balance,
                }
            )

        return rows

    @staticmethod
    def _section(account_type, rows):
        accounts = [row for row in rows if row["account_type"] == account_type]
        return {
            "account_type": account_type,
            "label": str(ACCOUNT_TYPE_LABELS[account_type]),
            "accounts": accounts,
            "total": sum((row["balance"] for row in accounts), ZERO),
        }

    @staticmethod
    def _trial_balance_totals(rows):
        return {
            field: sum((row[field] for row in rows), ZERO)
            for field in ("total_debit", "total_credit", "debit_balance", "credit_balance")
        }
