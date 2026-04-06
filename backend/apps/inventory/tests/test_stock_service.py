from decimal import Decimal

from django.test import TestCase

from apps.core.models.company import Company, Branch
from apps.inventory.models import (
    Category,
    Unit,
    Product,
    Warehouse,
    StockBalance,
    StockTransaction,
)
from apps.inventory.services.stock_service import StockService


class StockServiceTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(
            company=self.company,
            name="Main Branch"
        )

        self.category = Category.objects.create(
            company=self.company,
            name="Electronics"
        )

        self.unit = Unit.objects.create(
            name="Piece",
            short_name="PCS"
        )

        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Laptop",
            product_type="storable",
            average_cost=Decimal("100.00"),
            cost_price=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )

        self.warehouse_1 = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse"
        )

        self.warehouse_2 = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Showroom Warehouse",
            warehouse_type="sub"
        )

    def test_post_in_transaction_increases_stock_and_updates_average_cost(self):
        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse_1,
        )

        StockService.create_movement(
            transaction_obj=tx,
            product=self.product,
            quantity=Decimal("10.00"),
            unit_cost=Decimal("120.00"),
        )

        StockService.post_transaction(tx)

        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_1
        )

        self.product.refresh_from_db()
        tx.refresh_from_db()

        self.assertEqual(tx.status, "posted")
        self.assertEqual(balance.quantity, Decimal("10.00"))
        self.assertEqual(self.product.average_cost, Decimal("120.00"))

    def test_post_out_transaction_decreases_stock(self):
        balance = StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_1,
            quantity=Decimal("10.00"),
            reserved_quantity=Decimal("0.00"),
        )

        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="OUT",
            source_warehouse=self.warehouse_1,
        )

        StockService.create_movement(
            transaction_obj=tx,
            product=self.product,
            quantity=Decimal("4.00"),
            unit_cost=self.product.average_cost,
        )

        StockService.post_transaction(tx)

        balance.refresh_from_db()
        tx.refresh_from_db()

        self.assertEqual(tx.status, "posted")
        self.assertEqual(balance.quantity, Decimal("6.00"))

    def test_post_out_transaction_fails_when_stock_not_enough(self):
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_1,
            quantity=Decimal("2.00"),
            reserved_quantity=Decimal("0.00"),
        )

        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="OUT",
            source_warehouse=self.warehouse_1,
        )

        StockService.create_movement(
            transaction_obj=tx,
            product=self.product,
            quantity=Decimal("5.00"),
            unit_cost=self.product.average_cost,
        )

        with self.assertRaises(ValueError):
            StockService.post_transaction(tx)

    def test_transfer_moves_stock_between_warehouses(self):
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_1,
            quantity=Decimal("8.00"),
            reserved_quantity=Decimal("0.00"),
        )

        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="TRANSFER",
            source_warehouse=self.warehouse_1,
            destination_warehouse=self.warehouse_2,
        )

        StockService.create_movement(
            transaction_obj=tx,
            product=self.product,
            quantity=Decimal("3.00"),
            unit_cost=self.product.average_cost,
        )

        StockService.post_transaction(tx)

        source_balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_1,
        )
        dest_balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse_2,
        )

        self.assertEqual(source_balance.quantity, Decimal("5.00"))
        self.assertEqual(dest_balance.quantity, Decimal("3.00"))

    def test_cannot_post_empty_transaction(self):
        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse_1,
        )

        with self.assertRaises(ValueError):
            StockService.post_transaction(tx)

    def test_cannot_post_non_draft_transaction(self):
        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse_1,
            status="posted",
        )

        with self.assertRaises(ValueError):
            StockService.post_transaction(tx)