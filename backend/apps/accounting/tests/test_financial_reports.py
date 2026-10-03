from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.entry import JournalEntry, JournalItem
from apps.accounting.models.journal import Journal
from apps.accounting.services.reports import FinancialReportService
from apps.core.models.company import Branch, Company
from apps.partners.models import Partner
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User
from apps.users.roles import (
    ROLE_ACCOUNTANT,
    ROLE_AUDITOR,
    ROLE_SALES_USER,
    assign_role,
)


class FinancialReportFixtureMixin:
    """
    Posted activity for the main company:
      2026-01-05  Cash 1000 / Owner Capital 1000
      2026-01-20  Cash  500 / Sales Revenue  500
      2026-02-10  Operating Expenses 200 / Cash 200
      2026-02-15  Cash  300 / Sales Revenue  300
    Plus a draft entry and another company's entry that must be ignored.
    """

    def create_fixture(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_company = Company.objects.create(name="Other Company")

        self.journal = Journal.objects.create(
            company=self.company, code="GEN", name="General Journal", type="general"
        )
        self.other_journal = Journal.objects.create(
            company=self.other_company, code="GEN", name="Other Journal", type="general"
        )

        self.cash = self.account(self.company, "1002")
        self.capital = self.account(self.company, "3001")
        self.revenue = self.account(self.company, "4001")
        self.opex = self.account(self.company, "5002")

        self.capital_entry = self.post_entry("2026-01-05", [(self.cash, 1000, 0), (self.capital, 0, 1000)])
        self.post_entry("2026-01-20", [(self.cash, 500, 0), (self.revenue, 0, 500)])
        self.post_entry("2026-02-10", [(self.opex, 200, 0), (self.cash, 0, 200)])
        self.post_entry("2026-02-15", [(self.cash, 300, 0), (self.revenue, 0, 300)])

        self.create_entry(
            "2026-02-20", [(self.cash, 999, 0), (self.revenue, 0, 999)], post=False
        )
        self.create_entry(
            "2026-02-20",
            [
                (self.account(self.other_company, "1002"), 5000, 0),
                (self.account(self.other_company, "4001"), 0, 5000),
            ],
            company=self.other_company,
            journal=self.other_journal,
        )

    @staticmethod
    def account(company, code):
        return Account.objects.get(company=company, code=code, is_deleted=False)

    def post_entry(self, entry_date, lines):
        return self.create_entry(entry_date, lines)

    def create_entry(self, entry_date, lines, post=True, company=None, journal=None):
        entry = JournalEntry.objects.create(
            company=company or self.company,
            journal=journal or self.journal,
            date=entry_date,
            status="draft",
        )
        for account, debit, credit in lines:
            JournalItem.objects.create(
                entry=entry,
                account=account,
                description="Line",
                debit=Decimal(debit),
                credit=Decimal(credit),
            )
        if post:
            entry.post()
        return entry


def accounts_by_code(section):
    return {row["code"]: row for row in section["accounts"]}


class FinancialReportServiceTestCase(FinancialReportFixtureMixin, TestCase):
    def setUp(self):
        self.create_fixture()

    def test_trial_balance_aggregates_posted_company_items(self):
        report = FinancialReportService.trial_balance(self.company)

        sections = {section["account_type"]: section for section in report["sections"]}
        self.assertEqual(list(sections), ["asset", "liability", "equity", "income", "expense"])

        cash = accounts_by_code(sections["asset"])["1002"]
        self.assertEqual(cash["total_debit"], Decimal("1800.00"))
        self.assertEqual(cash["total_credit"], Decimal("200.00"))
        self.assertEqual(cash["balance"], Decimal("1600.00"))
        self.assertEqual(cash["debit_balance"], Decimal("1600.00"))
        self.assertEqual(cash["credit_balance"], Decimal("0.00"))

        revenue = accounts_by_code(sections["income"])["4001"]
        self.assertEqual(revenue["balance"], Decimal("800.00"))
        self.assertEqual(revenue["credit_balance"], Decimal("800.00"))

        self.assertEqual(sections["liability"]["accounts"], [])
        self.assertEqual(report["totals"]["total_debit"], Decimal("2000.00"))
        self.assertEqual(report["totals"]["total_credit"], Decimal("2000.00"))
        self.assertEqual(report["totals"]["debit_balance"], Decimal("1800.00"))
        self.assertEqual(report["totals"]["credit_balance"], Decimal("1800.00"))
        self.assertTrue(report["totals"]["is_balanced"])

    def test_trial_balance_respects_date_range(self):
        report = FinancialReportService.trial_balance(
            self.company, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )

        sections = {section["account_type"]: section for section in report["sections"]}
        cash = accounts_by_code(sections["asset"])["1002"]
        self.assertEqual(cash["total_debit"], Decimal("300.00"))
        self.assertEqual(cash["total_credit"], Decimal("200.00"))
        self.assertEqual(sections["equity"]["accounts"], [])
        self.assertEqual(report["totals"]["total_debit"], Decimal("500.00"))
        self.assertTrue(report["totals"]["is_balanced"])

    def test_income_statement_calculates_net_profit(self):
        report = FinancialReportService.income_statement(
            self.company, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )

        self.assertEqual(report["income"]["total"], Decimal("300.00"))
        self.assertEqual(report["expenses"]["total"], Decimal("200.00"))
        self.assertEqual(report["net_profit"], Decimal("100.00"))
        self.assertEqual(list(accounts_by_code(report["expenses"])), ["5002"])

    def test_income_statement_reports_loss_as_negative(self):
        self.post_entry("2026-03-01", [(self.opex, 900, 0), (self.cash, 0, 900)])

        report = FinancialReportService.income_statement(
            self.company, start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )

        self.assertEqual(report["net_profit"], Decimal("-900.00"))

    def test_balance_sheet_injects_period_profit_and_retained_earnings(self):
        report = FinancialReportService.balance_sheet(
            self.company, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )

        self.assertEqual(report["assets"]["total"], Decimal("1600.00"))
        self.assertEqual(report["liabilities"]["total"], Decimal("0.00"))
        self.assertEqual(accounts_by_code(report["equity"])["3001"]["balance"], Decimal("1000.00"))
        self.assertEqual(report["equity"]["retained_earnings"], Decimal("500.00"))
        self.assertEqual(report["equity"]["net_profit"], Decimal("100.00"))
        self.assertEqual(report["equity"]["total"], Decimal("1600.00"))
        self.assertEqual(report["total_liabilities_and_equity"], Decimal("1600.00"))
        self.assertTrue(report["is_balanced"])

    def test_balance_sheet_as_of_date_without_start_date(self):
        report = FinancialReportService.balance_sheet(self.company, end_date=date(2026, 1, 31))

        self.assertEqual(report["assets"]["total"], Decimal("1500.00"))
        self.assertEqual(report["equity"]["retained_earnings"], Decimal("0.00"))
        self.assertEqual(report["equity"]["net_profit"], Decimal("500.00"))
        self.assertTrue(report["is_balanced"])

    def test_branch_scope_only_includes_entries_linked_to_branch_documents(self):
        customer = Partner.objects.create(
            company=self.company, partner_type="customer", name="Customer A"
        )
        SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=customer,
            journal_entry=self.capital_entry,
        )

        report = FinancialReportService.trial_balance(self.company, branch=self.branch)

        self.assertEqual(report["totals"]["total_debit"], Decimal("1000.00"))
        self.assertTrue(report["totals"]["is_balanced"])


class FinancialReportAPITestCase(FinancialReportFixtureMixin, APITestCase):
    urls = {
        "trial_balance": "/api/accounting/reports/trial-balance/",
        "income_statement": "/api/accounting/reports/income-statement/",
        "balance_sheet": "/api/accounting/reports/balance-sheet/",
    }

    def setUp(self):
        self.create_fixture()
        self.auditor = self.create_user("auditor@example.com", ROLE_AUDITOR)

    def create_user(self, email, role, branch=None):
        user = User.objects.create_user(
            email=email,
            password="password",
            full_name=email,
            company=self.company,
            branch=branch,
        )
        assign_role(user, role)
        return user

    def test_authentication_is_required(self):
        for url in self.urls.values():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_user_gets_reports(self):
        self.client.force_authenticate(self.auditor)
        params = {"start_date": "2026-02-01", "end_date": "2026-02-28"}

        for url in self.urls.values():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, params).status_code, status.HTTP_200_OK)

    def test_trial_balance_response_format(self):
        self.client.force_authenticate(self.auditor)

        response = self.client.get(self.urls["trial_balance"])

        self.assertEqual(response.data["sections"][0]["account_type"], "asset")
        cash = response.data["sections"][0]["accounts"][0]
        self.assertEqual(cash["code"], "1002")
        self.assertEqual(cash["balance"], "1600.00")
        self.assertEqual(response.data["totals"]["total_debit"], "2000.00")
        self.assertTrue(response.data["totals"]["is_balanced"])
        self.assertIsNone(response.data["start_date"])

    def test_income_statement_response_format(self):
        self.client.force_authenticate(self.auditor)

        response = self.client.get(
            self.urls["income_statement"],
            {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        )

        self.assertEqual(response.data["start_date"], "2026-02-01")
        self.assertEqual(response.data["income"]["total"], "300.00")
        self.assertEqual(response.data["expenses"]["total"], "200.00")
        self.assertEqual(response.data["net_profit"], "100.00")

    def test_balance_sheet_response_format(self):
        self.client.force_authenticate(self.auditor)

        response = self.client.get(
            self.urls["balance_sheet"],
            {"start_date": "2026-02-01", "end_date": "2026-02-28"},
        )

        self.assertEqual(response.data["assets"]["total"], "1600.00")
        self.assertEqual(response.data["equity"]["retained_earnings"], "500.00")
        self.assertEqual(response.data["equity"]["net_profit"], "100.00")
        self.assertEqual(response.data["total_liabilities_and_equity"], "1600.00")
        self.assertTrue(response.data["is_balanced"])

    def test_user_without_report_role_is_forbidden(self):
        self.client.force_authenticate(self.create_user("sales@example.com", ROLE_SALES_USER))

        for url in self.urls.values():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_date_range_is_rejected(self):
        self.client.force_authenticate(self.auditor)

        for url in self.urls.values():
            with self.subTest(url=url):
                response = self.client.get(
                    url, {"start_date": "2026-02-28", "end_date": "2026-02-01"}
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_branch_scoped_accountant_sees_only_branch_entries(self):
        self.client.force_authenticate(
            self.create_user("accountant@example.com", ROLE_ACCOUNTANT, branch=self.branch)
        )

        response = self.client.get(self.urls["trial_balance"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["totals"]["total_debit"], "0.00")

    def test_branch_scoped_accountant_without_branch_is_forbidden(self):
        self.client.force_authenticate(self.create_user("nobranch@example.com", ROLE_ACCOUNTANT))

        for url in [*self.urls.values(), "/api/accounting/reports/general-ledger/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
