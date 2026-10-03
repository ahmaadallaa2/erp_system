from django.test import TestCase, override_settings

from apps.core.models.company import Branch, Company
from apps.inventory.models import Warehouse
from apps.users.models import User


# Manifest static storage needs collectstatic output, which tests don't have.
@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class WarehouseAdminAddViewTestCase(TestCase):
    add_url = "/admin/inventory/warehouse/add/"

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="warehouse-admin@example.com",
            password="testpass123",
            full_name="Warehouse Admin",
        )
        self.client.force_login(self.user)
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")

    def form_data(self, **overrides):
        data = {
            "company": str(self.company.pk),
            "name": "Main Warehouse",
            "warehouse_type": "main",
            "is_active": "on",
            "branch": str(self.branch.pk),
            "address": "",
            "keeper": "",
        }
        data.update(overrides)
        return data

    def test_add_page_loads(self):
        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 200)

    def test_empty_submit_returns_field_errors(self):
        response = self.client.post(self.add_url, {})

        self.assertEqual(response.status_code, 200)
        errors = response.context["adminform"].form.errors
        self.assertIn("company", errors)
        self.assertIn("branch", errors)
        self.assertIn("name", errors)
        self.assertFalse(Warehouse.objects.exists())

    def test_missing_branch_returns_field_error(self):
        response = self.client.post(self.add_url, self.form_data(branch=""))

        self.assertEqual(response.status_code, 200)
        errors = response.context["adminform"].form.errors
        self.assertIn("branch", errors)
        self.assertFalse(Warehouse.objects.exists())

    def test_branch_from_other_company_returns_form_error(self):
        other_company = Company.objects.create(name="Other Company")
        other_branch = Branch.objects.create(company=other_company, name="Other Branch")

        response = self.client.post(self.add_url, self.form_data(branch=str(other_branch.pk)))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["adminform"].form.non_field_errors())
        self.assertFalse(Warehouse.objects.exists())

    def test_str_without_branch_does_not_raise(self):
        self.assertIn("-", str(Warehouse(name="Draft")))

    def test_valid_submit_creates_warehouse(self):
        response = self.client.post(self.add_url, self.form_data())

        self.assertEqual(response.status_code, 302)
        warehouse = Warehouse.objects.get()
        self.assertEqual(warehouse.branch, self.branch)
        self.assertTrue(warehouse.code.startswith("WH-"))
