from decimal import Decimal

from django.test import TestCase

from apps.core.models.company import Company, Branch
from apps.accounting.models.account import Account
from apps.inventory.models import Category, Unit, Product, Warehouse
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.purchases.models.purchase_invoice_item import PurchaseInvoiceItem
from apps.sales.models.sales_invoice import SalesInvoice
from apps.sales.models.sales_invoice_item import SalesInvoiceItem
from apps.accounting.services.accounting_service import AccountingService


class AccountingServiceTestCase(TestCase):
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

        self.asset_customer = Account.objects.create(
            company=self.company,
            code="1003",
            name="Customers",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            allow_reconciliation=True,
        )

        self.asset_inventory = Account.objects.create(
            company=self.company,
            code="1004",
            name="Inventory",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )

        self.asset_cash = Account.objects.create(
            company=self.company,
            code="1002",
            name="Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )

        self.liability_supplier = Account.objects.create(
            company=self.company,
            code="2001",
            name="Suppliers",
            account_type="liability",
            normal_balance="credit",
            is_postable=True,
            allow_reconciliation=True,
        )

        self.income_sales = Account.objects.create(
            company=self.company,
            code="4001",
            name="Sales Revenue",
            account_type="income",
            normal_balance="credit",
            is_postable=True,
        )

        self.expense_purchase = Account.objects.create(
            company=self.company,
            code="5001",
            name="Cost of Goods Sold",
            account_type="expense",
            normal_balance="debit",
            is_postable=True,
        )

        self.category = Category.objects.create(company=self.company, name="Electronics")
        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse"
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
            income_account=self.income_sales,
            expense_account=self.expense_purchase,
        )

    def test_create_sales_invoice_entry(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )

        SalesInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("150.00"),
        )

        invoice.refresh_from_db()
        entry = AccountingService.create_sales_invoice_entry(invoice)

        entry.refresh_from_db()
        self.assertEqual(entry.status, "posted")
        self.assertEqual(entry.company, self.company)

        items = entry.items.order_by("id")
        self.assertEqual(items.count(), 4)

        total_debit = sum((item.debit for item in items), Decimal("0.00"))
        total_credit = sum((item.credit for item in items), Decimal("0.00"))

        self.assertEqual(total_debit, Decimal("500.00"))
        self.assertEqual(total_credit, Decimal("500.00"))

        receivable_line = items.filter(account=self.asset_customer).first()
        revenue_line = items.filter(account=self.income_sales).first()
        cogs_line = items.filter(account=self.expense_purchase).first()
        inventory_line = items.filter(account=self.asset_inventory).first()

        self.assertIsNotNone(receivable_line)
        self.assertIsNotNone(revenue_line)
        self.assertIsNotNone(cogs_line)
        self.assertIsNotNone(inventory_line)
        self.assertEqual(receivable_line.partner, self.customer)
        self.assertEqual(receivable_line.debit, Decimal("300.00"))
        self.assertEqual(revenue_line.credit, Decimal("300.00"))
        self.assertEqual(cogs_line.debit, Decimal("200.00"))
        self.assertEqual(inventory_line.credit, Decimal("200.00"))

    def test_create_purchase_invoice_entry(self):
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="draft",
            shipping_cost=Decimal("20.00"),
            clearance_cost=Decimal("10.00"),
            commission_percentage=Decimal("5.00"),
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
        )

        invoice.refresh_from_db()
        entry = AccountingService.create_purchase_invoice_entry(invoice)

        entry.refresh_from_db()
        self.assertEqual(entry.status, "posted")
        self.assertEqual(entry.company, self.company)

        items = entry.items.order_by("id")
        self.assertEqual(items.count(), 3)

        total_debit = sum((item.debit for item in items), Decimal("0.00"))
        total_credit = sum((item.credit for item in items), Decimal("0.00"))

        inventory_line = items.filter(account=self.asset_inventory).first()
        payable_line = items.filter(account=self.liability_supplier).first()
        expense_line = items.filter(account=self.asset_cash).first()

        self.assertIsNotNone(inventory_line)
        self.assertIsNotNone(payable_line)
        self.assertIsNotNone(expense_line)

        # قيمة البضاعة فقط = 200.00
        # الشحن + التخليص = 30.00
        # العمولة = 5% من قيمة البضاعة = 10.00
        # إجمالي تحميل المخزون = 240.00
        self.assertEqual(total_debit, Decimal("240.00"))
        self.assertEqual(total_credit, Decimal("240.00"))

        self.assertEqual(inventory_line.debit, Decimal("240.00"))
        self.assertEqual(payable_line.credit, Decimal("200.00"))
        self.assertEqual(expense_line.credit, Decimal("40.00"))
        self.assertEqual(payable_line.partner, self.supplier)
