from __future__ import annotations

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from preflight.api.deps import get_audit_store
from preflight.config import get_settings
from preflight.erp.registry import get_adapter
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import PostgresAuditStore

router = APIRouter(prefix="/api/v1/system", tags=["System Configuration & Modes"])


class SystemModesResponse(BaseModel):
    company_name: str = Field(..., description="Configured company/workspace name")
    database: str = Field(..., description="Database backend type (postgresql or sqlite)")
    ocr: str = Field(..., description="OCR service readiness (live or unavailable)")
    telegram: str = Field(..., description="Telegram bot mode (live, dry_run, or unconfigured)")
    zalo: str = Field(..., description="Zalo OA mode (live, dry_run, or unconfigured)")
    erp: dict[str, str] = Field(..., description="Active ERP adapter name and mode")
    fx: str = Field(..., description="FX exchange rate provider mode (live or static)")
    environment: str = Field(..., description="Current deployment environment")
    auth_required: bool = Field(..., description="Whether API key authentication is enforced")
    sse: str = Field("single_process", description="SSE transport mode (redis_pubsub or single_process)")
    queue: str = Field("in_memory", description="Job queue backend (arq_redis or in_memory)")
    rate_limiter: str = Field("in_memory", description="Rate limiter backend (redis or in_memory)")


@router.get(
    "/modes",
    response_model=SystemModesResponse,
    summary="System Operational Modes & Integration Status",
    description="Inspect runtime operational modes of core subsystems (DB, OCR, Telegram, Zalo, ERP, FX).",
)
def get_system_modes(
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store=Depends(get_audit_store),
) -> SystemModesResponse:
    cfg = get_settings()

    # Dynamic env check (supporting monkeypatching in unit tests)
    env = os.getenv("PREFLIGHT_ENV", cfg.env).strip().lower()
    auth_req = os.getenv("PREFLIGHT_AUTH_REQUIRED", str(cfg.auth_required)).lower() in ("true", "1", "yes")

    # DB mode
    db_mode = "postgresql" if isinstance(store, PostgresAuditStore) else "sqlite"

    # OCR mode
    gemini_key = os.getenv("GEMINI_API_KEY", cfg.gemini_api_key or "")
    ocr_mode = "live" if gemini_key else "unavailable"

    # Telegram mode
    tele_token = os.getenv("TELEGRAM_BOT_TOKEN", cfg.telegram_bot_token or "")
    tele_dry = os.getenv("TELEGRAM_DRY_RUN", str(cfg.telegram_dry_run)).lower() in ("true", "1", "yes")
    if tele_token:
        tele_mode = "live"
    elif tele_dry:
        tele_mode = "dry_run"
    else:
        tele_mode = "unconfigured"

    # Zalo mode
    zalo_secret = os.getenv("ZALO_OA_SECRET", cfg.zalo_oa_secret or "")
    zalo_dry = os.getenv("ZALO_DRY_RUN", str(cfg.zalo_dry_run)).lower() in ("true", "1", "yes")
    if zalo_secret:
        zalo_mode = "live"
    elif zalo_dry:
        zalo_mode = "dry_run"
    else:
        zalo_mode = "unconfigured"

    # ERP mode
    adapter_name = os.getenv("PREFLIGHT_ERP_ADAPTER", cfg.erp_default_adapter)
    adapter = get_adapter(adapter_name)
    erp_info = {
        "adapter": adapter_name,
        "mode": getattr(adapter, "mode", "mock"),
    }

    # FX mode
    fx_key = os.getenv("EXCHANGE_RATE_API_KEY", cfg.exchange_rate_api_key or "")
    fx_mode = "live" if (fx_key or cfg.fx_live) else "static"

    company = os.getenv("PREFLIGHT_COMPANY_NAME", cfg.company_name).strip()

    # Redis-backed modes (SSE, Job Queue, Rate Limiter)
    redis_url = os.getenv("REDIS_URL", "").strip()
    sse_mode = "redis_pubsub" if (redis_url and redis_url.startswith("redis")) else "single_process"
    queue_mode = "arq_redis" if (redis_url and redis_url.startswith("redis")) else "in_memory"
    rate_limiter_mode = "redis" if (redis_url and redis_url.startswith("redis")) else "in_memory"

    return SystemModesResponse(
        company_name=company,
        database=db_mode,
        ocr=ocr_mode,
        telegram=tele_mode,
        zalo=zalo_mode,
        erp=erp_info,
        fx=fx_mode,
        environment=env,
        auth_required=auth_req,
        sse=sse_mode,
        queue=queue_mode,
        rate_limiter=rate_limiter_mode,
    )
