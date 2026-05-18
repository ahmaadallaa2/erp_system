from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.entry import JournalEntry, JournalItem
from apps.accounting.models.journal import Journal
from apps.core.models.company import Branch, Company
from apps.partners.models import Partner
from apps.users.models import User


class GeneralLedgerReportAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_company = Company.objects.create(name="Other Company")
        self.other_branch = Branch.objects.create(
            company=self.other_company,
            name="Other Branch",
        )

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password",
            full_name="Test User",
            company=self.company,
            branch=self.branch,
        )

        self.journal = Journal.objects.create(
            company=self.company,
            code="GEN",
            name="General Journal",
            type="general",
        )
        self.other_journal = Journal.objects.create(
            company=self.other_company,
            code="GEN",
            name="Other General Journal",
            type="general",
        )

        self.cash_account = Account.objects.create(
            company=self.company,
            code="1002",
            name="Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )
        self.receivable_account = Account.objects.create(
            company=self.company,
            code="1003",
            name="Accounts Receivable",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            allow_reconciliation=True,
        )
        self.revenue_account = Account.objects.create(
            company=self.company,
            code="4001",
            name="Sales Revenue",
            account_type="income",
            normal_balance="credit",
            is_postable=True,
        )
        self.other_cash_account = Account.objects.create(
            company=self.other_company,
            code="1002",
            name="Other Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            allow_reconciliation=True,
        )

        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )
        self.other_customer = Partner.objects.create(
            company=self.other_company,
            partner_type="customer",
            name="Other Customer",
        )

        self.url = "/api/accounting/reports/general-ledger/"

    def test_authentication_is_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_returns_posted_company_rows_only(self):
        self.client.force_authenticate(self.user)
        posted_entry = self.create_posted_entry(
            date="2026-05-10",
            reference="POSTED-1",
            debit=Decimal("100.00"),
            credit=Decimal("100.00"),
        )
        self.create_draft_entry()
        self.create_other_company_posted_entry()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        entry_ids = {row["journal_entry_id"] for row in response.data}

        self.assertEqual(entry_ids, {str(posted_entry.id)})
        self.assertEqual(
            [row["account_code"] for row in response.data],
            ["1003", "4001"],
        )
        self.assertEqual(response.data[0]["reference"], "POSTED-1")
        self.assertEqual(response.data[0]["account_code"], "1003")
        self.assertEqual(response.data[0]["account_name"], "Accounts Receivable")
        self.assertEqual(response.data[0]["partner"], "Customer A")
        self.assertEqual(response.data[0]["debit"], "100.00")
        self.assertEqual(response.data[0]["credit"], "0.00")
        self.assertEqual(response.data[0]["running_balance"], "100.00")

    def test_account_filter_returns_account_rows_and_running_balance(self):
        self.client.force_authenticate(self.user)
        self.create_posted_entry(
            date="2026-05-10",
            reference="POSTED-1",
            debit=Decimal("100.00"),
            credit=Decimal("100.00"),
        )
        self.create_posted_entry(
            date="2026-05-11",
            reference="POSTED-2",
            debit=Decimal("50.00"),
            credit=Decimal("50.00"),
        )

        response = self.client.get(
            self.url,
            {"account": str(self.receivable_account.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["running_balance"], "100.00")
        self.assertEqual(response.data[1]["running_balance"], "150.00")
        self.assertTrue(
            all(row["account_code"] == "1003" for row in response.data)
        )

    def test_partner_and_date_filters_are_applied(self):
        self.client.force_authenticate(self.user)
        self.create_posted_entry(
            date="2026-05-09",
            reference="BEFORE",
            debit=Decimal("80.00"),
            credit=Decimal("80.00"),
        )
        included_entry = self.create_posted_entry(
            date="2026-05-10",
            reference="INCLUDED",
            debit=Decimal("120.00"),
            credit=Decimal("120.00"),
        )

        response = self.client.get(
            self.url,
            {
                "start_date": "2026-05-10",
                "end_date": "2026-05-10",
                "partner": str(self.customer.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["journal_entry_id"], str(included_entry.id))
        self.assertEqual(response.data[0]["partner"], "Customer A")

    def test_another_company_account_filter_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {"account": str(self.other_cash_account.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_range_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {
                "start_date": "2026-05-11",
                "end_date": "2026-05-10",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def create_posted_entry(self, date, reference, debit, credit):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            date=date,
            reference=reference,
            status="draft",
        )
        JournalItem.objects.create(
            entry=entry,
            account=self.receivable_account,
            partner=self.customer,
            description="Receivable line",
            debit=debit,
            credit=Decimal("0.00"),
        )
        JournalItem.objects.create(
            entry=entry,
            account=self.revenue_account,
            description="Revenue line",
            debit=Decimal("0.00"),
            credit=credit,
        )
        entry.post()
        entry.refresh_from_db()
        return entry

    def create_draft_entry(self):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            date="2026-05-10",
            reference="DRAFT-1",
            status="draft",
        )
        JournalItem.objects.create(
            entry=entry,
            account=self.cash_account,
            description="Draft line",
            debit=Decimal("999.00"),
            credit=Decimal("0.00"),
        )
        return entry

    def create_other_company_posted_entry(self):
        entry = JournalEntry.objects.create(
            company=self.other_company,
            journal=self.other_journal,
            date="2026-05-10",
            reference="OTHER-1",
            status="draft",
        )
        JournalItem.objects.create(
            entry=entry,
            account=self.other_cash_account,
            partner=self.other_customer,
            description="Other cash line",
            debit=Decimal("200.00"),
            credit=Decimal("0.00"),
        )
        JournalItem.objects.create(
            entry=entry,
            account=Account.objects.create(
                company=self.other_company,
                code="4001",
                name="Other Revenue",
                account_type="income",
                normal_balance="credit",
                is_postable=True,
            ),
            description="Other revenue line",
            debit=Decimal("0.00"),
            credit=Decimal("200.00"),
        )
        entry.post()
        return entry
