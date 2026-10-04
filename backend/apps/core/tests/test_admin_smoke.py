import datetime
from decimal import Decimal

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounting.models import Account, Payment
from apps.accounting.services.payment_allocation_service import PaymentAllocationService
from apps.accounting.services.payment_service import PaymentService
from apps.core.models import Attachment, Branch, Company, FiscalYear, SystemSetting
from apps.inventory.models import Category, Product, StockMovement, StockTransaction, Unit, Warehouse
from apps.partners.models import Partner
from apps.purchases.models import PurchaseInvoice, PurchaseInvoiceItem
from apps.purchases.services import PurchaseService
from apps.sales.models import SalesInvoice, SalesInvoiceItem
from apps.sales.services import SalesService
from apps.users.models import User


# Manifest static storage needs collectstatic output, which tests don't have.
@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AdminSmokeTestCase(TestCase):
    """Every registered admin page renders for a superuser with real data."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            email="smoke-admin@example.com",
            password="testpass123",
            full_name="Smoke Admin",
        )
        company = Company.objects.create(name="Smoke Company")
        branch = Branch.objects.create(company=company, name="Main Branch")
        FiscalYear.objects.create(
            company=company,
            name="FY2026",
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 12, 31),
            is_active=True,
        )
        SystemSetting.get_settings()

        unit = Unit.objects.create(name="Piece", short_name="PCS")
        category = Category.objects.create(company=company, name="Electronics")
        product = Product.objects.create(
            company=company,
            category=category,
            unit=unit,
            name="Laptop",
            cost_price=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )
        warehouse = Warehouse.objects.create(company=company, branch=branch, name="Main Warehouse")
        customer = Partner.objects.create(company=company, partner_type="customer", name="Customer A")
        supplier = Partner.objects.create(company=company, partner_type="supplier", name="Supplier A")

        purchase = PurchaseInvoice.objects.create(
            company=company, branch=branch, supplier=supplier, warehouse=warehouse
        )
        PurchaseInvoiceItem.objects.create(
            invoice=purchase, product=product, quantity=Decimal("10"), unit_price=Decimal("100.00")
        )
        PurchaseService.post_invoice(purchase, user=cls.superuser)

        sale = SalesInvoice.objects.create(
            company=company, branch=branch, customer=customer, warehouse=warehouse
        )
        SalesInvoiceItem.objects.create(
            invoice=sale, product=product, quantity=Decimal("2"), unit_price=Decimal("150.00")
        )
        SalesService.post_invoice(sale, user=cls.superuser)

        payment = Payment.objects.create(
            company=company,
            branch=branch,
            partner=customer,
            payment_type="inbound",
            payment_method="cash",
            account=Account.objects.get(company=company, code="1002", is_deleted=False),
            amount=Decimal("100.00"),
        )
        PaymentService.post_payment(payment, user=cls.superuser)
        PaymentAllocationService.allocate_payment(payment.pk, sale.pk, "sales", "100.00")

        draft = StockTransaction.objects.create(
            company=company, transaction_type="IN", source_warehouse=warehouse
        )
        StockMovement.objects.create(
            transaction=draft, product=product, quantity=Decimal("1"), unit_cost=Decimal("100.00")
        )

        Attachment.objects.create(
            content_type=ContentType.objects.get_for_model(Product),
            object_id=str(product.pk),
            file="attachments/product/spec-sheet.pdf",
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def admin_url(self, model, view, *args):
        opts = model._meta
        return reverse(f"admin:{opts.app_label}_{opts.model_name}_{view}", args=args)

    def test_admin_index_loads(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)

    def test_every_registered_model_page_loads(self):
        models_without_rows = []

        for model, model_admin in admin.site._registry.items():
            with self.subTest(model=model._meta.label):
                changelist = self.admin_url(model, "changelist")
                self.assertEqual(self.client.get(changelist).status_code, 200)

                if model_admin.search_fields:
                    self.assertEqual(self.client.get(changelist, {"q": "smoke"}).status_code, 200)

                add_response = self.client.get(self.admin_url(model, "add"))
                self.assertIn(add_response.status_code, (200, 403))

                obj = model._default_manager.first()
                if obj is None:
                    models_without_rows.append(model._meta.label)
                    continue
                change_response = self.client.get(self.admin_url(model, "change", obj.pk))
                self.assertEqual(change_response.status_code, 200)

        self.assertEqual(models_without_rows, [])
