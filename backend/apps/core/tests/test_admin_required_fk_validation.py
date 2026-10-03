from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.accounting.models.payment import Payment
from apps.inventory.models import StockBalance, StockTransaction
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User

# model, admin add URL, required foreign keys that must surface as field errors
CASES = (
    (StockTransaction, "/admin/inventory/stocktransaction/add/", ("company", "source_warehouse")),
    (StockBalance, "/admin/inventory/stockbalance/add/", ("company", "product", "warehouse")),
    (SalesInvoice, "/admin/sales/salesinvoice/add/", ("company", "branch", "customer")),
    (PurchaseInvoice, "/admin/purchases/purchaseinvoice/add/", ("company", "branch", "supplier", "warehouse")),
    (Payment, "/admin/accounting/payment/add/", ("company", "branch", "partner", "account")),
)


# Manifest static storage needs collectstatic output, which tests don't have.
@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AdminRequiredForeignKeyValidationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email="fk-admin@example.com",
            password="testpass123",
            full_name="FK Admin",
        )
        self.client.force_login(self.user)

    def test_empty_add_form_returns_field_errors(self):
        for model, url, required_fields in CASES:
            with self.subTest(model=model.__name__):
                response = self.client.post(url, {})

                self.assertEqual(response.status_code, 200)
                errors = response.context["adminform"].form.errors
                for field in required_fields:
                    self.assertIn(field, errors)
                self.assertFalse(model.objects.exists())

    def test_full_clean_without_foreign_keys_raises_validation_error(self):
        for model, _url, required_fields in CASES:
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError) as ctx:
                    model().full_clean()

                for field in required_fields:
                    self.assertIn(field, ctx.exception.message_dict)

    def test_str_without_foreign_keys_does_not_raise(self):
        for model, _url, _fields in CASES:
            with self.subTest(model=model.__name__):
                self.assertIsInstance(str(model()), str)
