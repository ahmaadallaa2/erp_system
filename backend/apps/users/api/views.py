import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.roles import is_system_admin
from apps.users.services.user_admin_service import UserAdminService
from .permissions import CanManageUsers
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    MeSerializer,
    ContextSerializer,
    UserAdminSerializer,
)

User = get_user_model()


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


def _uuid_param(request, name):
    value = request.query_params.get(name)
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        raise ValidationError({name: "Must be a valid UUID."})


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description=(
            "System admins see every user; company admins see their company's "
            "users except superusers and system admins. Inactive users are included."
        ),
        tags=["Users"],
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search email or full name."),
            OpenApiParameter(
                "user_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                enum=[choice for choice, _ in User.USER_TYPE_CHOICES],
            ),
            OpenApiParameter("is_active", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter("branch", OpenApiTypes.UUID, OpenApiParameter.QUERY),
            OpenApiParameter(
                "company",
                OpenApiTypes.UUID,
                OpenApiParameter.QUERY,
                description="System admins only; ignored for company admins.",
            ),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve user", tags=["Users"]),
    create=extend_schema(
        summary="Create user",
        description=(
            "Company admins always create users in their own company and cannot "
            "assign the system_admin type."
        ),
        tags=["Users"],
    ),
    update=extend_schema(summary="Update user", tags=["Users"]),
    partial_update=extend_schema(summary="Partially update user", tags=["Users"]),
    destroy=extend_schema(
        summary="Deactivate user",
        description="Set is_active to false. Users are never hard-deleted through the API.",
        tags=["Users"],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserAdminSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params

        qs = (
            User.objects.select_related("company", "branch")
            .prefetch_related("groups")
            .order_by("full_name", "email")
        )

        if is_system_admin(user):
            company_id = _uuid_param(self.request, "company")
            if company_id:
                qs = qs.filter(company_id=company_id)
        else:
            qs = qs.filter(company_id=user.company_id, is_superuser=False).exclude(
                user_type="system_admin"
            )

        search = params.get("search")
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(full_name__icontains=search))

        user_type = params.get("user_type")
        if user_type in dict(User.USER_TYPE_CHOICES):
            qs = qs.filter(user_type=user_type)

        is_active = params.get("is_active")
        if is_active in ("true", "false"):
            qs = qs.filter(is_active=is_active == "true")

        branch_id = _uuid_param(self.request, "branch")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        return qs

    def perform_destroy(self, instance):
        try:
            UserAdminService.deactivate_user(instance, actor=self.request.user)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc