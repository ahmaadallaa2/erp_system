import json
import shutil
from pathlib import Path

from django.conf import settings

from apps.ai_assistant.models import DocumentChunk

from .embedding_service import EmbeddingService


class FaissStoreService:
    INDEX_FILENAME = "index.faiss"
    METADATA_FILENAME = "metadata.json"

    @classmethod
    def build_document_index(cls, document, model_name=None):
        try:
            import faiss
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("faiss-cpu and numpy are required for semantic search.") from exc

        model_name = model_name or EmbeddingService.DEFAULT_MODEL_NAME
        chunks = list(document.chunks.order_by("chunk_index"))

        if not chunks:
            raise ValueError("Document has no chunks. Process it before building a search index.")

        missing_embeddings = [
            chunk for chunk in chunks
            if not chunk.embedding or chunk.embedding_model != model_name
        ]

        if missing_embeddings:
            embeddings = EmbeddingService.embed_texts(
                [chunk.text for chunk in missing_embeddings],
                model_name=model_name,
            )

            for chunk, embedding in zip(missing_embeddings, embeddings, strict=True):
                chunk.embedding = embedding
                chunk.embedding_model = model_name

            DocumentChunk.objects.bulk_update(
                missing_embeddings,
                ["embedding", "embedding_model"],
            )

        chunks = list(document.chunks.order_by("chunk_index"))
        vectors = np.array([chunk.embedding for chunk in chunks], dtype="float32")

        if vectors.ndim != 2 or vectors.shape[0] == 0:
            raise ValueError("No embeddings were generated for this document.")

        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)

        index_dir = cls._document_index_dir(document)
        index_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(index, str(index_dir / cls.INDEX_FILENAME))

        metadata = [
            {
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
            }
            for chunk in chunks
        ]

        (index_dir / cls.METADATA_FILENAME).write_text(
            json.dumps(
                {
                    "document_id": str(document.id),
                    "model_name": model_name,
                    "metadata": metadata,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return index_dir

    @classmethod
    def search_document(cls, document, query, top_k=5, model_name=None):
        try:
            import faiss
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("faiss-cpu and numpy are required for semantic search.") from exc

        if not query or not query.strip():
            raise ValueError("Search query is required.")

        top_k = max(1, min(int(top_k), 20))
        model_name = model_name or EmbeddingService.DEFAULT_MODEL_NAME

        index_dir = cls._document_index_dir(document)
        index_path = index_dir / cls.INDEX_FILENAME
        metadata_path = index_dir / cls.METADATA_FILENAME

        if not index_path.exists() or not metadata_path.exists():
            cls.build_document_index(document, model_name=model_name)

        metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata_payload.get("model_name") != model_name:
            cls.build_document_index(document, model_name=model_name)
            metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))

        index = faiss.read_index(str(index_path))
        query_vector = np.array(
            [EmbeddingService.embed_query(query, model_name=model_name)],
            dtype="float32",
        )

        scores, positions = index.search(query_vector, top_k)
        metadata = metadata_payload["metadata"]
        chunk_ids = [
            metadata[position]["chunk_id"]
            for position in positions[0]
            if 0 <= position < len(metadata)
        ]

        chunks_by_id = {
            str(chunk.id): chunk
            for chunk in DocumentChunk.objects.filter(id__in=chunk_ids)
        }

        results = []
        for score, position in zip(scores[0], positions[0], strict=True):
            if position < 0 or position >= len(metadata):
                continue

            chunk_meta = metadata[position]
            chunk = chunks_by_id.get(chunk_meta["chunk_id"])
            if not chunk:
                continue

            results.append(
                {
                    "score": float(score),
                    "chunk": chunk,
                }
            )

        return results

    @classmethod
    def delete_document_index(cls, document):
        index_dir = cls._document_index_dir(document)
        if index_dir.exists():
            shutil.rmtree(index_dir)

    @staticmethod
    def _document_index_dir(document):
        return (
            Path(settings.MEDIA_ROOT)
            / "ai_assistant"
            / "faiss"
            / f"company_{document.company_id}"
            / str(document.id)
        )
