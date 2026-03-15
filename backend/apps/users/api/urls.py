# apps/users/urls.py
from django.urls import path
from ..api.views.auth_views import CustomTokenObtainPairView

urlpatterns = [
    # مسار اللوجين اللي هيرجع الـ Access والـ Refresh توكن
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]