from __future__ import annotations

from typing import Any
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.ingestion.schemas import ExtractedOrder

router = APIRouter(prefix="/api/v1/ingest", tags=["Multimodal Ingestion & Vision OCR"])

_INGESTION_PIPELINE = IntelligentIngestionPipeline()


@router.post(
    "/extract",
    summary="Extract Structured PO from Scanned PDF / Image / Digital Document",
    description=(
        "Upload a document (PDF, PNG, JPG, CSV, JSON) to extract header, line items, and financial totals. "
        "Applies Gemini 2.0 Flash Vision OCR for scans and self-reflection mathematical verification."
    ),
    response_model=ExtractedOrder,
)
async def extract_purchase_order(
    file: UploadFile = File(..., description="Purchase order document (PDF, PNG, JPG, CSV, JSON)"),
) -> ExtractedOrder:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        extracted, _ = _INGESTION_PIPELINE.process_file_bytes(content, filename=file.filename)
        return extracted
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {exc}",
        )
