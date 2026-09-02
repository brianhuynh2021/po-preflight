from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from preflight.api.errors import ParseError
from preflight.ingestion.detector import detect_document_type
from preflight.ingestion.ocr_engine import GeminiVisionOCREngine
from preflight.ingestion.schemas import (
    DocumentType,
    ExtractedLineItem,
    ExtractedOrder,
    ExtractedOrderHeader,
    ExtractorEngine,
)
from preflight.ingestion.verifier import SelfReflectionVerifier
from preflight.models import LineItem, Order
from preflight.parsers import parse_order_content


class IntelligentIngestionPipeline:
    """Enterprise Multimodal PO Ingestion Pipeline.
    Cascades from Zero-Token Deterministic Parsers to Gemini 2.0 Flash Vision OCR without silent fallbacks.
    """

    def __init__(self, gemini_api_key: str | None = None, ocr_engine: Any | None = None):
        self.ocr_engine = ocr_engine or GeminiVisionOCREngine(api_key=gemini_api_key)
        self.verifier = SelfReflectionVerifier()

    def process_file_bytes(self, file_bytes: bytes, filename: str) -> tuple[ExtractedOrder, Order]:
        """Ingest document bytes, execute extraction, and produce validated domain Order."""
        doc_type = detect_document_type(file_bytes, filename)

        # -------------------------------------------------------------
        # 1. Native Excel Spreadsheets (.xlsx / .xls / .xlsm)
        # -------------------------------------------------------------
        if doc_type == DocumentType.SPREADSHEET_EXCEL:
            try:
                from preflight.ingestion.excel_parser import ExcelExtractor

                extractor = ExcelExtractor()
                return extractor.extract(file_bytes, filename)
            except Exception as exc:
                raise ParseError(f"Lỗi khi đọc bảng tính Excel '{filename}': {exc}") from exc

        # -------------------------------------------------------------
        # 2. Zero-Token Deterministic Path (JSON / CSV / TXT)
        # -------------------------------------------------------------
        if doc_type in [
            DocumentType.STRUCTURED_JSON,
            DocumentType.DELIMITED_CSV,
            DocumentType.PLAIN_TEXT,
        ]:
            try:
                text_content = file_bytes.decode("utf-8", errors="replace")
                domain_order = parse_order_content(text_content, suffix=Path(filename).suffix)

                items = [
                    ExtractedLineItem(
                        sku=it.sku,
                        description=it.sku,
                        quantity=it.quantity,
                        unit_price=it.unit_price,
                        amount=it.quantity * it.unit_price,
                    )
                    for it in domain_order.items
                ]
                subtotal = domain_order.total
                header = ExtractedOrderHeader(
                    po_number=domain_order.po_number,
                    customer=domain_order.customer,
                    order_date=None,
                    currency=domain_order.currency,
                    subtotal=subtotal,
                    tax_amount=Decimal("0"),
                    grand_total=subtotal,
                    notes="Parsed via Zero-Token Deterministic Engine",
                )
                math_res = self.verifier.verify(header, items)

                extracted = ExtractedOrder(
                    header=header,
                    items=items,
                    raw_text=text_content[:200],
                    confidence_score=1.0,
                    extractor_used=ExtractorEngine.DETERMINISTIC_PARSER,
                    document_type=doc_type,
                    math_verification=math_res,
                    mode="live",
                )
                return extracted, domain_order
            except Exception as exc:
                raise ParseError(f"Không thể phân tích tệp {doc_type.value} '{filename}': {exc}") from exc

        # -------------------------------------------------------------
        # 3. Digital PDF Path (Attempt deterministic text extraction, fallback to OCR)
        # -------------------------------------------------------------
        if doc_type == DocumentType.DIGITAL_PDF:
            try:
                text_content = file_bytes.decode("utf-8", errors="ignore")
                domain_order = parse_order_content(text_content, suffix=".pdf")
                if domain_order.items:
                    items = [
                        ExtractedLineItem(
                            sku=it.sku,
                            description=it.sku,
                            quantity=it.quantity,
                            unit_price=it.unit_price,
                            amount=it.quantity * it.unit_price,
                        )
                        for it in domain_order.items
                    ]
                    subtotal = domain_order.total
                    header = ExtractedOrderHeader(
                        po_number=domain_order.po_number,
                        customer=domain_order.customer,
                        order_date=None,
                        currency="VND",
                        subtotal=subtotal,
                        tax_amount=Decimal("0"),
                        grand_total=subtotal,
                        notes="Parsed via Zero-Token Deterministic PDF Engine",
                    )
                    math_res = self.verifier.verify(header, items)

                    extracted = ExtractedOrder(
                        header=header,
                        items=items,
                        raw_text=text_content[:200],
                        confidence_score=1.0,
                        extractor_used=ExtractorEngine.DETERMINISTIC_PARSER,
                        document_type=doc_type,
                        math_verification=math_res,
                        mode="live",
                    )
                    return extracted, domain_order
            except Exception:
                pass  # For digital PDF with embedded images or layout issues, fall through to Vision OCR

        # -------------------------------------------------------------
        # 4. Multimodal Vision OCR Path (Scanned PDF / Photos / Raster Images)
        # -------------------------------------------------------------
        extracted = self.ocr_engine.extract(file_bytes, filename, doc_type)

        # Convert ExtractedOrder to Domain Order
        domain_items = [
            LineItem(
                sku=it.sku,
                quantity=it.quantity,
                unit_price=it.unit_price,
            )
            for it in extracted.items
        ]
        domain_order = Order(
            po_number=extracted.header.po_number,
            customer=extracted.header.customer,
            items=domain_items,
            currency=extracted.header.currency,
        )

        return extracted, domain_order


# Backward compatibility alias
IngestionPipeline = IntelligentIngestionPipeline
