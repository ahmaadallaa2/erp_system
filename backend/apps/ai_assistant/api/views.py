import re

from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.ai_assistant.models import Document
from apps.ai_assistant.services import DocumentProcessingService, FaissStoreService, QAService
from apps.users.api.permissions import IsCompanyMember
from .serializers import (
    AskDocumentRequestSerializer,
    AskDocumentResponseSerializer,
    DocumentChunkSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    KeywordSearchRequestSerializer,
    KeywordSearchResultSerializer,
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
        request={
            "multipart/form-data": DocumentUploadSerializer,
        },
        responses={201: DocumentSerializer},
    ),
)
class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        return [permission() for permission in [IsAuthenticated, IsCompanyMember]]

    def get_serializer_class(self):
        if self.action == "create":
            return DocumentUploadSerializer
        return DocumentSerializer

    def get_queryset(self):
        user = self.request.user
        return Document.objects.filter(
            is_deleted=False,
            company=user.company,
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        if not request.user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save(
            company=request.user.company,
            uploaded_by=request.user,
        )
        response_serializer = DocumentSerializer(
            document,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user

        if not user.company:
            raise ValidationError("Authenticated user is not assigned to a company.")

        serializer.save(
            company=user.company,
            uploaded_by=user,
        )

    @extend_schema(
        summary="Delete AI document",
        description="Delete an uploaded AI document and clean its chunks and local FAISS index.",
        tags=["AI Assistant"],
        responses={204: None},
    )
    def destroy(self, request, *args, **kwargs):
        document = self.get_object()

        try:
            FaissStoreService.delete_document_index(document)
        except OSError as exc:
            raise ValidationError(f"Failed to delete FAISS index: {exc}") from exc

        if document.file:
            document.file.delete(save=False)

        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Process AI document",
        description="Extract text, create chunks, generate embeddings, and build the local FAISS index.",
        tags=["AI Assistant"],
        request=None,
        responses={200: DocumentSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="process",
        parser_classes=[JSONParser],
    )
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
    @action(
        detail=True,
        methods=["post"],
        url_path="search",
        parser_classes=[JSONParser],
    )
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

    @extend_schema(
        summary="Keyword search AI document",
        description="Search extracted document chunks with case-insensitive keyword matching.",
        tags=["AI Assistant"],
        request=KeywordSearchRequestSerializer,
        responses={200: KeywordSearchResultSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="keyword-search",
        parser_classes=[JSONParser],
    )
    def keyword_search(self, request, pk=None):
        document = self.get_object()
        serializer = KeywordSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        top_k = serializer.validated_data["top_k"]
        terms = re.findall(r"\w+", query.lower())

        if not terms:
            return Response([])

        text_filter = Q()
        for term in terms:
            text_filter |= Q(text__icontains=term)

        chunks = document.chunks.filter(
            text_filter,
            company=request.user.company,
        ).order_by("chunk_index")

        results = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            score = sum(text_lower.count(term) for term in terms)
            if score <= 0:
                continue

            results.append(
                {
                    "chunk_id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "score": float(score),
                    "method": "keyword",
                }
            )

        results.sort(key=lambda result: (-result["score"], result["chunk_index"]))
        response_serializer = KeywordSearchResultSerializer(results[:top_k], many=True)
        return Response(response_serializer.data)

    @extend_schema(
        summary="Ask AI document",
        description="Answer a question using retrieved document chunks and Ollama llama3. No ERP core data is modified.",
        tags=["AI Assistant"],
        request=AskDocumentRequestSerializer,
        responses={200: AskDocumentResponseSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="ask",
        parser_classes=[JSONParser],
    )
    def ask(self, request, pk=None):
        document = self.get_object()
        serializer = AskDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = QAService.answer_question(
                document=document,
                question=serializer.validated_data["question"],
                top_k=serializer.validated_data["top_k"],
            )
        except (RuntimeError, ValueError) as exc:
            raise ValidationError(str(exc))

        response_serializer = AskDocumentResponseSerializer(result)
        return Response(response_serializer.data)
