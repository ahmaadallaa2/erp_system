from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.core.models.company import Company, Branch
from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.accounting.services.chart_of_accounts_seed import (
    seed_standard_chart_of_accounts,
)
from apps.accounting.services.payment_service import PaymentService
from apps.partners.models import Partner


class PaymentServiceTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")

        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A"
        )

        self.supplier = Partner.objects.create(
            company=self.company,
            partner_type="supplier",
            name="Supplier A"
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

        self.payable_account = Account.objects.create(
            company=self.company,
            code="2001",
            name="Suppliers",
            account_type="liability",
            normal_balance="credit",
            is_postable=True,
            allow_reconciliation=True,
        )

    def test_post_inbound_payment_creates_entry_and_updates_status(self):
        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("500.00"),
            status="draft",
        )

        entry = PaymentService.post_payment(payment)

        payment.refresh_from_db()
        entry.refresh_from_db()

        self.assertEqual(payment.status, "posted")
        self.assertEqual(payment.journal_entry, entry)
        self.assertEqual(entry.status, "posted")

        items = entry.items.order_by("id")
        self.assertEqual(items.count(), 2)

        cash_line = items.filter(account=self.cash_account).first()
        customer_line = items.filter(account=self.receivable_account).first()

        self.assertEqual(cash_line.debit, Decimal("500.00"))
        self.assertIsNone(cash_line.partner)
        self.assertEqual(customer_line.credit, Decimal("500.00"))
        self.assertEqual(customer_line.partner, self.customer)

    def test_post_outbound_payment_creates_entry_and_updates_status(self):
        # نعطي الصندوق رصيد أولًا عن طريق قيد سابق
        from apps.accounting.models.entry import JournalEntry, JournalItem
        from apps.accounting.models.journal import Journal

        journal = Journal.objects.create(
            company=self.company,
            code="GEN",
            name="General Journal",
            type="general",
        )

        seed_entry = JournalEntry.objects.create(
            company=self.company,
            journal=journal,
            date="2026-01-01",
            reference="OPEN",
            status="draft",
        )

        JournalItem.objects.create(
            entry=seed_entry,
            account=self.cash_account,
            description="Opening cash",
            debit=Decimal("1000.00"),
            credit=Decimal("0.00"),
        )

        equity_account = Account.objects.create(
            company=self.company,
            code="3001",
            name="Owner Equity",
            account_type="equity",
            normal_balance="credit",
            is_postable=True,
        )

        JournalItem.objects.create(
            entry=seed_entry,
            account=equity_account,
            description="Opening equity",
            debit=Decimal("0.00"),
            credit=Decimal("1000.00"),
        )

        seed_entry.post()

        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.supplier,
            payment_type="outbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("300.00"),
            status="draft",
        )

        entry = PaymentService.post_payment(payment)

        payment.refresh_from_db()
        entry.refresh_from_db()

        self.assertEqual(payment.status, "posted")
        self.assertEqual(entry.status, "posted")

        items = entry.items.order_by("id")
        self.assertEqual(items.count(), 2)

        supplier_line = items.filter(account=self.payable_account).first()
        cash_line = items.filter(account=self.cash_account).first()

        self.assertEqual(supplier_line.debit, Decimal("300.00"))
        self.assertEqual(supplier_line.partner, self.supplier)
        self.assertEqual(cash_line.credit, Decimal("300.00"))
        self.assertIsNone(cash_line.partner)

    def test_cannot_post_non_draft_payment(self):
        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("200.00"),
            status="posted",
        )

        with self.assertRaises(ValidationError):
            PaymentService.post_payment(payment)

    def test_post_inbound_payment_with_standard_coa_does_not_fail_reconciliation(self):
        company = Company.objects.create(name="Standard COA Company")
        branch = Branch.objects.create(company=company, name="Main Branch")
        customer = Partner.objects.create(
            company=company,
            partner_type="customer",
            name="Standard Customer",
        )
        accounts = seed_standard_chart_of_accounts(company)

        payment = Payment.objects.create(
            company=company,
            branch=branch,
            partner=customer,
            payment_type="inbound",
            payment_method="cash",
            account=accounts["1002"],
            amount=Decimal("150.00"),
            status="draft",
        )

        entry = PaymentService.post_payment(payment)

        cash_line = entry.items.get(account=accounts["1002"])
        receivable_line = entry.items.get(account=accounts["1003"])

        self.assertIsNone(cash_line.partner)
        self.assertEqual(receivable_line.partner, customer)
        self.assertEqual(receivable_line.credit, Decimal("150.00"))

    def test_post_outbound_payment_with_standard_coa_does_not_fail_reconciliation(self):
        from apps.accounting.models.entry import JournalEntry, JournalItem
        from apps.accounting.models.journal import Journal

        company = Company.objects.create(name="Standard COA Outbound Company")
        branch = Branch.objects.create(company=company, name="Main Branch")
        supplier = Partner.objects.create(
            company=company,
            partner_type="supplier",
            name="Standard Supplier",
        )
        accounts = seed_standard_chart_of_accounts(company)

        journal = Journal.objects.create(
            company=company,
            code="GEN",
            name="General Journal",
            type="general",
        )
        seed_entry = JournalEntry.objects.create(
            company=company,
            journal=journal,
            date="2026-01-01",
            reference="OPEN",
            status="draft",
        )
        JournalItem.objects.create(
            entry=seed_entry,
            account=accounts["1002"],
            description="Opening cash",
            debit=Decimal("500.00"),
            credit=Decimal("0.00"),
        )
        JournalItem.objects.create(
            entry=seed_entry,
            account=accounts["3001"],
            description="Opening equity",
            debit=Decimal("0.00"),
            credit=Decimal("500.00"),
        )
        seed_entry.post()

        payment = Payment.objects.create(
            company=company,
            branch=branch,
            partner=supplier,
            payment_type="outbound",
            payment_method="cash",
            account=accounts["1002"],
            amount=Decimal("125.00"),
            status="draft",
        )

        entry = PaymentService.post_payment(payment)

        payable_line = entry.items.get(account=accounts["2001"])
        cash_line = entry.items.get(account=accounts["1002"])

        self.assertEqual(payable_line.partner, supplier)
        self.assertEqual(payable_line.debit, Decimal("125.00"))
        self.assertIsNone(cash_line.partner)
