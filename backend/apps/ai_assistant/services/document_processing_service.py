from django.db import transaction

from apps.ai_assistant.models import DocumentChunk

from .chunking_service import ChunkingService
from .extraction_service import ExtractionService
from .faiss_store_service import FaissStoreService


class DocumentProcessingService:
    @staticmethod
    @transaction.atomic
    def process(document):
        document.status = document.Status.PROCESSING
        document.notes = ""
        document.save(update_fields=["status", "notes", "updated_at"])

        try:
            blocks = ExtractionService.extract(document)
            chunks = ChunkingService.chunk_blocks(blocks)

            if not chunks:
                raise ValueError("No extractable text was found in this document.")

            DocumentChunk.objects.filter(document=document).delete()
            DocumentChunk.objects.bulk_create(
                [
                    DocumentChunk(
                        document=document,
                        company=document.company,
                        chunk_index=index,
                        text=chunk.text,
                        page_number=chunk.page_number,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                    )
                    for index, chunk in enumerate(chunks)
                ]
            )

            FaissStoreService.build_document_index(document)

            document.status = document.Status.READY
            document.notes = ""
            document.save(update_fields=["status", "notes", "updated_at"])

            return document
        except Exception as exc:
            document.status = document.Status.FAILED
            document.notes = str(exc)
            document.save(update_fields=["status", "notes", "updated_at"])
            raise
