from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models.company import Branch, Company
from apps.inventory.models import Category, Product, StockTransaction, Unit, Warehouse
from apps.users.models import User


class StockMovementAPITestCase(APITestCase):
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
        self.other_warehouse = Warehouse.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            name="Other Warehouse",
        )

        self.transaction = StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse,
            status="draft",
        )
        self.other_transaction = StockTransaction.objects.create(
            company=self.other_company,
            transaction_type="IN",
            source_warehouse=self.other_warehouse,
            status="draft",
        )

        self.url = "/api/inventory/stock-movements/"

    def test_authenticated_user_can_create_movement_for_own_company_transaction(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {
                "transaction": str(self.transaction.id),
                "product": str(self.product.id),
                "quantity": "2.00",
                "unit_cost": "10.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["transaction"]), str(self.transaction.id))
        self.assertEqual(str(response.data["product"]), str(self.product.id))

    def test_user_cannot_create_movement_for_another_company_transaction(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {
                "transaction": str(self.other_transaction.id),
                "product": str(self.other_product.id),
                "quantity": "2.00",
                "unit_cost": "10.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_create_movement_with_another_company_product(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            self.url,
            {
                "transaction": str(self.transaction.id),
                "product": str(self.other_product.id),
                "quantity": "2.00",
                "unit_cost": "10.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_create_stock_movement(self):
        response = self.client.post(
            self.url,
            {
                "transaction": str(self.transaction.id),
                "product": str(self.product.id),
                "quantity": "2.00",
                "unit_cost": "10.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
