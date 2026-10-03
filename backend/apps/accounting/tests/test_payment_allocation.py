from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models import Account, Payment, PaymentAllocation
from apps.accounting.services.payment_allocation_service import PaymentAllocationService
from apps.accounting.services.payment_service import PaymentService
from apps.core.models.company import Branch, Company
from apps.inventory.models import Warehouse
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User
from apps.users.roles import ROLE_ACCOUNTANT, ROLE_ACCOUNTING_MANAGER, ROLE_AUDITOR, assign_role


class AllocationFixtureMixin:
    def create_fixture(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_branch = Branch.objects.create(company=self.company, name="Second Branch")
        self.other_company = Company.objects.create(name="Other Company")
        self.other_company_branch = Branch.objects.create(company=self.other_company, name="Other")

        self.cash = Account.objects.get(company=self.company, code="1002", is_deleted=False)
        self.warehouse = Warehouse.objects.create(
            company=self.company, branch=self.branch, name="Main Warehouse"
        )

        self.customer = self.partner("Customer A", "customer")
        self.other_customer = self.partner("Customer B", "customer")
        self.supplier = self.partner("Supplier A", "supplier")
        self.foreign_customer = self.partner("Foreign", "customer", company=self.other_company)

    def partner(self, name, partner_type, company=None):
        return Partner.objects.create(
            company=company or self.company, partner_type=partner_type, name=name
        )

    def posted_payment(self, partner, amount, payment_type="inbound", branch=None):
        if payment_type == "outbound":
            # Outbound payments need enough cash on hand.
            self.posted_payment(self.partner("Cash Funder", "customer"), amount)

        payment = Payment.objects.create(
            company=self.company,
            branch=branch or self.branch,
            partner=partner,
            payment_type=payment_type,
            payment_method="cash",
            account=self.cash,
            amount=Decimal(amount),
        )
        PaymentService.post_payment(payment)
        payment.refresh_from_db()
        return payment

    def sales_invoice(self, total, customer=None, status="posted", company=None, branch=None):
        return SalesInvoice.objects.create(
            company=company or self.company,
            branch=branch or self.branch,
            customer=customer or self.customer,
            status=status,
            total_amount=Decimal(total),
        )

    def purchase_invoice(self, total, supplier=None, status="posted"):
        return PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=supplier or self.supplier,
            warehouse=self.warehouse,
            status=status,
            total_amount=Decimal(total),
        )


class PaymentAllocationServiceTestCase(AllocationFixtureMixin, TestCase):
    def setUp(self):
        self.create_fixture()

    def allocate(self, payment, invoice, amount, invoice_type="sales", **kwargs):
        return PaymentAllocationService.allocate_payment(
            payment.pk, invoice.pk, invoice_type, amount, **kwargs
        )

    def assertAllocationError(self, payment, invoice, amount, message, invoice_type="sales", **kwargs):
        with self.assertRaises(ValidationError) as ctx:
            self.allocate(payment, invoice, amount, invoice_type, **kwargs)
        self.assertIn(message, str(ctx.exception))

    # --- success ----------------------------------------------------------

    def test_partial_allocation_updates_invoice_and_payment_balances(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")

        allocation = self.allocate(payment, invoice, "200.00")

        invoice.refresh_from_db()
        self.assertEqual(allocation.invoice, invoice)
        self.assertEqual(allocation.amount, Decimal("200.00"))
        self.assertEqual(invoice.amount_paid, Decimal("200.00"))
        self.assertEqual(invoice.amount_due, Decimal("100.00"))
        self.assertEqual(invoice.payment_status, "partially_paid")
        self.assertEqual(payment.allocated_amount, Decimal("200.00"))
        self.assertEqual(payment.unallocated_amount, Decimal("300.00"))

    def test_invoice_becomes_paid_across_allocations_and_keeps_posted_status(self):
        first = self.posted_payment(self.customer, "100.00")
        second = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")

        self.allocate(first, invoice, "100.00")
        self.allocate(second, invoice, "200.00")

        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal("300.00"))
        self.assertEqual(invoice.amount_due, Decimal("0.00"))
        self.assertEqual(invoice.payment_status, "paid")
        self.assertEqual(invoice.status, "posted")

    def test_outbound_payment_allocates_to_purchase_invoice(self):
        payment = self.posted_payment(self.supplier, "400.00", payment_type="outbound")
        invoice = self.purchase_invoice("400.00")

        self.allocate(payment, invoice, "400.00", invoice_type="purchase")

        invoice.refresh_from_db()
        self.assertEqual(invoice.payment_status, "paid")

    # --- over-allocation ----------------------------------------------------

    def test_amount_cannot_exceed_payment_unallocated_balance(self):
        payment = self.posted_payment(self.customer, "250.00")
        first_invoice = self.sales_invoice("200.00")
        second_invoice = self.sales_invoice("200.00")
        self.allocate(payment, first_invoice, "200.00")

        self.assertAllocationError(payment, second_invoice, "100.00", "unallocated balance (50.00)")

        second_invoice.refresh_from_db()
        self.assertEqual(second_invoice.amount_paid, Decimal("0.00"))

    def test_amount_cannot_exceed_invoice_outstanding_balance(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")
        self.allocate(payment, invoice, "250.00")

        self.assertAllocationError(payment, invoice, "100.00", "outstanding balance (50.00)")

    def test_invalid_amounts_are_rejected(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")

        for amount in ("0", "-5", "10.005", "abc"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValidationError):
                    self.allocate(payment, invoice, amount)

    # --- mismatches -----------------------------------------------------------

    def test_partner_must_match(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00", customer=self.other_customer)

        self.assertAllocationError(payment, invoice, "100.00", "same partner")
        self.assertFalse(PaymentAllocation.objects.exists())

    def test_company_must_match(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice(
            "300.00",
            customer=self.foreign_customer,
            company=self.other_company,
            branch=self.other_company_branch,
        )

        self.assertAllocationError(payment, invoice, "100.00", "same company")
        self.assertAllocationError(payment, invoice, "100.00", "Invoice not found", company=self.company)

    def test_payment_direction_must_match_invoice_type(self):
        both = self.partner("Customer and Supplier", "both")
        outbound = self.posted_payment(both, "500.00", payment_type="outbound")
        invoice = self.sales_invoice("300.00", customer=both)

        self.assertAllocationError(outbound, invoice, "100.00", "inbound payments")

    def test_payment_and_invoice_must_be_posted(self):
        payment = self.posted_payment(self.customer, "500.00")
        draft_invoice = self.sales_invoice("300.00", status="draft")
        draft_payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash,
            amount=Decimal("100.00"),
        )

        self.assertAllocationError(payment, draft_invoice, "100.00", "posted invoices")
        self.assertAllocationError(draft_payment, self.sales_invoice("50.00"), "10.00", "posted payments")

    def test_branch_scope_hides_other_branch_invoices(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00", branch=self.other_branch)

        self.assertAllocationError(payment, invoice, "100.00", "Invoice not found", branch=self.branch)

    # --- cancellation -----------------------------------------------------------

    def test_cancelling_payment_releases_its_allocations(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")
        self.allocate(payment, invoice, "300.00")

        PaymentService.cancel_payment(payment, reason="Bounced cheque")

        invoice.refresh_from_db()
        self.assertEqual(invoice.amount_paid, Decimal("0.00"))
        self.assertEqual(invoice.payment_status, "unpaid")
        self.assertFalse(PaymentAllocation.objects.exists())
        self.assertTrue(PaymentAllocation.all_objects.filter(is_deleted=True).exists())

    def test_releasing_invoice_frees_payment_balance(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")
        self.allocate(payment, invoice, "300.00")

        PaymentAllocationService.release_for_invoice(invoice)

        self.assertEqual(invoice.amount_paid, Decimal("0.00"))
        self.assertEqual(payment.allocated_amount, Decimal("0.00"))


class PaymentAllocationAPITestCase(AllocationFixtureMixin, APITestCase):
    def setUp(self):
        self.create_fixture()
        self.user = User.objects.create_user(
            email="manager@example.com",
            password="password",
            full_name="Manager",
            company=self.company,
            branch=self.branch,
        )
        assign_role(self.user, ROLE_ACCOUNTING_MANAGER)
        self.client.force_authenticate(self.user)

    def allocate_url(self, payment):
        return f"/api/accounting/payments/{payment.pk}/allocate/"

    def test_allocate_returns_allocation_and_updates_balances(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00")

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": str(invoice.pk), "invoice_type": "sales", "amount": "120.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["invoice_type"], "sales")
        self.assertEqual(response.data["invoice_id"], str(invoice.pk))
        self.assertEqual(response.data["invoice_number"], invoice.invoice_number)
        self.assertEqual(response.data["amount"], "120.00")
        self.assertEqual(response.data["invoice_amount_due"], "180.00")
        self.assertEqual(response.data["invoice_payment_status"], "partially_paid")
        self.assertEqual(response.data["payment_unallocated_amount"], "380.00")

        detail = self.client.get(f"/api/accounting/payments/{payment.pk}/")
        self.assertEqual(detail.data["allocated_amount"], "120.00")
        self.assertEqual(detail.data["unallocated_amount"], "380.00")

        invoice_detail = self.client.get(f"/api/sales/invoices/{invoice.pk}/")
        self.assertEqual(invoice_detail.data["amount_paid"], "120.00")
        self.assertEqual(invoice_detail.data["payment_status"], "partially_paid")

    def test_over_allocation_returns_400(self):
        payment = self.posted_payment(self.customer, "100.00")
        invoice = self.sales_invoice("300.00")

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": str(invoice.pk), "invoice_type": "sales", "amount": "150.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_partner_mismatch_returns_400(self):
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00", customer=self.other_customer)

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": str(invoice.pk), "invoice_type": "sales", "amount": "100.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("same partner", str(response.data))

    def test_invalid_payload_returns_400(self):
        payment = self.posted_payment(self.customer, "500.00")

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": "not-a-uuid", "invoice_type": "rent", "amount": "0"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(response.data), {"invoice_id", "invoice_type", "amount"})

    def test_role_without_allocate_permission_is_forbidden(self):
        auditor = User.objects.create_user(
            email="auditor@example.com", password="password", full_name="Auditor", company=self.company
        )
        assign_role(auditor, ROLE_AUDITOR)
        self.client.force_authenticate(auditor)
        payment = self.posted_payment(self.customer, "500.00")

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": str(self.sales_invoice("100.00").pk), "invoice_type": "sales", "amount": "10.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_branch_accountant_cannot_allocate_to_other_branch_invoice(self):
        accountant = User.objects.create_user(
            email="accountant@example.com",
            password="password",
            full_name="Accountant",
            company=self.company,
            branch=self.branch,
        )
        assign_role(accountant, ROLE_ACCOUNTANT)
        self.client.force_authenticate(accountant)
        payment = self.posted_payment(self.customer, "500.00")
        invoice = self.sales_invoice("300.00", branch=self.other_branch)

        response = self.client.post(
            self.allocate_url(payment),
            {"invoice_id": str(invoice.pk), "invoice_type": "sales", "amount": "100.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invoice_id", response.data)
