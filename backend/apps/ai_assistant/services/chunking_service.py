from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    page_number: int | None
    char_start: int
    char_end: int


class ChunkingService:
    DEFAULT_CHUNK_SIZE = 1200
    DEFAULT_OVERLAP = 150

    @classmethod
    def chunk_blocks(
        cls,
        blocks,
        chunk_size=DEFAULT_CHUNK_SIZE,
        overlap=DEFAULT_OVERLAP,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be zero or greater and smaller than chunk_size.")

        chunks = []
        global_offset = 0

        for block in blocks:
            text = cls._normalize_text(block.text)
            if not text:
                continue

            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunk_text = text[start:end].strip()

                if chunk_text:
                    chunks.append(
                        TextChunk(
                            text=chunk_text,
                            page_number=block.page_number,
                            char_start=global_offset + start,
                            char_end=global_offset + end,
                        )
                    )

                if end >= len(text):
                    break

                start = end - overlap

            global_offset += len(text) + 1

        return chunks

    @staticmethod
    def _normalize_text(text):
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
