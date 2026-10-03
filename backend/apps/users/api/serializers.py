from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

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


class ContextSerializer(serializers.Serializer):
    user = MeSerializer()
    company = serializers.JSONField()
    branch = serializers.JSONField()
