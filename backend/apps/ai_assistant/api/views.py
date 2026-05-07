from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.ai_assistant.models import Document
from apps.ai_assistant.services import DocumentProcessingService, FaissStoreService
from .serializers import (
    DocumentChunkSerializer,
    DocumentSerializer,
    SemanticSearchRequestSerializer,
    SemanticSearchResultSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List AI documents",
        description="Retrieve uploaded AI assistant documents for the authenticated user's company.",
        tags=["AI Assistant"],
    ),
    retrieve=extend_schema(
        summary="Retrieve AI document",
        description="Retrieve one uploaded document by ID.",
        tags=["AI Assistant"],
    ),
    create=extend_schema(
        summary="Upload AI document",
        description="Upload a PDF or DOCX document. No AI processing is performed in this phase.",
        tags=["AI Assistant"],
    ),
)
class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Document.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        serializer.save(
            company=user.company,
            uploaded_by=user,
        )

    @extend_schema(
        summary="Process AI document",
        description="Extract text from a PDF/DOCX document and store text chunks. No embeddings are created.",
        tags=["AI Assistant"],
        responses={200: DocumentSerializer},
    )
    @action(detail=True, methods=["post"], url_path="process")
    def process_document(self, request, pk=None):
        document = self.get_object()

        try:
            DocumentProcessingService.process(document)
        except (RuntimeError, ValueError) as exc:
            raise ValidationError(str(exc))

        document.refresh_from_db()
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List AI document chunks",
        description="Retrieve text chunks extracted from one document.",
        tags=["AI Assistant"],
        responses=DocumentChunkSerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="chunks")
    def chunks(self, request, pk=None):
        document = self.get_object()
        queryset = document.chunks.order_by("chunk_index")
        serializer = DocumentChunkSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Semantic search AI document",
        description="Search extracted document chunks semantically using a local FAISS index. No chat or Q&A is performed.",
        tags=["AI Assistant"],
        request=SemanticSearchRequestSerializer,
        responses={200: SemanticSearchResultSerializer(many=True)},
    )
    @action(detail=True, methods=["post"], url_path="search")
    def search(self, request, pk=None):
        document = self.get_object()
        serializer = SemanticSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            results = FaissStoreService.search_document(
                document=document,
                query=serializer.validated_data["query"],
                top_k=serializer.validated_data["top_k"],
            )
        except (RuntimeError, ValueError) as exc:
            raise ValidationError(str(exc))

        response_serializer = SemanticSearchResultSerializer(results, many=True)
        return Response(response_serializer.data)
