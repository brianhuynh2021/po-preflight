from __future__ import annotations

import io
from pathlib import Path

from preflight.ingestion.schemas import DocumentType


def detect_document_type(file_bytes: bytes, filename: str = "document") -> DocumentType:
    """Classify document format: Digital PDF, Scanned PDF, Raster Image, JSON, CSV, or Text."""
    name_lower = filename.lower()

    if name_lower.endswith(".json"):
        return DocumentType.STRUCTURED_JSON
    if name_lower.endswith(".csv"):
        return DocumentType.DELIMITED_CSV
    if any(name_lower.endswith(ext) for ext in [".xlsx", ".xls", ".xlsm", ".xlsb"]):
        return DocumentType.SPREADSHEET_EXCEL
    if name_lower.endswith(".txt"):
        return DocumentType.PLAIN_TEXT
    if any(name_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]):
        return DocumentType.IMAGE_RASTER


    # Check for PDF
    if name_lower.endswith(".pdf") or file_bytes.startswith(b"%PDF"):
        # Check if PDF contains extractable text layer
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            total_text = ""
            for page in reader.pages[:3]:
                text = page.extract_text() or ""
                total_text += text.strip()

            if len(total_text) > 30:
                return DocumentType.DIGITAL_PDF
            return DocumentType.SCANNED_PDF
        except Exception:
            return DocumentType.SCANNED_PDF

    return DocumentType.PLAIN_TEXT
