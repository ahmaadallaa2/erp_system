from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    MeSerializer,
    ContextSerializer,
)


class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RefreshAPIView(TokenRefreshView):
    pass


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


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