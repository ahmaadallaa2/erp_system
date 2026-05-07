from rest_framework import serializers

from apps.ai_assistant.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "company",
            "uploaded_by",
            "file",
            "original_filename",
            "file_type",
            "file_size",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company",
            "uploaded_by",
            "original_filename",
            "file_type",
            "file_size",
            "status",
            "created_at",
            "updated_at",
        ]
