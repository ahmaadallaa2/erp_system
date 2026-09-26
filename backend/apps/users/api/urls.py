from django.urls import path
from django.contrib.auth.decorators import login_not_required
from .views import LoginAPIView, RefreshAPIView, MeAPIView, ContextAPIView

urlpatterns = [
    path("login/", login_not_required(LoginAPIView.as_view()), name="api-login"),
    path("refresh/", login_not_required(RefreshAPIView.as_view()), name="api-refresh"),
    path("me/", MeAPIView.as_view(), name="api-me"),
    path("context/", ContextAPIView.as_view(), name="api-context"),
]
