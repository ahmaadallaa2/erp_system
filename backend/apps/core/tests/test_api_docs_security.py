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

    def test_schema_requires_authentication_when_debug_is_false(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_swagger_requires_authentication_when_debug_is_false(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_redoc_requires_authentication_when_debug_is_false(self):
        response = self.client.get("/api/redoc/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_schema_allows_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
