from io import StringIO

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.sql import emit_post_migrate_signal
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models.company import Branch, Company
from apps.users.admin import CustomUserAdmin
from apps.users.models import User
from apps.users.roles import (
    ROLE_ACCOUNTANT,
    ROLE_MODEL_PERMISSIONS,
    ROLE_SALES_USER,
    SYSTEM_ROLES,
    sync_role_groups,
)


def group_permission_names(group):
    return {
        f"{perm.content_type.app_label}.{perm.codename}"
        for perm in group.permissions.select_related("content_type")
    }


class RoleGroupSyncTestCase(TestCase):
    def test_migrate_created_all_role_groups_with_mapped_permissions(self):
        for role in SYSTEM_ROLES:
            group = Group.objects.get(name=role)
            self.assertEqual(group_permission_names(group), ROLE_MODEL_PERMISSIONS[role], role)

    def test_every_mapped_permission_exists(self):
        existing = {
            f"{perm.content_type.app_label}.{perm.codename}"
            for perm in Permission.objects.select_related("content_type")
        }
        mapped = set().union(*ROLE_MODEL_PERMISSIONS.values())

        self.assertEqual(mapped - existing, set())

    def test_no_role_can_delete_or_manage_users(self):
        for perms in ROLE_MODEL_PERMISSIONS.values():
            for perm in perms:
                app_label, codename = perm.split(".", 1)
                self.assertFalse(codename.startswith("delete_"), perm)
                self.assertNotIn(app_label, {"users", "auth"}, perm)

    def test_post_migrate_recreates_deleted_groups(self):
        Group.objects.filter(name__in=SYSTEM_ROLES).delete()

        emit_post_migrate_signal(verbosity=0, interactive=False, db="default")

        self.assertEqual(Group.objects.filter(name__in=SYSTEM_ROLES).count(), len(SYSTEM_ROLES))
        accountant = Group.objects.get(name=ROLE_ACCOUNTANT)
        self.assertEqual(group_permission_names(accountant), ROLE_MODEL_PERMISSIONS[ROLE_ACCOUNTANT])

    def test_sync_keeps_manually_added_permissions(self):
        group = Group.objects.get(name=ROLE_SALES_USER)
        extra = Permission.objects.get(
            content_type__app_label="sales",
            codename="delete_salesinvoiceitem",
        )
        group.permissions.add(extra)

        sync_role_groups()

        self.assertIn("sales.delete_salesinvoiceitem", group_permission_names(group))

    def test_setup_roles_command_still_works(self):
        Group.objects.filter(name=ROLE_SALES_USER).delete()
        out = StringIO()

        call_command("setup_roles", stdout=out)

        self.assertIn("1 newly created", out.getvalue())
        self.assertTrue(Group.objects.filter(name=ROLE_SALES_USER).exists())


class AuthApiHardeningTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            full_name="Test User",
            company=self.company,
            branch=self.branch,
        )

    def tearDown(self):
        cache.clear()

    def test_me_returns_null_company_and_branch_for_unassigned_user(self):
        user = User.objects.create_user(
            email="nocompany@example.com",
            password="password123",
            full_name="No Company",
        )
        self.client.force_authenticate(user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["company_id"])
        self.assertIsNone(response.data["branch_id"])

    def test_login_returns_tokens_and_user_payload(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@example.com", "password": "password123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["company_id"], str(self.company.id))
        self.assertEqual(response.data["user"]["branch_id"], str(self.branch.id))

    def test_refresh_for_deleted_user_is_unauthorized(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.user.delete()

        response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_for_inactive_user_is_unauthorized(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.user.soft_delete()

        response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_is_throttled(self):
        payload = {"email": "user@example.com", "password": "wrong-password"}
        statuses = [
            self.client.post("/api/auth/login/", payload, format="json").status_code
            for _ in range(11)
        ]

        self.assertEqual(statuses[:10], [status.HTTP_401_UNAUTHORIZED] * 10)
        self.assertEqual(statuses[10], status.HTTP_429_TOO_MANY_REQUESTS)


class UserModelHardeningTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="password123",
            full_name="Branch Manager",
            user_type="branch_manager",
            company=self.company,
            branch=self.branch,
        )
        User.objects.filter(pk=self.manager.pk).update(branch=None)
        self.manager.refresh_from_db()

    def test_partial_saves_work_for_user_left_without_branch(self):
        self.manager.save(update_fields=["last_login"])
        self.manager.soft_delete()

        self.manager.refresh_from_db()
        self.assertFalse(self.manager.is_active)

    def test_full_save_still_validates(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self.manager.save()


class UserAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.model_admin = CustomUserAdmin(User, admin.site)
        self.target = User.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target",
        )

    def request_for(self, user):
        request = self.factory.get("/admin/users/user/")
        request.user = user
        return request

    def test_staff_cannot_edit_superuser_flag_or_direct_permissions(self):
        staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            full_name="Staff",
            is_staff=True,
        )

        readonly = self.model_admin.get_readonly_fields(self.request_for(staff), self.target)

        self.assertIn("is_superuser", readonly)
        self.assertIn("user_permissions", readonly)

    def test_superuser_can_edit_superuser_flag(self):
        superuser = User.objects.create_superuser(
            email="root@example.com",
            password="password123",
            full_name="Root",
        )

        readonly = self.model_admin.get_readonly_fields(self.request_for(superuser), self.target)

        self.assertNotIn("is_superuser", readonly)
