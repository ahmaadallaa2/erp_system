from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.core.models.company import Branch, Company
from apps.partners.models import Partner
from apps.users.models import User
from apps.users.roles import ROLE_ACCOUNTING_MANAGER, assign_role


class PaymentAPITestCase(APITestCase):
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
        assign_role(self.user, ROLE_ACCOUNTING_MANAGER)
        self.client.force_authenticate(self.user)

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
            name="Customers",
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

        self.list_url = "/api/accounting/payments/"

    def payment_payload(self):
        return {
            "partner": str(self.customer.id),
            "payment_type": "inbound",
            "payment_method": "cash",
            "account": str(self.cash_account.id),
            "amount": "250.00",
            "date": "2026-05-10",
            "reference": "REF-1",
            "notes": "Initial receipt",
        }

    def test_authenticated_user_can_create_draft_payment(self):
        response = self.client.post(self.list_url, self.payment_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.get(id=response.data["id"])

        self.assertEqual(payment.company, self.company)
        self.assertEqual(payment.branch, self.branch)
        self.assertEqual(payment.status, "draft")
        self.assertEqual(payment.amount, Decimal("250.00"))
        self.assertTrue(payment.voucher_number.startswith("REC-"))

    def test_user_can_post_draft_payment(self):
        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("250.00"),
            status="draft",
        )

        response = self.client.post(
            f"{self.list_url}{payment.id}/post/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()

        self.assertEqual(payment.status, "posted")
        self.assertIsNotNone(payment.journal_entry_id)
        self.assertEqual(payment.posted_by, self.user)
        self.assertIsNotNone(payment.posted_at)

    def test_user_can_cancel_posted_payment(self):
        payment = self.create_posted_payment()
        original_entry_id = payment.journal_entry_id

        response = self.client.post(
            f"{self.list_url}{payment.id}/cancel/",
            {"cancellation_reason": "Duplicate receipt"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()

        self.assertEqual(payment.status, "cancelled")
        self.assertEqual(payment.journal_entry_id, original_entry_id)
        self.assertEqual(payment.cancelled_by, self.user)
        self.assertIsNotNone(payment.cancelled_at)
        self.assertEqual(payment.cancellation_reason, "Duplicate receipt")

    def test_posted_payment_cannot_be_edited(self):
        payment = self.create_posted_payment()

        response = self.client.patch(
            f"{self.list_url}{payment.id}/",
            {"notes": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payment.refresh_from_db()
        self.assertNotEqual(payment.notes, "Updated")

    def test_posted_payment_cannot_be_deleted(self):
        payment = self.create_posted_payment()

        response = self.client.delete(f"{self.list_url}{payment.id}/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Payment.objects.filter(id=payment.id).exists())

    def test_queryset_is_company_scoped(self):
        own_payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("100.00"),
            status="draft",
        )
        other_payment = Payment.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            partner=self.other_customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.other_cash_account,
            amount=Decimal("100.00"),
            status="draft",
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payment_ids = {item["id"] for item in response.data}

        self.assertIn(str(own_payment.id), payment_ids)
        self.assertNotIn(str(other_payment.id), payment_ids)

    def create_posted_payment(self):
        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("250.00"),
            status="draft",
        )

        self.client.post(f"{self.list_url}{payment.id}/post/", {}, format="json")
        payment.refresh_from_db()
        return payment
