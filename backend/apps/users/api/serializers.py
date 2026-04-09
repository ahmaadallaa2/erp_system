from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["email"] = user.email
        token["company_id"] = str(user.company_id) if user.company_id else None
        token["branch_id"] = str(user.branch_id) if user.branch_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "full_name": self.user.full_name,
            "user_type": self.user.user_type,
            "company_id": str(self.user.company_id) if self.user.company_id else None,
            "branch_id": str(self.user.branch_id) if self.user.branch_id else None,
        }

        return data


class MeSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(source="company.id", read_only=True)
    branch_id = serializers.UUIDField(source="branch.id", read_only=True)

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


class ContextSerializer(serializers.Serializer):
    user = MeSerializer()
    company = serializers.JSONField()
    branch = serializers.JSONField()