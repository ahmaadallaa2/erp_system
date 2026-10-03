from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from apps.core.models.company import Branch, Company
from apps.users.roles import SYSTEM_ROLES, is_system_admin
from apps.users.services.user_admin_service import UserAdminService

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(read_only=True, allow_null=True)
    branch_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "job_title",
            "user_type",
            "company_id",
            "branch_id",
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["company_id"] = str(user.company_id) if user.company_id else None
        token["branch_id"] = str(user.branch_id) if user.branch_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user).data
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except User.DoesNotExist:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )


class RoleListField(serializers.ListField):
    child = serializers.ChoiceField(choices=SYSTEM_ROLES)

    def get_attribute(self, instance):
        return sorted(group.name for group in instance.groups.all() if group.name in SYSTEM_ROLES)


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        trim_whitespace=False,
        style={"input_type": "password"},
        help_text="Required on create. On update, sets a new password.",
    )
    roles = RoleListField(
        required=False,
        help_text=(
            "ERP role groups. Replaces the current roles when sent. The default "
            "role of the user_type (CompanyAdmin, BranchManager) is always added."
        ),
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )
    company_name = serializers.CharField(source="company.name", read_only=True, allow_null=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "job_title",
            "user_type",
            "company",
            "company_name",
            "branch",
            "branch_name",
            "roles",
            "is_active",
            "password",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]

    @property
    def actor(self):
        return self.context["request"].user

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        duplicates = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        instance = self.instance

        if instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "This field is required."})

        if not is_system_admin(self.actor):
            self._validate_company_admin_scope(attrs)

        company = attrs["company"] if "company" in attrs else getattr(instance, "company", None)
        branch = attrs["branch"] if "branch" in attrs else getattr(instance, "branch", None)
        if branch is not None and (company is None or branch.company_id != company.pk):
            raise serializers.ValidationError(
                {"branch": "Branch must belong to the user's company."}
            )

        if attrs.get("password"):
            self._validate_password(attrs)

        return attrs

    def _validate_company_admin_scope(self, attrs):
        user_type = attrs.get("user_type", getattr(self.instance, "user_type", None))
        if user_type == "system_admin":
            raise serializers.ValidationError(
                {"user_type": "Company administrators cannot assign the system_admin type."}
            )

        if "company" in attrs and attrs["company"] != self.actor.company:
            raise serializers.ValidationError(
                {"company": "You can only manage users of your own company."}
            )

        if self.instance is None:
            attrs["company"] = self.actor.company

    def _validate_password(self, attrs):
        candidate = self.instance or User(
            email=attrs.get("email", ""),
            full_name=attrs.get("full_name", ""),
        )
        try:
            password_validation.validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

    def create(self, validated_data):
        try:
            return UserAdminService.create_user(**validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(serializers.as_serializer_error(exc)) from exc

    def update(self, instance, validated_data):
        try:
            return UserAdminService.update_user(instance, actor=self.actor, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(serializers.as_serializer_error(exc)) from exc


class ContextSerializer(serializers.Serializer):
    user = MeSerializer()
    company = serializers.JSONField()
    branch = serializers.JSONField()
