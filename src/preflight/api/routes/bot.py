from __future__ import annotations

import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request

from preflight.api.deps import get_store
from preflight.api.events import event_bus
from preflight.bot.schemas import BotConfigStatus, BotNotificationResult, TelegramUpdate
from preflight.bot.telegram import TelegramBotService
from preflight.bot.zalo import ZaloBotService
from preflight.store import AuditStore

router = APIRouter(prefix="/api/v1/bot", tags=["Multi-Channel Approval Bots (Telegram & Zalo)"])


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
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    bot_service = TelegramBotService(store=store)
    return bot_service.set_webhook(webhook_url=webhook_url, secret_token=secret_token)


@router.post(
    "/telegram/webhook",
    summary="Telegram Webhook Receiver",
    description="Receive updates from Telegram Bot API when managers click inline approval buttons or send commands.",
)
async def telegram_webhook(
    request: Request,
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    # Anti-Spoofing Guard: Verify Secret Token if configured
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_SECRET_TOKEN")
    if expected_secret:
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
        username = from_user.get("username", from_user.get("first_name", "Manager"))

        result = bot_service.handle_callback_action(
            callback_data=data,
            from_username=username,
            callback_query_id=cb_id,
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

    # 2. Handle Text Command (e.g. /status, /orders)
    if "message" in body and "text" in body["message"]:
        text = body["message"]["text"].strip()
        chat_id = body["message"]["chat"]["id"]

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
    description="Receive user button click events from Zalo OA with HMAC-SHA256 signature verification.",
)
async def zalo_webhook(
    request: Request,
    store: AuditStore = Depends(get_store),
) -> dict[str, Any]:
    raw_body = await request.body()
    signature = request.headers.get("X-Zalo-Signature", "")
    timestamp = request.headers.get("X-Zalo-Timestamp", "")

    zalo_service = ZaloBotService(store=store)
    if signature and not zalo_service.verify_webhook_signature(raw_body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Zalo webhook signature.")

    try:
        body = await request.json()
    except Exception:
        body = {}

    result = zalo_service.process_webhook_event(body)

    if result.get("status") == "success":
        event_bus.publish(
            "order.decided",
            {
                "order_id": result.get("po_number", ""),
                "decision": result.get("action", ""),
                "actor": "zalo_manager",
            },
        )

    return {"ok": True, "result": result}


