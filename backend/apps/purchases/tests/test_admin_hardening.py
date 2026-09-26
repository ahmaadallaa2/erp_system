from decimal import Decimal

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.core.models.company import Branch, Company
from apps.inventory.models import Category, Product, Unit, Warehouse
from apps.partners.models import Partner
from apps.purchases.admin.purchase_invoice_admin import (
    PurchaseInvoiceAdmin,
    PurchaseInvoiceItemInline,
)
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.users.models import User


class PurchaseInvoiceAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/")
        self.request.user = User.objects.create_superuser(
            email="purchase-admin@example.com",
            password="testpass123",
            full_name="Purchase Admin",
        )
        self.model_admin = PurchaseInvoiceAdmin(PurchaseInvoice, admin.site)
        self.inline_admin = PurchaseInvoiceItemInline(PurchaseInvoice, admin.site)

        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.category = Category.objects.create(company=self.company, name="Electronics")
        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Laptop",
            product_type="storable",
            cost_price=Decimal("100.00"),
            average_cost=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )
        self.supplier = Partner.objects.create(
            company=self.company,
            partner_type="supplier",
            name="Supplier A",
        )

    def create_invoice(self, status="draft"):
        return PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status=status,
        )

    def test_posted_and_cancelled_invoice_cannot_be_changed_or_deleted(self):
        posted_invoice = self.create_invoice(status="posted")
        cancelled_invoice = self.create_invoice(status="cancelled")

        self.assertFalse(self.model_admin.has_change_permission(self.request, posted_invoice))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, posted_invoice))
        self.assertFalse(self.model_admin.has_change_permission(self.request, cancelled_invoice))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, cancelled_invoice))

    def test_status_is_readonly_and_bulk_delete_is_disabled(self):
        readonly_fields = self.model_admin.get_readonly_fields(self.request)
        actions = self.model_admin.get_actions(self.request)

        self.assertIn("status", readonly_fields)
        self.assertIn("posted_by", readonly_fields)
        self.assertIn("posted_at", readonly_fields)
        self.assertIn("cancelled_by", readonly_fields)
        self.assertIn("cancelled_at", readonly_fields)
        self.assertIn("cancellation_reason", readonly_fields)
        self.assertNotIn("delete_selected", actions)

    def test_posted_and_cancelled_item_inlines_are_locked(self):
        posted_invoice = self.create_invoice(status="posted")
        cancelled_invoice = self.create_invoice(status="cancelled")

        for invoice in (posted_invoice, cancelled_invoice):
            self.assertFalse(self.inline_admin.has_add_permission(self.request, invoice))
            self.assertFalse(self.inline_admin.has_change_permission(self.request, invoice))
            self.assertFalse(self.inline_admin.has_delete_permission(self.request, invoice))
