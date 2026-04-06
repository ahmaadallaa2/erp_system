from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.core.models.company import Company
from apps.accounting.models.account import Account
from apps.accounting.models.journal import Journal
from apps.accounting.models.entry import JournalEntry, JournalItem


class JournalEntryModelTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")

        self.journal = Journal.objects.create(
            company=self.company,
            code="GEN",
            name="General Journal",
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

        self.revenue_account = Account.objects.create(
            company=self.company,
            code="4001",
            name="Revenue",
            account_type="income",
            normal_balance="credit",
            is_postable=True,
        )

    def test_post_balanced_entry_success(self):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            reference="TEST-1",
            status="draft",
        )

        JournalItem.objects.create(
            entry=entry,
            account=self.cash_account,
            description="Debit line",
            debit=Decimal("100.00"),
            credit=Decimal("0.00"),
        )

        JournalItem.objects.create(
            entry=entry,
            account=self.revenue_account,
            description="Credit line",
            debit=Decimal("0.00"),
            credit=Decimal("100.00"),
        )

        entry.post()
        entry.refresh_from_db()

        self.assertEqual(entry.status, "posted")
        self.assertTrue(entry.is_balanced)

    def test_post_unbalanced_entry_fails(self):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            reference="TEST-2",
            status="draft",
        )

        JournalItem.objects.create(
            entry=entry,
            account=self.cash_account,
            description="Debit line",
            debit=Decimal("100.00"),
            credit=Decimal("0.00"),
        )

        JournalItem.objects.create(
            entry=entry,
            account=self.revenue_account,
            description="Credit line",
            debit=Decimal("0.00"),
            credit=Decimal("80.00"),
        )

        with self.assertRaises(ValidationError):
            entry.post()

    def test_journal_item_cannot_be_zero_on_both_sides(self):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            reference="TEST-3",
            status="draft",
        )

        item = JournalItem(
            entry=entry,
            account=self.cash_account,
            description="Zero line",
            debit=Decimal("0.00"),
            credit=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError):
            item.full_clean()