# apps/users/api/views/auth_views.py

from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers.auth_serializer import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    # هنا بنقول لـ SimpleJWT: استخدم السلايزر "المعدل" بتاعنا
    serializer_class = CustomTokenObtainPairSerializer