from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


class ApiDocsSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="docs-user@example.com",
            password="password",
            full_name="Docs User",
        )
        self.staff_user = User.objects.create_user(
            email="docs-staff@example.com",
            password="password",
            full_name="Docs Staff",
            is_staff=True,
        )

    def test_docs_require_authentication_when_debug_is_false(self):
        for url in ("/api/schema/", "/api/docs/", "/api/redoc/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_docs_reject_non_staff_user_when_debug_is_false(self):
        self.client.force_authenticate(user=self.user)
        for url in ("/api/schema/", "/api/docs/", "/api/redoc/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_schema_allows_staff_user(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
