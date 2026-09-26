from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.core.models.company import Branch, Company
from apps.users.models import User


class AccountLookupAPITestCase(APITestCase):
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

        self.cash_account = Account.objects.create(
            company=self.company,
            code="1002",
            name="Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            is_active=True,
        )
        self.inactive_account = Account.objects.create(
            company=self.company,
            code="1003",
            name="Inactive Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            is_active=False,
        )
        self.non_postable_account = Account.objects.create(
            company=self.company,
            code="1004",
            name="Asset Group",
            account_type="asset",
            normal_balance="debit",
            is_postable=False,
            is_active=True,
        )
        self.other_company_account = Account.objects.create(
            company=self.other_company,
            code="1002",
            name="Other Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            is_active=True,
        )

        self.list_url = "/api/accounting/accounts/"

    def test_authentication_is_required(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lists_only_current_company_accounts(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account_ids = {item["id"] for item in response.data}

        self.assertIn(str(self.cash_account.id), account_ids)
        self.assertNotIn(str(self.other_company_account.id), account_ids)

    def test_does_not_return_inactive_accounts(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account_ids = {item["id"] for item in response.data}

        self.assertNotIn(str(self.inactive_account.id), account_ids)

    def test_does_not_return_non_postable_accounts(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account_ids = {item["id"] for item in response.data}

        self.assertNotIn(str(self.non_postable_account.id), account_ids)

    def test_returns_lookup_fields(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        account = response.data[0]
        self.assertEqual(account["id"], str(self.cash_account.id))
        self.assertEqual(account["code"], "1002")
        self.assertEqual(account["name"], "Cash")
        self.assertEqual(account["account_type"], "asset")
