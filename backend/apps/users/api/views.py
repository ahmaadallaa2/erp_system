from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    MeSerializer,
    ContextSerializer,
)


@extend_schema(
    tags=["Auth"],
    summary="Login",
    description="Authenticate user and return access and refresh tokens.",
    request=CustomTokenObtainPairSerializer,
    responses={200: CustomTokenObtainPairSerializer},
)
class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@extend_schema(
    tags=["Auth"],
    summary="Refresh token",
    description="Refresh access token using a valid refresh token.",
)
class RefreshAPIView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@extend_schema(
    tags=["Auth"],
    summary="Current user",
    description="Return the authenticated user profile.",
    responses={200: MeSerializer},
)
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


@extend_schema(
    tags=["Auth"],
    summary="Auth context",
    description="Return authentication context including current user, company, and branch.",
    responses={200: ContextSerializer},
)
class ContextAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = None
        if request.user.company:
            company = {
                "id": str(request.user.company.id),
                "name": request.user.company.name,
            }

        branch = None
        if request.user.branch:
            branch = {
                "id": str(request.user.branch.id),
                "name": request.user.branch.name,
            }

        data = {
            "user": request.user,
            "company": company,
            "branch": branch,
        }
        serializer = ContextSerializer(data)
        return Response(serializer.data)