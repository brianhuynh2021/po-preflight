from __future__ import annotations

import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status

import time
from pydantic import BaseModel, Field
from preflight.api.deps import get_store
from preflight.api.events import event_bus
from preflight.bot.schemas import BotConfigStatus, BotNotificationResult, TelegramUpdate
from preflight.bot.telegram import TelegramBotService
from preflight.bot.zalo import ZaloBotService
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore

router = APIRouter(prefix="/api/v1/bot", tags=["Multi-Channel Approval Bots (Telegram & Zalo)"])


class LinkCodeResponse(BaseModel):
    code: str = Field(..., description="6-character alphanumeric linking code")
    expires_in: int = Field(600, description="Lifetime in seconds (10 minutes)")
    instructions: str = Field(..., description="Usage instructions")


@router.post(
    "/link-code",
    response_model=LinkCodeResponse,
    summary="Generate Self-Service Channel Linking Code",
    description="Generate a secure 6-character code valid for 10 minutes to link Telegram or Zalo accounts.",
)
def generate_channel_link_code(
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_store),
) -> LinkCodeResponse:
    role_val = user.role.name if hasattr(user.role, "name") else str(user.role)
    code = store.create_channel_link_code(
        user_id=user.username,
        display_name=getattr(user, "display_name", None) or user.username,
        role=role_val,
        expires_in_seconds=600,
    )
    return LinkCodeResponse(
        code=code,
        expires_in=600,
        instructions="Gửi lệnh /link <MÃ> cho PO Preflight Telegram Bot để liên kết tài khoản.",
    )


@router.get(
    "/status",
    response_model=BotConfigStatus,
    summary="Check Bot Channel Status",
    description="Inspect whether Telegram and Zalo OA bot credentials and webhooks are active.",
)
def get_bot_status() -> BotConfigStatus:
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
    zalo_app_id = os.getenv("ZALO_APP_ID")

    return BotConfigStatus(
        telegram_enabled=bool(telegram_token and telegram_chat),
        telegram_chat_id=telegram_chat,
        zalo_enabled=bool(zalo_app_id),
        webhook_url="/api/v1/bot/telegram/webhook",
    )


@router.post(
    "/telegram/notify/{order_id}",
    response_model=BotNotificationResult,
    summary="Dispatch Telegram PO Approval Card",
    description="Generate and send an interactive PO Preflight alert card with 1-click inline action buttons to Telegram.",
)
def send_telegram_alert(
    order_id: int,
    request: Request,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_store),
) -> BotNotificationResult:
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order #{order_id} not found in store.")

    base_url = str(request.base_url).rstrip("/")
    bot_service = TelegramBotService(store=store)
    return bot_service.send_order_alert(order, web_base_url=base_url)


@router.post(
    "/telegram/set-webhook",
    summary="Register Telegram Webhook",
    description="Register public webhook URL and secret token with Telegram Bot API.",
)
def set_telegram_webhook(
    webhook_url: str,
    secret_token: str | None = None,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    bot_service = TelegramBotService(store=store)
    return bot_service.set_webhook(webhook_url=webhook_url, secret_token=secret_token)


from pydantic import BaseModel, Field

class LinkChannelIdentityRequest(BaseModel):
    external_id: str = Field(..., description="External channel identifier (e.g. Telegram numeric ID or Zalo UID)")
    user_id: str = Field(..., description="Internal system user ID")
    display_name: str | None = Field(None, description="Human display name")
    role: Role = Field(Role.MANAGER, description="Authorized role for this channel identity")


@router.post(
    "/telegram/link",
    summary="Link Telegram User ID with System Identity",
    description="Authorize a Telegram account for interactive button decisions.",
)
def link_telegram_identity(
    payload: LinkChannelIdentityRequest,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    store.upsert_channel_identity(
        channel="telegram",
        external_id=payload.external_id,
        user_id=payload.user_id,
        display_name=payload.display_name or payload.user_id,
        role=payload.role.value,
    )
    return {
        "success": True,
        "message": f"Linked Telegram user {payload.external_id} to internal user {payload.user_id} with role {payload.role.value}.",
    }


@router.post(
    "/zalo/link",
    summary="Link Zalo User ID with System Identity",
    description="Authorize a Zalo OA account for interactive button decisions.",
)
def link_zalo_identity(
    payload: LinkChannelIdentityRequest,
    user: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    store.upsert_channel_identity(
        channel="zalo",
        external_id=payload.external_id,
        user_id=payload.user_id,
        display_name=payload.display_name or payload.user_id,
        role=payload.role.value,
    )
    return {
        "success": True,
        "message": f"Linked Zalo user {payload.external_id} to internal user {payload.user_id} with role {payload.role.value}.",
    }


@router.post(
    "/telegram/webhook",
    summary="Telegram Webhook Receiver",
    description="Receive updates from Telegram Bot API when managers click inline approval buttons or send commands.",
)
async def telegram_webhook(
    request: Request,
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    # Mandatory Secret Token Guard across all environments
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_SECRET_TOKEN")
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram webhook secret token is not configured on server.",
        )

    token_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not token_header or token_header != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid or missing Telegram webhook secret token.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    bot_service = TelegramBotService(store=store)

    # 1. Handle Inline Button Callback Query
    if "callback_query" in body:
        cb = body["callback_query"]
        cb_id = str(cb.get("id", ""))
        data = str(cb.get("data", ""))
        from_user = cb.get("from", {})
        from_user_id = str(from_user.get("id", ""))
        username = from_user.get("username", from_user.get("first_name", "Manager"))
        msg = cb.get("message", {})
        msg_id = msg.get("message_id")
        chat_id = msg.get("chat", {}).get("id")

        result = bot_service.handle_callback_action(
            callback_data=data,
            from_user_id=from_user_id,
            from_username=username,
            callback_query_id=cb_id,
            chat_id=chat_id,
            message_id=msg_id,
        )

        if result.get("success"):
            event_bus.publish(
                "order.decided",
                {
                    "order_id": str(result.get("order_id", "")),
                    "decision": result.get("decision", ""),
                    "actor": result.get("decided_by", ""),
                },
            )

        return {
            "ok": True,
            "handled_event": "callback_query",
            "result": result,
        }

    # 2. Handle Text Command (e.g. /status, /orders, /link)
    if "message" in body and "text" in body["message"]:
        text = body["message"]["text"].strip()
        chat_id = body["message"]["chat"]["id"]

        if text.startswith("/link"):
            parts = text.split(None, 1)
            from_user = body["message"].get("from", {})
            from_user_id = str(from_user.get("id", ""))

            if len(parts) < 2 or not parts[1].strip():
                reply = "Cú pháp: <code>/link &lt;MÃ_LIÊN_KẾT&gt;</code>. Lấy mã liên kết tại Cài đặt tài khoản trên Web Portal."
                return {
                    "ok": True,
                    "handled_event": "link_command",
                    "reply": reply,
                    "linked": False,
                }

            link_code = parts[1].strip()
            res = store.consume_channel_link_code(link_code)
            if not res:
                reply = "❌ Mã liên kết không hợp lệ hoặc đã được sử dụng. Vui lòng tạo mã mới trên Web Portal."
                return {
                    "ok": True,
                    "handled_event": "link_command",
                    "reply": reply,
                    "linked": False,
                    "error": "INVALID_CODE",
                }
            if res.get("expired"):
                reply = "⚠️ Mã liên kết đã hết hạn (chỉ có hiệu lực trong 10 phút). Vui lòng tạo mã mới trên Web Portal."
                return {
                    "ok": True,
                    "handled_event": "link_command",
                    "reply": reply,
                    "linked": False,
                    "error": "EXPIRED_CODE",
                }

            store.upsert_channel_identity(
                channel="telegram",
                external_id=from_user_id,
                user_id=res["user_id"],
                display_name=res["display_name"],
                role=res["role"],
            )
            reply = f"✅ Liên kết tài khoản thành công! Xin chào <b>{res['display_name']}</b> (Vai trò: <code>{res['role']}</code>)."
            return {
                "ok": True,
                "handled_event": "link_command",
                "reply": reply,
                "linked": True,
                "user_id": res["user_id"],
                "role": res["role"],
            }

        if text.startswith("/orders"):
            orders = store.list_orders(limit=5)
            return {
                "ok": True,
                "handled_event": "message_command",
                "command": "/orders",
                "orders_count": len(orders),
            }

        return {
            "ok": True,
            "handled_event": "message",
            "reply": "PO Preflight Bot active. Use inline buttons on alert cards to approve orders.",
        }

    return {"ok": True, "handled_event": "ignored"}


@router.post(
    "/zalo/notify/{order_id}",
    response_model=BotNotificationResult,
    summary="Dispatch Zalo OA Notification",
    description="Generate and dispatch a Zalo ZNS / OA transaction alert card.",
)
def send_zalo_alert(
    order_id: int,
    request: Request,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_store),
) -> BotNotificationResult:
    order = store.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order #{order_id} not found.")

    base_url = str(request.base_url).rstrip("/")
    zalo_service = ZaloBotService(store=store)
    return zalo_service.send_order_alert(order, web_base_url=base_url)


@router.post(
    "/zalo/webhook",
    summary="Zalo OA Webhook Receiver",
    description="Receive user button click events from Zalo OA with HMAC-SHA256 signature and anti-replay verification.",
)
async def zalo_webhook(
    request: Request,
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    raw_body = await request.body()
    signature = request.headers.get("X-Zalo-Signature", "")
    timestamp = request.headers.get("X-Zalo-Timestamp", "")

    # 1. Verify timestamp is within ±5 minutes (300 seconds)
    if timestamp:
        try:
            ts_val = float(timestamp)
            if ts_val > 1e11:
                ts_val = ts_val / 1000.0
            if abs(time.time() - ts_val) > 300.0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zalo webhook timestamp outside valid ±5 minutes window.",
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Zalo webhook timestamp.",
            )

    zalo_service = ZaloBotService(store=store)

    if not zalo_service.secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zalo webhook secret key is not configured on server.",
        )

    if not signature or not zalo_service.verify_webhook_signature(raw_body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid or missing Zalo webhook signature.")

    try:
        body = await request.json()
    except Exception:
        body = {}

    # 2. Anti-replay deduplication: check and record event_id
    event_id = str(body.get("event_id") or body.get("message", {}).get("msg_id") or "")
    if event_id:
        is_fresh = store.record_processed_webhook_event(channel="zalo", event_id=event_id)
        if not is_fresh:
            return {"ok": True, "status": "ignored", "reason": "replay_detected"}

    result = zalo_service.process_webhook_event(body)

    if result.get("status") == "error":
        err_code = result.get("status_code", 400)
        raise HTTPException(status_code=err_code, detail=result.get("message", "Zalo decision failed"))

    if result.get("status") == "success":
        event_bus.publish(
            "order.decided",
            {
                "order_id": result.get("po_number", ""),
                "decision": result.get("action", ""),
                "actor": f"zalo:{result.get('result', {}).get('actor', 'manager')}",
            },
        )

    return {"ok": True, "result": result}




