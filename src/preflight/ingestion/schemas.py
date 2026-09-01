from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    DIGITAL_PDF = "DIGITAL_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    IMAGE_RASTER = "IMAGE_RASTER"
    STRUCTURED_JSON = "STRUCTURED_JSON"
    DELIMITED_CSV = "DELIMITED_CSV"
    SPREADSHEET_EXCEL = "SPREADSHEET_EXCEL"
    PLAIN_TEXT = "PLAIN_TEXT"


class ExtractorEngine(str, Enum):
    DETERMINISTIC_PARSER = "DETERMINISTIC_PARSER"
    EXCEL_PARSER = "EXCEL_PARSER"
    GEMINI_FLASH_VISION = "GEMINI_FLASH_VISION"
    HYBRID_FALLBACK = "HYBRID_FALLBACK"


class ExtractedLineItem(BaseModel):
    sku: str = Field(..., description="Item SKU or product code if identified")
    description: str = Field(..., description="Item description text from PO")
    quantity: int = Field(..., description="Ordered quantity")
    unit_price: Decimal = Field(..., description="Unit price per item")
    amount: Decimal = Field(..., description="Line total amount (quantity * unit_price)")
    uom: str = Field(default="PCS", description="Declared Unit of Measure")



class ExtractedOrderHeader(BaseModel):
    po_number: str = Field(..., description="Purchase Order identifier")
    customer: str = Field(..., description="Customer enterprise name")
    order_date: str | None = Field(None, description="PO issuance date")
    currency: str = Field("VND", description="Declared currency (e.g. VND, USD)")
    subtotal: Decimal = Field(..., description="Declared subtotal on document")
    tax_amount: Decimal = Field(Decimal("0"), description="Declared tax or VAT amount")
    grand_total: Decimal = Field(..., description="Final payable amount")
    notes: str | None = Field(None, description="Special delivery/payment terms")


class MathVerificationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether line sums match declared total")
    calculated_items_total: Decimal = Field(..., description="Sum of line items (qty * unit_price)")
    declared_subtotal: Decimal = Field(..., description="Subtotal declared in header")
    difference: Decimal = Field(..., description="Absolute mathematical difference")
    discrepancy_detected: bool = Field(..., description="Whether discrepancy exceeds tolerance")
    message: str = Field(..., description="Audit explanation")


class ExtractedOrder(BaseModel):
    header: ExtractedOrderHeader
    items: list[ExtractedLineItem] = Field(default_factory=list)
    raw_text: str | None = None
    confidence_score: float = Field(..., description="Overall OCR/Extraction confidence (0.0 to 1.0)")
    extractor_used: ExtractorEngine
    document_type: DocumentType
    math_verification: MathVerificationResult
