from django.test import TestCase

from apps.accounting.models.account import Account
from apps.accounting.services.chart_of_accounts_seed import (
    STANDARD_CHART_OF_ACCOUNTS,
    create_default_chart_of_accounts,
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
        Account.objects.filter(company=self.company, code="1001").update(
            name="Custom Bank Name",
            parent=None,
        )

        seed_standard_chart_of_accounts(self.company)

        bank = Account.objects.get(company=self.company, code="1001")
        self.assertEqual(bank.name, "Custom Bank Name")
        self.assertEqual(bank.parent.code, "1000")


class DefaultChartOfAccountsSignalTestCase(TestCase):
    def test_new_company_gets_standard_chart_with_hierarchy(self):
        company = Company.objects.create(name="Signal Company")

        accounts = {
            account.code: account
            for account in Account.objects.filter(company=company).select_related("parent")
        }

        self.assertEqual(
            set(accounts),
            {item["code"] for item in STANDARD_CHART_OF_ACCOUNTS},
        )
        for item in STANDARD_CHART_OF_ACCOUNTS:
            account = accounts[item["code"]]
            self.assertEqual(account.name, item["name"])
            self.assertEqual(account.account_type, item["account_type"])
            self.assertEqual(account.is_postable, item["is_postable"])
            self.assertEqual(
                account.parent.code if account.parent else None,
                item["parent_code"],
            )

    def test_updating_company_does_not_duplicate_accounts(self):
        company = Company.objects.create(name="Signal Company")
        count_after_create = Account.objects.filter(company=company).count()

        company.name = "Renamed Company"
        company.save()

        self.assertEqual(
            Account.objects.filter(company=company).count(),
            count_after_create,
        )

    def test_create_default_chart_of_accounts_is_idempotent(self):
        company = Company.objects.create(name="Signal Company")
        count_after_create = Account.objects.filter(company=company).count()

        create_default_chart_of_accounts(company)

        self.assertEqual(
            Account.objects.filter(company=company).count(),
            count_after_create,
        )
