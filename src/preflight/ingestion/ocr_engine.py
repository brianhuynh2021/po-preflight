from __future__ import annotations

import base64
import json
import logging
import os
import urllib.request
from decimal import Decimal
from typing import Any

from preflight.api.errors import UpstreamUnavailable
from preflight.ingestion.schemas import (
    DocumentType,
    ExtractedLineItem,
    ExtractedOrder,
    ExtractedOrderHeader,
    ExtractorEngine,
)
from preflight.ingestion.verifier import SelfReflectionVerifier
from preflight.resilience.circuit_breaker import CircuitBreakerOpenException, vision_ai_circuit_breaker

logger = logging.getLogger("PreflightVisionOCR")


VISION_OCR_PROMPT = """
You are an expert enterprise Purchase Order (PO) and invoice extraction agent.
Analyze the provided document (PDF page or raster image) and extract all purchase order information accurately.

Extract the following JSON structure:
{
  "po_number": "Purchase order number/code",
  "customer": "Customer/Buyer company name",
  "order_date": "YYYY-MM-DD or date string",
  "currency": "VND or USD",
  "subtotal": 0.0,
  "tax_amount": 0.0,
  "grand_total": 0.0,
  "notes": "Payment/delivery notes",
  "items": [
    {
      "sku": "Product SKU/code if visible",
      "description": "Full product description text",
      "quantity": 1,
      "unit_price": 0.0,
      "amount": 0.0
    }
  ]
}

Return ONLY valid, raw JSON. Do not include markdown code block formatting.
"""


class GeminiVisionOCREngine:
    """Gemini 2.0 Flash Multimodal Vision OCR Extractor with Circuit Breaker Protection."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.verifier = SelfReflectionVerifier()

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def extract(self, file_bytes: bytes, filename: str, doc_type: DocumentType) -> ExtractedOrder:
        """Extract structured PO data from image or scanned document bytes."""
        if not self.is_live:
            raise UpstreamUnavailable(
                "OCR chưa được cấu hình. Vui lòng cấu hình GEMINI_API_KEY hoặc tải lên tệp Excel/CSV/JSON."
            )

        try:
            return vision_ai_circuit_breaker.call(
                self._call_gemini_api, file_bytes, filename, doc_type
            )
        except CircuitBreakerOpenException as exc:
            logger.error(f"Vision OCR Circuit Breaker is OPEN: {exc}")
            raise UpstreamUnavailable(
                f"Dịch vụ AI Vision tạm thời bị ngắt kết nối bảo vệ do lỗi quá nhiều lần. Vui lòng thử lại sau {exc.retry_after_sec:.0f} giây."
            ) from exc
        except Exception as exc:
            logger.error(f"Live Gemini Vision API call failed: {exc}")
            raise UpstreamUnavailable(f"Gọi Gemini Vision OCR thất bại: {exc}") from exc

    def _call_gemini_api(self, file_bytes: bytes, filename: str, doc_type: DocumentType) -> ExtractedOrder:
        mime_type = "application/pdf" if doc_type in [DocumentType.DIGITAL_PDF, DocumentType.SCANNED_PDF] else "image/png"
        b64_data = base64.b64encode(file_bytes).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": VISION_OCR_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            parsed_dict = json.loads(raw_text)

            header = ExtractedOrderHeader(
                po_number=parsed_dict.get("po_number", "PO-SCAN-01"),
                customer=parsed_dict.get("customer", "Scanned Customer"),
                order_date=parsed_dict.get("order_date"),
                currency=parsed_dict.get("currency", "VND"),
                subtotal=Decimal(str(parsed_dict.get("subtotal", 0))),
                tax_amount=Decimal(str(parsed_dict.get("tax_amount", 0))),
                grand_total=Decimal(str(parsed_dict.get("grand_total", 0))),
                notes=parsed_dict.get("notes"),
            )

            items = [
                ExtractedLineItem(
                    sku=it.get("sku", "UNKNOWN"),
                    description=it.get("description", ""),
                    quantity=int(it.get("quantity", 1)),
                    unit_price=Decimal(str(it.get("unit_price", 0))),
                    amount=Decimal(str(it.get("amount", 0))),
                )
                for it in parsed_dict.get("items", [])
            ]

            math_res = self.verifier.verify(header, items)
            confidence = 0.95 if math_res.is_valid else 0.70

            return ExtractedOrder(
                header=header,
                items=items,
                raw_text=raw_text,
                confidence_score=confidence,
                extractor_used=ExtractorEngine.GEMINI_FLASH_VISION,
                document_type=doc_type,
                math_verification=math_res,
                mode="live",
            )
