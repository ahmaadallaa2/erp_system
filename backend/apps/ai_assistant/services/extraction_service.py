import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedTextBlock:
    text: str
    page_number: int | None = None


class ExtractionService:
    @staticmethod
    def extract(document):
        file_path = document.file.path
        ext = os.path.splitext(document.file.name)[1].lower()

        if ext == ".pdf":
            return ExtractionService._extract_pdf(file_path)

        if ext == ".docx":
            return ExtractionService._extract_docx(file_path)

        raise ValueError("Unsupported document type.")

    @staticmethod
    def _extract_pdf(file_path):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required to extract PDF text.") from exc

        reader = PdfReader(file_path)
        blocks = []

        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                blocks.append(ExtractedTextBlock(text=text, page_number=index))

        return blocks

    @staticmethod
    def _extract_docx(file_path):
        try:
            from docx import Document as DocxDocument
        except ImportError as exc:
            raise RuntimeError("python-docx is required to extract DOCX text.") from exc

        doc = DocxDocument(file_path)
        paragraphs = [
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text and paragraph.text.strip()
        ]

        if not paragraphs:
            return []

        return [ExtractedTextBlock(text="\n".join(paragraphs), page_number=None)]
