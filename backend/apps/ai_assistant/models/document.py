import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel
from apps.core.models.company import Company


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    company_id = instance.company_id or "unassigned"
    return f"ai_assistant/company_{company_id}/documents/{safe_name}"


class Document(SoftDeleteModel):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", _("Uploaded")
        FAILED = "failed", _("Failed")

    ALLOWED_EXTENSIONS = {".pdf", ".docx"}

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="ai_documents",
        verbose_name=_("Company"),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_uploaded_documents",
        verbose_name=_("Uploaded by"),
    )
    file = models.FileField(
        _("File"),
        upload_to=document_upload_path,
    )
    original_filename = models.CharField(
        _("Original filename"),
        max_length=255,
        blank=True,
    )
    file_type = models.CharField(
        _("File type"),
        max_length=10,
        blank=True,
    )
    file_size = models.PositiveBigIntegerField(
        _("File size"),
        default=0,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
    )

    class Meta:
        verbose_name = _("AI Document")
        verbose_name_plural = _("AI Documents")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def __str__(self):
        return self.original_filename or os.path.basename(self.file.name)

    def clean(self):
        super().clean()

        if self.file:
            filename = os.path.basename(self.file.name)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    {"file": _("Only PDF and DOCX files are allowed.")}
                )

    def save(self, *args, **kwargs):
        if self.file:
            filename = os.path.basename(self.file.name)
            ext = os.path.splitext(filename)[1].lower()

            if not self.original_filename:
                self.original_filename = filename[:255]

            self.file_type = ext.lstrip(".")[:10]

            try:
                self.file_size = self.file.size or 0
            except (OSError, ValueError):
                self.file_size = 0

        self.full_clean()
        super().save(*args, **kwargs)
