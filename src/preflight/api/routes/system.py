from __future__ import annotations

import os
from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from preflight.api.deps import get_audit_store
from preflight.erp.registry import get_adapter
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore, PostgresAuditStore

router = APIRouter(prefix="/api/v1/system", tags=["System Configuration & Modes"])


class SystemModesResponse(BaseModel):
    database: str = Field(..., description="Database backend type (postgresql or sqlite)")
    ocr: str = Field(..., description="OCR service readiness (live or unavailable)")
    telegram: str = Field(..., description="Telegram bot mode (live, dry_run, or unconfigured)")
    zalo: str = Field(..., description="Zalo OA mode (live, dry_run, or unconfigured)")
    erp: dict[str, str] = Field(..., description="Active ERP adapter name and mode")
    fx: str = Field(..., description="FX exchange rate provider mode (live or static)")
    environment: str = Field(..., description="Current deployment environment")
    auth_required: bool = Field(..., description="Whether API key authentication is enforced")


@router.get(
    "/modes",
    response_model=SystemModesResponse,
    summary="System Operational Modes & Integration Status",
    description="Inspect runtime operational modes of core subsystems (DB, OCR, Telegram, Zalo, ERP, FX).",
)
def get_system_modes(
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
) -> SystemModesResponse:
    env = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
    auth_req = os.getenv("PREFLIGHT_AUTH_REQUIRED", "true").lower() in ("true", "1", "yes")

    # DB mode
    db_mode = "postgresql" if isinstance(store, PostgresAuditStore) else "sqlite"

    # OCR mode
    gemini_key = os.getenv("GEMINI_API_KEY")
    ocr_mode = "live" if gemini_key else "unavailable"

    # Telegram mode
    tele_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tele_dry = os.getenv("TELEGRAM_DRY_RUN", "false").lower() in ("true", "1", "yes")
    if tele_token:
        tele_mode = "live"
    elif tele_dry:
        tele_mode = "dry_run"
    else:
        tele_mode = "unconfigured"

    # Zalo mode
    zalo_secret = os.getenv("ZALO_OA_SECRET")
    zalo_dry = os.getenv("ZALO_DRY_RUN", "false").lower() in ("true", "1", "yes")
    if zalo_secret:
        zalo_mode = "live"
    elif zalo_dry:
        zalo_mode = "dry_run"
    else:
        zalo_mode = "unconfigured"

    # ERP mode
    adapter_name = os.getenv("PREFLIGHT_ERP_ADAPTER", "MOCK_SAP")
    adapter = get_adapter(adapter_name)
    erp_info = {
        "adapter": adapter_name,
        "mode": getattr(adapter, "mode", "mock"),
    }

    # FX mode
    fx_key = os.getenv("EXCHANGE_RATE_API_KEY")
    fx_mode = "live" if fx_key else "static"

    return SystemModesResponse(
        database=db_mode,
        ocr=ocr_mode,
        telegram=tele_mode,
        zalo=zalo_mode,
        erp=erp_info,
        fx=fx_mode,
        environment=env,
        auth_required=auth_req,
    )
