from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.accounting.admin.entry_admin import JournalEntryAdmin
from apps.accounting.admin.payment_admin import PaymentAdmin
from apps.accounting.models import JournalEntry, Journal
from apps.accounting.models.payment import Payment
from apps.accounting.services.chart_of_accounts_seed import seed_standard_chart_of_accounts
from apps.accounting.services.payment_service import PaymentService
from apps.core.models.company import Branch, Company
from apps.partners.models import Partner
from apps.users.models import User


class PaymentAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/")
        self.request.user = User.objects.create_superuser(
            email="accounting-admin@example.com",
            password="testpass123",
            full_name="Accounting Admin",
        )
        self.model_admin = PaymentAdmin(Payment, admin.site)

        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.accounts = seed_standard_chart_of_accounts(self.company)
        self.cash_account = self.accounts["1002"]
        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )

    def create_payment(self, status="draft"):
        return Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("100.00"),
            status=status,
        )

    def test_posted_and_cancelled_payment_cannot_be_changed_or_deleted(self):
        posted_payment = self.create_payment(status="posted")
        cancelled_payment = self.create_payment(status="cancelled")

        self.assertFalse(self.model_admin.has_change_permission(self.request, posted_payment))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, posted_payment))
        self.assertFalse(self.model_admin.has_change_permission(self.request, cancelled_payment))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, cancelled_payment))

    def test_status_is_readonly_and_bulk_delete_is_disabled(self):
        readonly_fields = self.model_admin.get_readonly_fields(self.request)
        actions = self.model_admin.get_actions(self.request)

        self.assertIn("status", readonly_fields)
        self.assertNotIn("delete_selected", actions)

    def test_cancel_action_uses_service_and_creates_reversal(self):
        payment = self.create_payment()
        PaymentService.post_payment(payment)
        payment.refresh_from_db()
        original_entry_id = payment.journal_entry_id

        with patch.object(self.model_admin, "message_user"):
            self.model_admin.action_cancel_payments(
                self.request,
                Payment.objects.filter(pk=payment.pk),
            )

        payment.refresh_from_db()
        self.assertEqual(payment.status, "cancelled")
        self.assertEqual(payment.journal_entry_id, original_entry_id)
        self.assertTrue(JournalEntry.objects.filter(reference=f"REV-{payment.voucher_number}").exists())


class JournalEntryAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/")
        self.request.user = User.objects.create_superuser(
            email="journal-admin@example.com",
            password="testpass123",
            full_name="Journal Admin",
        )
        self.model_admin = JournalEntryAdmin(JournalEntry, admin.site)
        self.company = Company.objects.create(name="Test Company")
        self.journal = Journal.objects.create(
            company=self.company,
            code="GEN",
            name="General Journal",
            type="general",
        )

    def create_entry(self, status="draft"):
        entry = JournalEntry.objects.create(
            company=self.company,
            journal=self.journal,
            reference=f"REF-{status}",
            status="draft",
        )
        if status != "draft":
            JournalEntry.objects.filter(pk=entry.pk).update(status=status)
            entry.refresh_from_db()
        return entry

    def test_posted_and_cancelled_entries_cannot_be_changed_or_deleted(self):
        posted_entry = self.create_entry(status="posted")
        cancelled_entry = self.create_entry(status="cancelled")

        self.assertFalse(self.model_admin.has_change_permission(self.request, posted_entry))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, posted_entry))
        self.assertFalse(self.model_admin.has_change_permission(self.request, cancelled_entry))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, cancelled_entry))

    def test_status_is_readonly_and_bulk_delete_is_disabled(self):
        readonly_fields = self.model_admin.get_readonly_fields(self.request)
        actions = self.model_admin.get_actions(self.request)

        self.assertIn("status", readonly_fields)
        self.assertNotIn("delete_selected", actions)
