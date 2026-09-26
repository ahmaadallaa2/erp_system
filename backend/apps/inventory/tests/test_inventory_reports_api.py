from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models.company import Branch, Company
from apps.inventory.models import (
    Category,
    Product,
    StockBalance,
    StockMovement,
    StockTransaction,
    Unit,
    Warehouse,
)
from apps.users.models import User


class ProductMovementHistoryReportAPITestCase(APITestCase):
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

        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.category = Category.objects.create(company=self.company, name="Main")
        self.other_category = Category.objects.create(
            company=self.other_company,
            name="Other",
        )

        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product A",
            product_type="storable",
        )
        self.product_b = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product B",
            product_type="storable",
        )
        self.other_product = Product.objects.create(
            company=self.other_company,
            category=self.other_category,
            unit=self.unit,
            name="Other Product",
            product_type="storable",
        )

        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )
        self.destination_warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Destination Warehouse",
        )
        self.other_warehouse = Warehouse.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            name="Other Warehouse",
        )

        self.url = "/api/inventory/reports/product-movements/"

    def test_authentication_is_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_returns_posted_company_movements_only(self):
        self.client.force_authenticate(self.user)
        posted_tx = self.create_transaction(
            transaction_type="IN",
            status="posted",
            product=self.product,
            warehouse=self.warehouse,
            date="2026-05-10",
            reference="PINV-00001",
            quantity=Decimal("5.00"),
            unit_cost=Decimal("12.00"),
        )
        self.create_transaction(
            transaction_type="IN",
            status="draft",
            product=self.product,
            warehouse=self.warehouse,
            date="2026-05-10",
            reference="DRAFT",
            quantity=Decimal("99.00"),
            unit_cost=Decimal("1.00"),
        )
        self.create_other_company_transaction()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        row = response.data[0]
        self.assertEqual(row["transaction_id"], str(posted_tx.id))
        self.assertEqual(row["transaction_number"], posted_tx.code)
        self.assertEqual(row["reference"], "PINV-00001")
        self.assertEqual(row["transaction_type"], "IN")
        self.assertEqual(row["product_id"], str(self.product.id))
        self.assertEqual(row["product_name"], "Product A")
        self.assertEqual(row["warehouse_id"], str(self.warehouse.id))
        self.assertEqual(row["warehouse_name"], "Main Warehouse")
        self.assertEqual(row["quantity_in"], "5.00")
        self.assertEqual(row["quantity_out"], "0.00")
        self.assertEqual(row["unit_cost"], "12.00")
        self.assertEqual(row["notes"], "Report test movement")

    def test_product_date_and_transaction_type_filters_are_applied(self):
        self.client.force_authenticate(self.user)
        self.create_transaction(
            transaction_type="IN",
            status="posted",
            product=self.product,
            warehouse=self.warehouse,
            date="2026-05-09",
            reference="BEFORE",
            quantity=Decimal("4.00"),
            unit_cost=Decimal("10.00"),
        )
        included_tx = self.create_transaction(
            transaction_type="OUT",
            status="posted",
            product=self.product,
            warehouse=self.warehouse,
            date="2026-05-10",
            reference="SINV-00001",
            quantity=Decimal("2.00"),
            unit_cost=Decimal("10.00"),
        )
        self.create_transaction(
            transaction_type="OUT",
            status="posted",
            product=self.product_b,
            warehouse=self.warehouse,
            date="2026-05-10",
            reference="OTHER-PRODUCT",
            quantity=Decimal("3.00"),
            unit_cost=Decimal("10.00"),
        )

        response = self.client.get(
            self.url,
            {
                "product": str(self.product.id),
                "start_date": "2026-05-10",
                "end_date": "2026-05-10",
                "transaction_type": "OUT",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["transaction_id"], str(included_tx.id))
        self.assertEqual(response.data[0]["quantity_in"], "0.00")
        self.assertEqual(response.data[0]["quantity_out"], "2.00")

    def test_warehouse_filter_for_transfer_returns_matching_side_only(self):
        self.client.force_authenticate(self.user)
        transfer_tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="TRANSFER",
            source_warehouse=self.warehouse,
            destination_warehouse=self.destination_warehouse,
            date="2026-05-11",
            reference="TRF-REF",
            status="posted",
        )
        StockMovement.objects.create(
            transaction=transfer_tx,
            product=self.product,
            quantity=Decimal("3.00"),
            unit_cost=Decimal("7.00"),
            note="Transfer movement",
        )

        response = self.client.get(
            self.url,
            {"warehouse": str(self.destination_warehouse.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["warehouse_id"], str(self.destination_warehouse.id))
        self.assertEqual(response.data[0]["quantity_in"], "3.00")
        self.assertEqual(response.data[0]["quantity_out"], "0.00")

    def test_transfer_without_warehouse_filter_returns_in_and_out_rows(self):
        self.client.force_authenticate(self.user)
        transfer_tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="TRANSFER",
            source_warehouse=self.warehouse,
            destination_warehouse=self.destination_warehouse,
            date="2026-05-11",
            reference="TRF-REF",
            status="posted",
        )
        StockMovement.objects.create(
            transaction=transfer_tx,
            product=self.product,
            quantity=Decimal("3.00"),
            unit_cost=Decimal("7.00"),
            note="Transfer movement",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        quantities = {
            (row["warehouse_name"], row["quantity_in"], row["quantity_out"])
            for row in response.data
        }
        self.assertIn(("Main Warehouse", "0.00", "3.00"), quantities)
        self.assertIn(("Destination Warehouse", "3.00", "0.00"), quantities)

    def test_another_company_filter_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {"product": str(self.other_product.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_range_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {
                "start_date": "2026-05-11",
                "end_date": "2026-05-10",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def create_transaction(
        self,
        transaction_type,
        status,
        product,
        warehouse,
        date,
        reference,
        quantity,
        unit_cost,
    ):
        transaction = StockTransaction.objects.create(
            company=product.company,
            transaction_type=transaction_type,
            source_warehouse=warehouse,
            date=date,
            reference=reference,
            status=status,
            notes="Report test transaction",
        )
        StockMovement.objects.create(
            transaction=transaction,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost,
            note="Report test movement",
        )
        return transaction

    def create_other_company_transaction(self):
        return self.create_transaction(
            transaction_type="IN",
            status="posted",
            product=self.other_product,
            warehouse=self.other_warehouse,
            date="2026-05-10",
            reference="OTHER",
            quantity=Decimal("8.00"),
            unit_cost=Decimal("3.00"),
        )


class WarehouseBalanceReportAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_company = Company.objects.create(name="Other Company")
        self.other_branch = Branch.objects.create(
            company=self.other_company,
            name="Other Branch",
        )

        self.user = User.objects.create_user(
            email="warehouse@example.com",
            password="password",
            full_name="Warehouse User",
            company=self.company,
            branch=self.branch,
        )

        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.category = Category.objects.create(company=self.company, name="Main")
        self.other_category = Category.objects.create(
            company=self.other_company,
            name="Other",
        )

        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product A",
            sku="PROD-A",
            product_type="storable",
            average_cost=Decimal("10.00"),
        )
        self.product_b = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product B",
            sku="PROD-B",
            product_type="storable",
            average_cost=Decimal("7.50"),
        )
        self.other_product = Product.objects.create(
            company=self.other_company,
            category=self.other_category,
            unit=self.unit,
            name="Other Product",
            sku="OTHER",
            product_type="storable",
            average_cost=Decimal("99.00"),
        )

        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )
        self.warehouse_b = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Secondary Warehouse",
        )
        self.other_warehouse = Warehouse.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            name="Other Warehouse",
        )

        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("5.00"),
            reorder_point=Decimal("10.00"),
        )
        StockBalance.objects.create(
            company=self.company,
            product=self.product_b,
            warehouse=self.warehouse_b,
            quantity=Decimal("20.00"),
            reorder_point=Decimal("5.00"),
        )
        StockBalance.objects.create(
            company=self.other_company,
            product=self.other_product,
            warehouse=self.other_warehouse,
            quantity=Decimal("99.00"),
            reorder_point=Decimal("100.00"),
        )

        self.url = "/api/inventory/reports/warehouse-balances/"

    def test_authentication_is_required(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_report_returns_company_stock_balances_with_estimated_value(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        row = next(item for item in response.data if item["product_code"] == "PROD-A")
        self.assertEqual(row["warehouse_id"], str(self.warehouse.id))
        self.assertEqual(row["warehouse_name"], "Main Warehouse")
        self.assertEqual(row["product_id"], str(self.product.id))
        self.assertEqual(row["product_name"], "Product A")
        self.assertEqual(row["quantity"], "5.00")
        self.assertEqual(row["reorder_point"], "10.00")
        self.assertTrue(row["is_low_stock"])
        self.assertEqual(row["average_cost"], "10.00")
        self.assertEqual(row["estimated_value"], "50.00")

        product_codes = {item["product_code"] for item in response.data}
        self.assertNotIn("OTHER", product_codes)

    def test_warehouse_product_and_low_stock_filters_are_applied(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {
                "warehouse": str(self.warehouse.id),
                "product": str(self.product.id),
                "low_stock": "true",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_code"], "PROD-A")
        self.assertTrue(response.data[0]["is_low_stock"])

    def test_low_stock_false_returns_non_low_stock_rows(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url, {"low_stock": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_code"], "PROD-B")
        self.assertFalse(response.data[0]["is_low_stock"])

    def test_another_company_filter_is_rejected(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            self.url,
            {"warehouse": str(self.other_warehouse.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
