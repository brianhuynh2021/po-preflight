from __future__ import annotations

import hashlib
import json
import logging
import os
import smtplib
import threading
import time
from email.message import EmailMessage
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from preflight.api.deps import get_audit_store
from preflight.api.errors import RateLimited
from preflight.security.rbac import Role, require_role
from preflight.store import BaseAuditStore

logger = logging.getLogger("preflight.leads")

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])

# Thread-safe in-memory IP rate limiter for lead submissions: 5 requests / 60s per IP
_ip_requests_lock = threading.Lock()
_ip_requests: dict[str, list[float]] = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW_SECONDS = 60.0


def check_lead_rate_limit(client_ip: str) -> None:
    now = time.time()
    with _ip_requests_lock:
        timestamps = _ip_requests.get(client_ip, [])
        # Prune old timestamps
        timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
        if len(timestamps) >= RATE_LIMIT_MAX:
            _ip_requests[client_ip] = timestamps
            raise RateLimited("Bạn đã gửi quá 5 yêu cầu trong 1 phút. Vui lòng thử lại sau.")
        timestamps.append(now)
        _ip_requests[client_ip] = timestamps


class CreateLeadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Họ và tên người liên hệ")
    company: str = Field(..., min_length=1, max_length=255, description="Tên doanh nghiệp / Nhà phân phối")
    phone: str = Field(..., min_length=6, max_length=64, description="Số điện thoại")
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255, description="Email doanh nghiệp")
    erp: str | None = Field(default=None, description="Hệ thống ERP đang sử dụng (MISA, Bravo, Fast, SAP...)")
    volume: str | None = Field(default=None, description="Số lượng đơn hàng trung bình mỗi ngày")
    note: str | None = Field(default=None, description="Nhu cầu cụ thể hoặc ghi chú thêm")
    website: str | None = Field(default=None, description="Honeypot field (hidden)")
    hp: str | None = Field(default=None, description="Honeypot field (hidden)")


def send_smtp_notification(lead: dict[str, Any]) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        logger.info(
            "SMTP not configured; logged lead notification: name=%s, company=%s, phone=%s",
            lead.get("name"),
            lead.get("company"),
            lead.get("phone"),
        )
        return

    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")
        to_email = os.getenv("CONTACT_NOTIFICATION_EMAIL", "contact@popreflight.vn")

        msg = EmailMessage()
        msg["Subject"] = f"[PO Preflight] Khách hàng mới đăng ký Pilot: {lead.get('company')}"
        msg["From"] = os.getenv("SMTP_FROM", "no-reply@popreflight.vn")
        msg["To"] = to_email

        body = (
            f"Thông tin khách hàng đăng ký trải nghiệm PO Preflight:\n\n"
            f"- Họ tên: {lead.get('name')}\n"
            f"- Doanh nghiệp: {lead.get('company')}\n"
            f"- Số điện thoại: {lead.get('phone')}\n"
            f"- Email: {lead.get('email')}\n"
            f"- ERP: {lead.get('erp') or 'Chưa rõ'}\n"
            f"- Số đơn/ngày: {lead.get('volume') or 'Chưa rõ'}\n"
            f"- Ghi chú: {lead.get('note') or 'Không có'}\n"
            f"- Thời gian: {lead.get('created_at')}\n"
        )
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10.0) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("Sent SMTP notification for lead id=%s to %s", lead.get("id"), to_email)
    except Exception as exc:
        logger.warning("Failed to send SMTP notification for lead: %s", exc)


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_lead(
    payload: CreateLeadRequest,
    request: Request,
    store: BaseAuditStore = Depends(get_audit_store),
) -> Response:
    client_ip = request.client.host if request.client else "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    # Rate limiting check (5/min per IP)
    check_lead_rate_limit(client_ip)

    # Anti-bot Honeypot check: if filled, return 200 dummy response without writing to database
    if payload.website or payload.hp:
        logger.info("Bot honeypot triggered by IP %s; returning dummy 200", client_ip)
        return Response(
            status_code=status.HTTP_200_OK,
            content=json.dumps({
                "success": True,
                "message": "Đã nhận, chúng tôi liên hệ trong 1 ngày làm việc",
            }),
            media_type="application/json",
        )

    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    lead = store.create_lead(
        name=payload.name.strip(),
        company=payload.company.strip(),
        phone=payload.phone.strip(),
        email=str(payload.email).strip().lower(),
        erp=payload.erp.strip() if payload.erp else None,
        volume=payload.volume.strip() if payload.volume else None,
        note=payload.note.strip() if payload.note else None,
        ip_hash=ip_hash,
    )

    send_smtp_notification(lead)

    return Response(
        status_code=status.HTTP_201_CREATED,
        content=json.dumps({
            "success": True,
            "message": "Đã nhận, chúng tôi liên hệ trong 1 ngày làm việc",
            "lead": lead,
        }),
        media_type="application/json",
    )


@router.get("", dependencies=[Depends(require_role(Role.ADMIN))])
async def list_leads(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    store: BaseAuditStore = Depends(get_audit_store),
) -> list[dict[str, Any]]:
    return store.list_leads(limit=limit, offset=offset)
