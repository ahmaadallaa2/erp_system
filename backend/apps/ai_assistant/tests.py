import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from apps.ai_assistant.api.serializers import DocumentUploadSerializer
from apps.ai_assistant.services.extraction_service import ExtractionService


FIXTURES_DIR = Path(__file__).resolve().parent / "test_assets" / "fixtures"


class DocumentUploadSerializerTestCase(SimpleTestCase):
    def test_accepts_pdf_and_docx_extensions_case_insensitively(self):
        for filename in [
            "sample_smart_contract_agreement.PDF",
            "sample_smart_contract_agreement.DOCX",
        ]:
            with self.subTest(filename=filename):
                serializer = DocumentUploadSerializer(
                    data={
                        "file": SimpleUploadedFile(
                            filename,
                            b"demo content",
                            content_type="application/octet-stream",
                        )
                    }
                )

                self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_unsupported_extensions(self):
        serializer = DocumentUploadSerializer(
            data={
                "file": SimpleUploadedFile(
                    "contract.txt",
                    b"demo content",
                    content_type="text/plain",
                )
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)
        self.assertIn("Only PDF and DOCX files are allowed.", str(serializer.errors["file"]))


class ExtractionServiceDemoFixturesTestCase(SimpleTestCase):
    def test_demo_fixture_files_are_available(self):
        expected_files = [
            "sample_smart_contract_agreement.pdf",
            "sample_smart_contract_agreement.docx",
            "demo_sales_report.pdf",
            "demo_sales_report.docx",
        ]

        for filename in expected_files:
            with self.subTest(filename=filename):
                self.assertTrue((FIXTURES_DIR / filename).exists())

    def test_extract_dispatches_pdf_and_docx_by_extension_case_insensitively(self):
        calls = []
        original_pdf = ExtractionService._extract_pdf
        original_docx = ExtractionService._extract_docx

        try:
            ExtractionService._extract_pdf = staticmethod(
                lambda file_path: calls.append(("pdf", file_path)) or []
            )
            ExtractionService._extract_docx = staticmethod(
                lambda file_path: calls.append(("docx", file_path)) or []
            )

            pdf_document = SimpleNamespace(
                file=SimpleNamespace(path="sample.pdf", name="sample.PDF")
            )
            docx_document = SimpleNamespace(
                file=SimpleNamespace(path="sample.docx", name="sample.DOCX")
            )

            ExtractionService.extract(pdf_document)
            ExtractionService.extract(docx_document)

            self.assertEqual(
                calls,
                [
                    ("pdf", "sample.pdf"),
                    ("docx", "sample.docx"),
                ],
            )
        finally:
            ExtractionService._extract_pdf = original_pdf
            ExtractionService._extract_docx = original_docx

    @skipUnless(importlib.util.find_spec("pypdf"), "pypdf is not installed")
    def test_extracts_text_from_demo_pdf_files(self):
        for filename in [
            "sample_smart_contract_agreement.pdf",
            "demo_sales_report.pdf",
        ]:
            with self.subTest(filename=filename):
                blocks = ExtractionService._extract_pdf(str(FIXTURES_DIR / filename))

                self.assertGreater(len(blocks), 0)
                self.assertTrue(any(block.text.strip() for block in blocks))

    @skipUnless(importlib.util.find_spec("docx"), "python-docx is not installed")
    def test_extracts_text_from_demo_docx_files(self):
        for filename in [
            "sample_smart_contract_agreement.docx",
            "demo_sales_report.docx",
        ]:
            with self.subTest(filename=filename):
                blocks = ExtractionService._extract_docx(str(FIXTURES_DIR / filename))

                self.assertEqual(len(blocks), 1)
                self.assertTrue(blocks[0].text.strip())
