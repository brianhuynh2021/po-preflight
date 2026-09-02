from __future__ import annotations

import io
import json
import unittest
from decimal import Decimal

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.ingestion.detector import detect_document_type
from preflight.ingestion.ocr_engine import GeminiVisionOCREngine
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.ingestion.schemas import (
    DocumentType,
    ExtractedLineItem,
    ExtractedOrderHeader,
    ExtractorEngine,
)
from preflight.ingestion.verifier import SelfReflectionVerifier
from preflight.security.rate_limiter import global_rate_limiter


class TestIngestionAndVisionOCR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, headers={"X-API-Key": "pf_dev_adm_9901"})
        cls.pipeline = IntelligentIngestionPipeline()
        cls.verifier = SelfReflectionVerifier()

    def setUp(self):
        global_rate_limiter.reset()


    def test_document_type_detection(self):
        """Test accurate classification of document types."""
        self.assertEqual(detect_document_type(b"{}", "order.json"), DocumentType.STRUCTURED_JSON)
        self.assertEqual(detect_document_type(b"sku,qty", "order.csv"), DocumentType.DELIMITED_CSV)
        self.assertEqual(detect_document_type(b"hello", "order.txt"), DocumentType.PLAIN_TEXT)
        self.assertEqual(detect_document_type(b"\x89PNG\r\n\x1a\n", "po_photo.png"), DocumentType.IMAGE_RASTER)
        self.assertEqual(detect_document_type(b"\xff\xd8\xff", "po_receipt.jpg"), DocumentType.IMAGE_RASTER)
        self.assertEqual(detect_document_type(b"%PDF-1.4", "scanned.pdf"), DocumentType.SCANNED_PDF)

    def test_self_reflection_math_verifier_valid(self):
        """Test verifier marks balanced calculations as valid."""
        header = ExtractedOrderHeader(
            po_number="PO-MOCK-01",
            customer="Acme Corp",
            currency="VND",
            subtotal=Decimal("37000000"),
            tax_amount=Decimal("0"),
            grand_total=Decimal("37000000"),
        )
        items = [
            ExtractedLineItem(
                sku="LAPTOP-A14",
                description="Laptop",
                quantity=2,
                unit_price=Decimal("18500000"),
                amount=Decimal("37000000"),
            )
        ]
        result = self.verifier.verify(header, items)
        self.assertTrue(result.is_valid)
        self.assertFalse(result.discrepancy_detected)
        self.assertEqual(result.difference, Decimal("0"))
        self.assertIn("Math verified 100%", result.message)

    def test_self_reflection_math_verifier_discrepancy(self):
        """Test verifier flags math discrepancies when line items don't match header."""
        header = ExtractedOrderHeader(
            po_number="PO-ERR-01",
            customer="Acme Corp",
            currency="VND",
            subtotal=Decimal("50000000"),  # Header says 50M
            tax_amount=Decimal("0"),
            grand_total=Decimal("50000000"),
        )
        items = [
            ExtractedLineItem(
                sku="LAPTOP-A14",
                description="Laptop",
                quantity=2,
                unit_price=Decimal("18500000"),  # Actual sum is 37M (13M gap)
                amount=Decimal("37000000"),
            )
        ]
        result = self.verifier.verify(header, items)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.discrepancy_detected)
        self.assertEqual(result.difference, Decimal("13000000"))
        self.assertIn("Math discrepancy detected", result.message)

    def test_pipeline_deterministic_json_ingestion(self):
        """Test pipeline fast-paths structured JSON through zero-token deterministic engine."""
        sample_json = {
            "po_number": "PO-DET-101",
            "customer": "Apex Solutions",
            "items": [
                {"sku": "CAB-CAT6-3M", "quantity": 10, "unit_price": 72000},
            ],
        }
        bytes_data = json.dumps(sample_json).encode("utf-8")
        extracted, domain_order = self.pipeline.process_file_bytes(bytes_data, "order.json")

        self.assertEqual(extracted.extractor_used, ExtractorEngine.DETERMINISTIC_PARSER)
        self.assertEqual(extracted.confidence_score, 1.0)
        self.assertEqual(extracted.header.po_number, "PO-DET-101")
        self.assertEqual(len(extracted.items), 1)
        self.assertEqual(domain_order.po_number, "PO-DET-101")

    def test_pipeline_scanned_image_vision_ocr_fallback(self):
        """Test pipeline falls back to Gemini Vision OCR for raster images."""
        from tests.fixtures.mock_ocr import MockOCREngine
        self.pipeline.ocr_engine = MockOCREngine()
        mock_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        extracted, domain_order = self.pipeline.process_file_bytes(mock_image_bytes, "mobile_photo.png")

        self.assertEqual(extracted.extractor_used, ExtractorEngine.GEMINI_FLASH_VISION)
        self.assertGreater(extracted.confidence_score, 0.8)
        self.assertTrue(extracted.math_verification.is_valid)
        self.assertGreater(len(domain_order.items), 0)

    def test_api_ingest_extract_endpoint(self):
        """Test POST /api/v1/ingest/extract endpoint."""
        sample_po = {
            "po_number": "PO-API-INGEST-77",
            "customer": "Cloud Gateway Corp",
            "items": [
                {"sku": "LAPTOP-A14", "quantity": 1, "unit_price": 18500000},
            ],
        }
        file_payload = {"file": ("order.json", json.dumps(sample_po), "application/json")}
        res = self.client.post("/api/v1/ingest/extract", files=file_payload)

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["header"]["po_number"], "PO-API-INGEST-77")
        self.assertEqual(data["extractor_used"], "DETERMINISTIC_PARSER")
        self.assertTrue(data["math_verification"]["is_valid"])


if __name__ == "__main__":
    unittest.main()
