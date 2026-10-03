from django.urls import path
from django.contrib.auth.decorators import login_not_required
from rest_framework.routers import SimpleRouter

from .views import LoginAPIView, RefreshAPIView, MeAPIView, ContextAPIView, UserViewSet

router = SimpleRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("login/", login_not_required(LoginAPIView.as_view()), name="api-login"),
    path("refresh/", login_not_required(RefreshAPIView.as_view()), name="api-refresh"),
    path("me/", MeAPIView.as_view(), name="api-me"),
    path("context/", ContextAPIView.as_view(), name="api-context"),
    *router.urls,
]
