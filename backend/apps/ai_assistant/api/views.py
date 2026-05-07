from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.ai_assistant.models import Document
from .serializers import DocumentSerializer


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
