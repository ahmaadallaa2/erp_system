from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from apps.core.middleware import ThreadLocalMiddleware, get_current_user


class DummyUser:
    is_authenticated = True


class ThreadLocalMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ThreadLocalMiddleware(get_response=lambda request: HttpResponse())

    def test_stores_request_user(self):
        request = self.factory.get("/")
        request.user = DummyUser()

        self.middleware.process_request(request)

        self.assertIs(get_current_user(), request.user)
        self.middleware.process_response(request, HttpResponse())

    def test_clears_user_after_response(self):
        request = self.factory.get("/")
        request.user = DummyUser()

        self.middleware.process_request(request)
        response = self.middleware.process_response(request, HttpResponse())

        self.assertIsNone(get_current_user())
        self.assertEqual(response.status_code, 200)

    def test_clears_user_after_exception(self):
        request = self.factory.get("/")
        request.user = DummyUser()

        self.middleware.process_request(request)
        self.middleware.process_exception(request, RuntimeError("boom"))

        self.assertIsNone(get_current_user())
