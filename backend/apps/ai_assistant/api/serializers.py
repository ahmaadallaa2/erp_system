from rest_framework import serializers

from drf_spectacular.utils import OpenApiTypes, extend_schema_field

from apps.ai_assistant.models import Document, DocumentChunk


@extend_schema_field(OpenApiTypes.BINARY)
class BinaryFileField(serializers.FileField):
    pass


class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source="chunks.count", read_only=True)
    file = serializers.FileField()

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
            "chunks_count",
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
            "chunks_count",
            "created_at",
            "updated_at",
        ]


class DocumentUploadSerializer(serializers.Serializer):
    file = BinaryFileField(write_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        return Document.objects.create(**validated_data)


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "document",
            "chunk_index",
            "text",
            "page_number",
            "char_start",
            "char_end",
            "created_at",
        ]
        read_only_fields = fields


class SemanticSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class SemanticSearchResultSerializer(serializers.Serializer):
    score = serializers.FloatField()
    chunk = DocumentChunkSerializer()


class AskDocumentRequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)


class AskDocumentCitationSerializer(serializers.Serializer):
    chunk_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    page_number = serializers.IntegerField(allow_null=True)
    text = serializers.CharField()
    score = serializers.FloatField()


class AskDocumentResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    citations = AskDocumentCitationSerializer(many=True)
