from django.test import TestCase

from apps.accounting.models.account import Account
from apps.accounting.services.chart_of_accounts_seed import (
    STANDARD_CHART_OF_ACCOUNTS,
    seed_standard_chart_of_accounts,
)
from apps.core.models.company import Company


class StandardChartOfAccountsSeedTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")

    def test_seed_creates_parent_accounts(self):
        seed_standard_chart_of_accounts(self.company)

        parent_codes = {"1000", "2000", "3000", "4000", "5000"}
        existing_codes = set(
            Account.objects.filter(
                company=self.company,
                code__in=parent_codes,
                is_deleted=False,
            ).values_list("code", flat=True)
        )

        self.assertEqual(existing_codes, parent_codes)

    def test_seed_creates_child_accounts(self):
        seed_standard_chart_of_accounts(self.company)

        child_codes = {
            item["code"]
            for item in STANDARD_CHART_OF_ACCOUNTS
            if item["parent_code"] is not None
        }
        existing_codes = set(
            Account.objects.filter(
                company=self.company,
                code__in=child_codes,
                is_deleted=False,
            ).values_list("code", flat=True)
        )

        self.assertEqual(existing_codes, child_codes)

    def test_parent_accounts_are_not_postable(self):
        seed_standard_chart_of_accounts(self.company)

        parent_accounts = Account.objects.filter(
            company=self.company,
            code__in=["1000", "2000", "3000", "4000", "5000"],
            is_deleted=False,
        )

        self.assertTrue(parent_accounts.exists())
        self.assertFalse(parent_accounts.filter(is_postable=True).exists())

    def test_child_accounts_are_postable(self):
        seed_standard_chart_of_accounts(self.company)

        child_codes = [
            item["code"]
            for item in STANDARD_CHART_OF_ACCOUNTS
            if item["parent_code"] is not None
        ]
        child_accounts = Account.objects.filter(
            company=self.company,
            code__in=child_codes,
            is_deleted=False,
        )

        self.assertEqual(child_accounts.count(), len(child_codes))
        self.assertFalse(child_accounts.filter(is_postable=False).exists())

    def test_normal_balances_are_correct(self):
        seed_standard_chart_of_accounts(self.company)

        expected_by_type = {
            "asset": "debit",
            "expense": "debit",
            "liability": "credit",
            "equity": "credit",
            "income": "credit",
        }

        for account in Account.objects.filter(company=self.company):
            self.assertEqual(
                account.normal_balance,
                expected_by_type[account.account_type],
            )

    def test_seed_is_idempotent(self):
        seed_standard_chart_of_accounts(self.company)
        first_count = Account.objects.filter(company=self.company).count()

        seed_standard_chart_of_accounts(self.company)
        second_count = Account.objects.filter(company=self.company).count()

        self.assertEqual(first_count, second_count)

    def test_required_payment_accounts_exist(self):
        seed_standard_chart_of_accounts(self.company)

        required_codes = {"1003", "2001"}
        existing_codes = set(
            Account.objects.filter(
                company=self.company,
                code__in=required_codes,
                is_deleted=False,
            ).values_list("code", flat=True)
        )

        self.assertEqual(existing_codes, required_codes)

    def test_existing_account_name_is_preserved_and_parent_is_set(self):
        Account.objects.create(
            company=self.company,
            code="1001",
            name="Custom Bank Name",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            is_active=True,
        )

        seed_standard_chart_of_accounts(self.company)

        bank = Account.objects.get(company=self.company, code="1001")
        self.assertEqual(bank.name, "Custom Bank Name")
        self.assertEqual(bank.parent.code, "1000")
