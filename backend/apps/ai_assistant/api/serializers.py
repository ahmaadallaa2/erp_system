from rest_framework import serializers

from apps.ai_assistant.models import Document, DocumentChunk


class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source="chunks.count", read_only=True)

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
