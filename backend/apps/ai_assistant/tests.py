import importlib.util
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_assistant.api.serializers import DocumentUploadSerializer
from apps.ai_assistant.models import Document, DocumentChunk
from apps.ai_assistant.services.extraction_service import ExtractionService
from apps.core.models.company import Company
from apps.users.models import User


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


class KeywordSearchAPITestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls._media_root = tempfile.TemporaryDirectory()
        cls._override = override_settings(MEDIA_ROOT=cls._media_root.name)
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        cls._media_root.cleanup()

    def setUp(self):
        self.company = Company.objects.create(name="Keyword Company")
        self.other_company = Company.objects.create(name="Other Company")
        self.user = User.objects.create_user(
            email="keyword@example.com",
            password="password",
            full_name="Keyword User",
            company=self.company,
        )
        self.other_user = User.objects.create_user(
            email="other-keyword@example.com",
            password="password",
            full_name="Other Keyword User",
            company=self.other_company,
        )
        self.document = self._create_document(self.company, self.user, "keyword.pdf")
        self.other_document = self._create_document(
            self.other_company,
            self.other_user,
            "other-keyword.pdf",
        )

        self.matching_chunk = DocumentChunk.objects.create(
            document=self.document,
            company=self.company,
            chunk_index=1,
            text="Revenue grew after the Alpha launch. alpha adoption increased.",
            page_number=2,
        )
        DocumentChunk.objects.create(
            document=self.document,
            company=self.company,
            chunk_index=2,
            text="Inventory levels stayed flat during the same period.",
            page_number=3,
        )
        self.second_matching_chunk = DocumentChunk.objects.create(
            document=self.document,
            company=self.company,
            chunk_index=3,
            text="Beta revenue was mentioned once.",
            page_number=None,
        )
        DocumentChunk.objects.create(
            document=self.other_document,
            company=self.other_company,
            chunk_index=1,
            text="Alpha revenue from another company must stay hidden.",
            page_number=1,
        )

    def test_keyword_search_returns_flat_keyword_results(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            f"/api/ai-assistant/documents/{self.document.id}/keyword-search/",
            {"query": "alpha revenue", "top_k": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["chunk_id"], str(self.matching_chunk.id))
        self.assertEqual(response.data[0]["chunk_index"], 1)
        self.assertEqual(response.data[0]["page_number"], 2)
        self.assertEqual(response.data[0]["score"], 3.0)
        self.assertEqual(response.data[0]["method"], "keyword")
        self.assertIn("Alpha launch", response.data[0]["text"])
        self.assertEqual(
            {result["chunk_id"] for result in response.data},
            {str(self.matching_chunk.id), str(self.second_matching_chunk.id)},
        )

    def test_keyword_search_respects_top_k(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            f"/api/ai-assistant/documents/{self.document.id}/keyword-search/",
            {"query": "revenue", "top_k": 1},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_keyword_search_rejects_other_company_document(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            f"/api/ai-assistant/documents/{self.other_document.id}/keyword-search/",
            {"query": "alpha", "top_k": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_keyword_search_requires_authenticated_user(self):
        response = self.client.post(
            f"/api/ai-assistant/documents/{self.document.id}/keyword-search/",
            {"query": "alpha", "top_k": 5},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def _create_document(self, company, user, filename):
        return Document.objects.create(
            company=company,
            uploaded_by=user,
            file=SimpleUploadedFile(
                filename,
                b"demo content",
                content_type="application/pdf",
            ),
        )
