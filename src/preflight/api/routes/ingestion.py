from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from preflight.api.errors import ParseError, UpstreamUnavailable, ValidationFailed
from preflight.ingestion.pipeline import IntelligentIngestionPipeline
from preflight.ingestion.schemas import ExtractedOrder
from preflight.security.rbac import Role, UserPrincipal, require_role

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
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
) -> ExtractedOrder:
    if not file.filename:
        raise ValidationFailed("Vui lòng chọn tệp để tải lên.")

    content = await file.read()
    if not content:
        raise ValidationFailed("Tệp tải lên rỗng.")

    try:
        extracted, _ = _INGESTION_PIPELINE.process_file_bytes(content, filename=file.filename)
        return extracted
    except UpstreamUnavailable:
        raise UpstreamUnavailable(
            "OCR chưa được cấu hình hoặc dịch vụ AI tạm thời không khả dụng. Vui lòng tải lên Excel/CSV hoặc nhập tay tại Staging Studio."
        )
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Không thể xử lý tệp '{file.filename}': {exc}")
