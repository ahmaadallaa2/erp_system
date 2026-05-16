from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.entry import JournalEntry, JournalItem
from apps.accounting.models.journal import Journal
from apps.core.models.company import Branch, Company
from apps.partners.models import Partner
from apps.users.models import User


class JournalEntryAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_company = Company.objects.create(name="Other Company")

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
        self.other_cash_account = Account.objects.create(
            company=self.other_company,
            code="1002",
            name="Other Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )

        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )

        self.entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            date="2026-05-10",
            reference="SINV-00001",
            notes="Sales invoice posting",
            status="draft",
        )
        JournalItem.objects.create(
            entry=self.entry,
            account=self.cash_account,
            description="Cash line",
            debit=Decimal("100.00"),
            credit=Decimal("0.00"),
        )
        JournalItem.objects.create(
            entry=self.entry,
            account=self.receivable_account,
            partner=self.customer,
            description="Customer line",
            debit=Decimal("0.00"),
            credit=Decimal("100.00"),
        )

        self.other_entry = JournalEntry.objects.create(
            company=self.other_company,
            journal=self.other_journal,
            date="2026-05-10",
            reference="OTHER-00001",
            notes="Other company entry",
            status="draft",
        )
        JournalItem.objects.create(
            entry=self.other_entry,
            account=self.other_cash_account,
            description="Other cash line",
            debit=Decimal("50.00"),
            credit=Decimal("0.00"),
        )

    def detail_url(self, entry):
        return f"/api/accounting/journal-entries/{entry.id}/"

    def test_authenticated_user_can_retrieve_own_company_journal_entry(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.detail_url(self.entry))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.entry.id))
        self.assertEqual(response.data["entry_number"], self.entry.entry_number)
        self.assertEqual(response.data["reference"], "SINV-00001")
        self.assertEqual(response.data["description"], "Sales invoice posting")
        self.assertEqual(response.data["journal"]["id"], str(self.journal.id))
        self.assertEqual(response.data["journal"]["code"], "GEN")

    def test_user_cannot_retrieve_another_company_journal_entry(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.detail_url(self.other_entry))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_includes_journal_items_with_debit_credit_and_account_data(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.detail_url(self.entry))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_debit"], "100.00")
        self.assertEqual(response.data["total_credit"], "100.00")
        self.assertEqual(len(response.data["items"]), 2)

        cash_line = next(
            item for item in response.data["items"]
            if item["account_code"] == "1002"
        )
        customer_line = next(
            item for item in response.data["items"]
            if item["account_code"] == "1003"
        )

        self.assertEqual(cash_line["account_id"], str(self.cash_account.id))
        self.assertEqual(cash_line["account_name"], "Cash")
        self.assertEqual(cash_line["debit"], "100.00")
        self.assertEqual(cash_line["credit"], "0.00")
        self.assertEqual(cash_line["description"], "Cash line")

        self.assertEqual(customer_line["partner_id"], str(self.customer.id))
        self.assertEqual(customer_line["partner_name"], "Customer A")
        self.assertEqual(customer_line["debit"], "0.00")
        self.assertEqual(customer_line["credit"], "100.00")

    def test_unauthenticated_access_is_rejected(self):
        response = self.client.get(self.detail_url(self.entry))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
