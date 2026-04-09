from django.urls import path
from .views import LoginAPIView, RefreshAPIView, MeAPIView, ContextAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path("refresh/", RefreshAPIView.as_view(), name="api-refresh"),
    path("me/", MeAPIView.as_view(), name="api-me"),
    path("context/", ContextAPIView.as_view(), name="api-context"),
]