# apps/users/api/views/auth_views.py

from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.auth_serializer import CustomTokenObtainPairSerializer

class CustomLoginView(TokenObtainPairView):
    """
    بوابة تسجيل الدخول:
    تستقبل (username, password) من الفلاتر.
    لو صح: بترجع Access Token + Refresh Token + User Data.
    لو غلط: بترجع رسالة خطأ 401 Unauthorized.
    """
    serializer_class = CustomTokenObtainPairSerializer