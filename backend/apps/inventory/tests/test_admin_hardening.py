from decimal import Decimal

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.core.models.company import Branch, Company
from apps.inventory.admin import StockMovementInline, StockTransactionAdmin
from apps.inventory.models import Category, Product, StockTransaction, Unit, Warehouse
from apps.users.models import User


class StockTransactionAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/")
        self.request.user = User.objects.create_superuser(
            email="inventory-admin@example.com",
            password="testpass123",
            full_name="Inventory Admin",
        )
        self.model_admin = StockTransactionAdmin(StockTransaction, admin.site)
        self.inline_admin = StockMovementInline(StockTransaction, admin.site)

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

    def create_transaction(self, status="draft"):
        return StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse,
            status=status,
        )

    def test_posted_and_cancelled_transactions_cannot_be_changed_or_deleted(self):
        posted_tx = self.create_transaction(status="posted")
        cancelled_tx = self.create_transaction(status="cancelled")

        self.assertFalse(self.model_admin.has_change_permission(self.request, posted_tx))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, posted_tx))
        self.assertFalse(self.model_admin.has_change_permission(self.request, cancelled_tx))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, cancelled_tx))

    def test_posted_and_cancelled_movement_inlines_are_locked(self):
        posted_tx = self.create_transaction(status="posted")
        cancelled_tx = self.create_transaction(status="cancelled")

        for tx in (posted_tx, cancelled_tx):
            self.assertFalse(self.inline_admin.has_add_permission(self.request, tx))
            self.assertFalse(self.inline_admin.has_change_permission(self.request, tx))
            self.assertFalse(self.inline_admin.has_delete_permission(self.request, tx))

    def test_status_is_readonly_and_bulk_delete_is_disabled(self):
        readonly_fields = self.model_admin.get_readonly_fields(self.request)
        actions = self.model_admin.get_actions(self.request)

        self.assertIn("status", readonly_fields)
        self.assertNotIn("delete_selected", actions)
