from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models.company import Branch, Company
from apps.users.models import User
from apps.users.roles import (
    ROLE_ACCOUNTANT,
    ROLE_BRANCH_MANAGER,
    ROLE_COMPANY_ADMIN,
    ROLE_SALES_USER,
    assign_role,
    user_role_names,
)

PASSWORD = "S3cure-Passw0rd!"
URL = "/api/auth/users/"


def detail_url(user):
    return f"{URL}{user.pk}/"


class UserAdminAPITestCase(APITestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.branch_a = Branch.objects.create(company=self.company_a, name="Branch A1")
        self.company_b = Company.objects.create(name="Company B")
        self.branch_b = Branch.objects.create(company=self.company_b, name="Branch B1")

        self.system_admin = self.make_user("sys@example.com", user_type="system_admin")
        self.admin_a = self.make_user("admin-a@example.com", "company_admin", self.company_a)
        self.admin_b = self.make_user("admin-b@example.com", "company_admin", self.company_b)
        self.employee_a = self.make_user(
            "emp-a@example.com", company=self.company_a, branch=self.branch_a
        )
        self.employee_b = self.make_user(
            "emp-b@example.com", company=self.company_b, branch=self.branch_b
        )
        self.superuser_a = User.objects.create_superuser(
            email="root-a@example.com", password=PASSWORD, full_name="Root", company=self.company_a
        )

    @staticmethod
    def make_user(email, user_type="employee", company=None, branch=None):
        return User.objects.create_user(
            email=email,
            password=PASSWORD,
            full_name=email.split("@")[0],
            user_type=user_type,
            company=company,
            branch=branch,
        )

    def new_user_payload(self, **overrides):
        payload = {
            "email": "new@example.com",
            "full_name": "New Employee",
            "password": PASSWORD,
            "branch": str(self.branch_a.pk),
        }
        payload.update(overrides)
        return payload

    def listed_emails(self, response):
        return {row["email"] for row in response.data}

    # --- access ---------------------------------------------------------

    def test_authentication_is_required(self):
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_users_are_forbidden(self):
        assign_role(self.employee_a, ROLE_SALES_USER)
        self.client.force_authenticate(self.employee_a)

        self.assertEqual(self.client.get(URL).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.post(URL, self.new_user_payload(), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_company_admin_role_group_grants_access(self):
        assign_role(self.employee_a, ROLE_COMPANY_ADMIN)
        self.client.force_authenticate(self.employee_a)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("emp-b@example.com", self.listed_emails(response))

    # --- company admin scoping -----------------------------------------

    def test_company_admin_lists_only_own_company_users(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.listed_emails(response), {"admin-a@example.com", "emp-a@example.com"}
        )
        self.assertNotIn("password", response.data[0])

    def test_company_admin_cannot_access_other_company_user(self):
        self.client.force_authenticate(self.admin_a)
        url = detail_url(self.employee_b)

        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(url, {"full_name": "Hacked"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

        self.employee_b.refresh_from_db()
        self.assertEqual(self.employee_b.full_name, "emp-b")
        self.assertTrue(self.employee_b.is_active)

    def test_company_admin_cannot_manage_superuser_or_system_admin_in_own_company(self):
        system_admin_a = self.make_user("sys-a@example.com", "system_admin", self.company_a)
        self.client.force_authenticate(self.admin_a)

        for target in (self.superuser_a, system_admin_a):
            with self.subTest(target=target.email):
                response = self.client.patch(
                    detail_url(target), {"password": "An0ther-Passw0rd!"}, format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_company_admin_creates_user_in_own_company(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(
            URL, self.new_user_payload(roles=[ROLE_SALES_USER]), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertNotIn("password", response.data)
        self.assertEqual(response.data["company"], self.company_a.pk)
        self.assertEqual(response.data["roles"], [ROLE_SALES_USER])

        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.company, self.company_a)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)

    def test_company_admin_cannot_create_user_in_other_company(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(
            URL,
            self.new_user_payload(company=str(self.company_b.pk), branch=str(self.branch_b.pk)),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", response.data)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_company_admin_cannot_assign_system_admin_type(self):
        self.client.force_authenticate(self.admin_a)

        create = self.client.post(
            URL, self.new_user_payload(user_type="system_admin"), format="json"
        )
        update = self.client.patch(
            detail_url(self.employee_a), {"user_type": "system_admin"}, format="json"
        )

        self.assertEqual(create.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_type", create.data)
        self.assertEqual(update.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee_a.refresh_from_db()
        self.assertEqual(self.employee_a.user_type, "employee")

    def test_company_admin_cannot_change_user_company(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.patch(
            detail_url(self.employee_a),
            {"company": str(self.company_b.pk), "branch": str(self.branch_b.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company", response.data)
        self.employee_a.refresh_from_db()
        self.assertEqual(self.employee_a.company, self.company_a)

    def test_branch_must_belong_to_user_company(self):
        self.client.force_authenticate(self.admin_a)

        create = self.client.post(
            URL, self.new_user_payload(branch=str(self.branch_b.pk)), format="json"
        )
        update = self.client.patch(
            detail_url(self.employee_a), {"branch": str(self.branch_b.pk)}, format="json"
        )

        self.assertEqual(create.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("branch", create.data)
        self.assertEqual(update.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("branch", update.data)

    # --- system admin ----------------------------------------------------

    def test_system_admin_manages_users_across_companies(self):
        self.client.force_authenticate(self.system_admin)

        listed = self.client.get(URL)
        filtered = self.client.get(URL, {"company": str(self.company_b.pk)})
        created = self.client.post(
            URL,
            self.new_user_payload(
                company=str(self.company_b.pk),
                branch=str(self.branch_b.pk),
                user_type="company_admin",
            ),
            format="json",
        )
        updated = self.client.patch(
            detail_url(self.employee_b), {"job_title": "Cashier"}, format="json"
        )

        self.assertIn("emp-b@example.com", self.listed_emails(listed))
        self.assertIn("root-a@example.com", self.listed_emails(listed))
        self.assertEqual(
            self.listed_emails(filtered), {"admin-b@example.com", "emp-b@example.com"}
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["company"], self.company_b.pk)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)

    def test_system_admin_can_create_system_admin(self):
        self.client.force_authenticate(self.system_admin)

        response = self.client.post(
            URL,
            {
                "email": "sys2@example.com",
                "full_name": "Second Sysadmin",
                "password": PASSWORD,
                "user_type": "system_admin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNone(response.data["company"])

    # --- roles -------------------------------------------------------------

    def test_user_type_default_role_is_synced(self):
        self.client.force_authenticate(self.admin_a)

        created = self.client.post(
            URL,
            self.new_user_payload(user_type="company_admin", roles=[ROLE_ACCOUNTANT]),
            format="json",
        )
        user = User.objects.get(email="new@example.com")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(user_role_names(user), {ROLE_COMPANY_ADMIN, ROLE_ACCOUNTANT})

        self.client.patch(detail_url(user), {"user_type": "branch_manager"}, format="json")
        self.assertEqual(user_role_names(user), {ROLE_BRANCH_MANAGER, ROLE_ACCOUNTANT})

        self.client.patch(detail_url(user), {"user_type": "employee"}, format="json")
        self.assertEqual(user_role_names(user), {ROLE_ACCOUNTANT})

    def test_explicit_roles_replace_erp_groups_only(self):
        from django.contrib.auth.models import Group

        custom_group = Group.objects.create(name="Newsletter")
        self.employee_a.groups.add(custom_group)
        assign_role(self.employee_a, ROLE_ACCOUNTANT)
        self.client.force_authenticate(self.admin_a)

        response = self.client.patch(
            detail_url(self.employee_a), {"roles": [ROLE_SALES_USER]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["roles"], [ROLE_SALES_USER])
        self.assertEqual(
            set(self.employee_a.groups.values_list("name", flat=True)),
            {ROLE_SALES_USER, "Newsletter"},
        )

    def test_unknown_role_is_rejected(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(URL, self.new_user_payload(roles=["Overlord"]), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("roles", response.data)

    # --- validation --------------------------------------------------------

    def test_password_is_required_and_validated_on_create(self):
        self.client.force_authenticate(self.admin_a)
        payload = self.new_user_payload()
        payload.pop("password")

        missing = self.client.post(URL, payload, format="json")
        weak = self.client.post(URL, self.new_user_payload(password="123"), format="json")

        self.assertIn("password", missing.data)
        self.assertEqual(weak.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", weak.data)

    def test_admin_can_reset_password(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.patch(
            detail_url(self.employee_a), {"password": "Brand-New-Passw0rd!"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_a.refresh_from_db()
        self.assertTrue(self.employee_a.check_password("Brand-New-Passw0rd!"))

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(
            URL, self.new_user_payload(email="EMP-A@example.com"), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_model_rules_return_400(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.post(
            URL, self.new_user_payload(user_type="branch_manager", branch=None), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- deactivation ------------------------------------------------------

    def test_delete_deactivates_instead_of_deleting(self):
        self.client.force_authenticate(self.admin_a)

        response = self.client.delete(detail_url(self.employee_a))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.employee_a.refresh_from_db()
        self.assertFalse(self.employee_a.is_active)

        listed = self.client.get(URL, {"is_active": "false"})
        self.assertEqual(self.listed_emails(listed), {"emp-a@example.com"})

        reactivated = self.client.patch(
            detail_url(self.employee_a), {"is_active": True}, format="json"
        )
        self.assertEqual(reactivated.status_code, status.HTTP_200_OK)
        self.assertTrue(reactivated.data["is_active"])

    def test_admin_cannot_deactivate_self(self):
        self.client.force_authenticate(self.admin_a)

        deleted = self.client.delete(detail_url(self.admin_a))
        patched = self.client.patch(detail_url(self.admin_a), {"is_active": False}, format="json")

        self.assertEqual(deleted.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(patched.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin_a.refresh_from_db()
        self.assertTrue(self.admin_a.is_active)
