from __future__ import annotations

from decimal import Decimal
from typing import Any

from preflight.ingestion.schemas import (
    DocumentType,
    ExtractedLineItem,
    ExtractedOrder,
    ExtractedOrderHeader,
    ExtractorEngine,
)
from preflight.ingestion.verifier import SelfReflectionVerifier


class MockOCREngine:
    """Mock OCR engine fixture for unit testing and offline demo flows."""

    def __init__(self):
        self.verifier = SelfReflectionVerifier()
        self.mode = "mock"

    @property
    def is_live(self) -> bool:
        return True

    def extract(self, file_bytes: bytes, filename: str, doc_type: DocumentType) -> ExtractedOrder:
        po_code = f"PO-FIXTURE-{abs(hash(filename)) % 10000:04d}"

        items = [
            ExtractedLineItem(
                sku="LAPTOP-A14",
                description="A14 Business Laptop 16GB RAM",
                quantity=2,
                unit_price=Decimal("18500000"),
                amount=Decimal("37000000"),
            ),
            ExtractedLineItem(
                sku="CAB-CAT6-3M",
                description="Cat6 Ethernet Cable 3m",
                quantity=5,
                unit_price=Decimal("72000"),
                amount=Decimal("360000"),
            ),
        ]

        subtotal = Decimal("37360000")
        header = ExtractedOrderHeader(
            po_number=po_code,
            customer="Fixture Customer Co",
            order_date="2026-09-01",
            currency="VND",
            subtotal=subtotal,
            tax_amount=Decimal("0"),
            grand_total=subtotal,
            notes="Extracted via Mock OCR Test Fixture",
        )

        math_res = self.verifier.verify(header, items)

        return ExtractedOrder(
            header=header,
            items=items,
            raw_text=f"PO {po_code} from Fixture Customer Co",
            confidence_score=0.92,
            extractor_used=ExtractorEngine.GEMINI_FLASH_VISION,
            document_type=doc_type,
            math_verification=math_res,
            mode="mock",
        )
