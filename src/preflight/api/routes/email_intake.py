from __future__ import annotations

import os
from typing import Any
from fastapi import APIRouter, Depends

from preflight.api.deps import get_store
from preflight.intake.email import EmailIntakeConfig, EmailIntakeService
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import BaseAuditStore

router = APIRouter(prefix="/api/v1/intake/email", tags=["Email Intake & Ingestion"])


@router.get(
    "/status",
    summary="Get Email Intake Configuration & Health Status",
)
def get_email_intake_status(
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
) -> dict[str, Any]:
    config = EmailIntakeConfig.from_env()
    logs = store.list_email_inbox_logs(limit=10)
    last_log = logs[0] if logs else None
    
    error_count = sum(1 for log in logs if log.get("status") in ("ERROR", "IGNORED"))

    return {
        "enabled": config.enabled,
        "imap_configured": bool(config.imap_host and config.imap_user),
        "imap_host": config.imap_host or None,
        "imap_folder": config.imap_folder,
        "smtp_configured": bool(config.smtp_host),
        "poll_interval_seconds": config.poll_interval_seconds,
        "last_polled_at": last_log.get("created_at") if last_log else None,
        "recent_error_count": error_count,
        "total_recent_logs": len(logs),
    }


@router.post(
    "/poll",
    summary="Trigger On-Demand Email Intake Mailbox Poll",
)
def trigger_email_poll(
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.SALES_ADMIN)),
) -> dict[str, Any]:
    service = EmailIntakeService(store=store)
    results = service.poll_once()
    
    return {
        "status": "success",
        "processed_count": len(results),
        "results": [
            {
                "message_id": r.message_id,
                "sender": r.sender_email,
                "subject": r.subject,
                "status": r.status,
                "orders_created": r.orders_created,
                "analysis_ids": r.analysis_ids,
                "po_numbers": r.po_numbers,
                "auto_reply_sent": r.auto_reply_sent,
                "customer_resolved": r.customer_resolved,
                "error_message": r.error_message,
            }
            for r in results
        ],
    }


@router.get(
    "/logs",
    summary="List Recent Email Inbox Ingestion Logs",
)
def list_email_logs(
    limit: int = 50,
    store: BaseAuditStore = Depends(get_store),
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
) -> list[dict[str, Any]]:
    return store.list_email_inbox_logs(limit=limit)
