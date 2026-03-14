# apps/users/api/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth_views import CustomLoginView

app_name = 'users_api'

urlpatterns = [
    # بوابة تسجيل الدخول (عشان تاخد التوكن لأول مرة)
    path('login/', CustomLoginView.as_view(), name='api_login'),
    
    # بوابة تجديد التوكن (عشان لو التوكن الأساسي خلص، الفلاتر يجدده في الخلفية)
    path('refresh/', TokenRefreshView.as_view(), name='api_refresh'),
]