from __future__ import annotations

import html
import json
import logging
import os
import urllib.request
from decimal import Decimal
from typing import Any

from preflight.bot.schemas import BotNotificationResult
from preflight.store import AuditStore

logger = logging.getLogger("PreflightBot")


def format_currency(value: float | int | Decimal, currency: str = "VND") -> str:
    """Format monetary values according to currency standards."""
    curr_upper = (currency or "VND").upper()
    num = float(value)
    if curr_upper == "USD":
        return f"${num:,.2f}"
    if curr_upper == "EUR":
        return f"€{num:,.2f}"
    if curr_upper == "GBP":
        return f"£{num:,.2f}"
    return f"{num:,.0f} {curr_upper}"


def format_telegram_po_card(order: dict[str, Any]) -> str:
    """Format rich HTML card for Telegram purchase order alerts."""
    po_num = html.escape(str(order.get("po_number", "N/A")))
    cust = html.escape(str(order.get("customer", "N/A")))
    status = str(order.get("status", "review_required"))
    risk = str(order.get("risk_level", "MEDIUM"))
    total_val = order.get("total_value", 0)
    curr = str(order.get("currency", "VND"))
    findings = order.get("findings", [])
    lines = order.get("line_items", [])

    # Status & Risk emojis
    risk_emoji = "🔴" if risk == "HIGH" else "🟡" if risk == "MEDIUM" else "🟢"
    status_badge = (
        "🚨 <b>BLOCKED (BỊ CHẶN)</b>" if status == "blocked"
        else "⚠️ <b>REVIEW REQUIRED (CẦN DUYỆT)</b>" if status == "review_required"
        else "✅ <b>READY FOR APPROVAL</b>" if status == "ready_for_approval"
        else f"ℹ️ <b>{status.upper()}</b>"
    )

    # Header
    text = (
        f"📋 <b>PO PREFLIGHT ALERT — ĐƠN HÀNG MỚI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Mã Đơn:</b> <code>{po_num}</code>\n"
        f"🏢 <b>Khách hàng:</b> <b>{cust}</b>\n"
        f"💰 <b>Tổng giá trị:</b> <code>{format_currency(total_val, curr)}</code>\n"
        f"📊 <b>Trạng thái:</b> {status_badge}\n"
        f"🛡️ <b>Mức độ rủi ro:</b> {risk_emoji} <b>{risk}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    # Line items summary
    text += f"📦 <b>Sản phẩm ({len(lines)} dòng):</b>\n"
    for idx, item in enumerate(lines[:3], 1):
        sku = html.escape(str(item.get("sku", "N/A")))
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        text += f"  {idx}. <code>{sku}</code> × {qty} (đơn giá: {format_currency(price, curr)})\n"
    if len(lines) > 3:
        text += f"  <i>...và {len(lines) - 3} sản phẩm khác</i>\n"

    # Findings / Violations
    text += f"\n🔍 <b>Chi tiết vi phạm ({len(findings)} cảnh báo):</b>\n"
    if findings:
        for f in findings:
            sev = f.get("severity", "warning")
            code = html.escape(str(f.get("code", "")))
            msg = html.escape(str(f.get("message", "")))
            sev_icon = "❌" if sev == "error" else "⚠️"
            text += f"  {sev_icon} [<b>{code}</b>]: {msg}\n"
    else:
        text += "  ✅ Không có vi phạm nào. Đơn hàng hợp lệ 100%.\n"

    text += "\n👇 <i>Vui lòng bấm nút bên dưới để ra quyết định:</i>"
    return text


def build_approval_inline_keyboard(order_id: int | str, web_base_url: str = "http://localhost:3000") -> dict[str, Any]:
    """Build interactive inline keyboard for Telegram approval."""
    return {
        "inline_keyboard": [
            [
                {"text": "🟢 Duyệt Đơn (Approve)", "callback_data": f"approve:{order_id}"},
                {"text": "🔴 Từ Chối (Reject)", "callback_data": f"reject:{order_id}"},
            ],
            [
                {"text": "📝 Yêu Cầu Sửa (Request Changes)", "callback_data": f"request_changes:{order_id}"},
                {"text": "🌐 Mở Web Portal", "url": f"{web_base_url}"},
            ],
        ]
    }


class TelegramBotService:
    """Telegram Bot Service for dispatching alerts and handling approval webhooks."""

    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        store: AuditStore | None = None,
        dry_run: bool | None = None,
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.store = store
        self.dry_run = dry_run if dry_run is not None else (os.getenv("TELEGRAM_DRY_RUN", "false").lower() in ("true", "1", "yes"))

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_order_alert(self, order: dict[str, Any], web_base_url: str = "http://localhost:3000") -> BotNotificationResult:
        """Send PO Preflight alert card with inline action buttons to Telegram."""
        order_id = order.get("id", order.get("po_number", "unknown"))
        text = format_telegram_po_card(order)
        keyboard = build_approval_inline_keyboard(order_id, web_base_url=web_base_url)

        if not self.is_configured:
            if self.dry_run:
                logger.info(f"[TelegramBot (DRY RUN)] Dispatched PO alert for Order #{order_id}")
                return BotNotificationResult(
                    success=True,
                    channel="telegram",
                    order_id=order_id,
                    message_id=None,
                    dry_run=True,
                    mode="dry_run",
                    details=f"Dry-run alert for Order #{order_id} generated successfully.",
                )
            else:
                env_name = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
                if env_name in ("production", "prod") and self.store:
                    self.store.record_audit_block(
                        po_number=str(order.get("po_number", order_id)),
                        action="NOTIFY_SKIPPED",
                        actor="system",
                        data={"reason": "Telegram not configured in production", "channel": "telegram"},
                    )
                return BotNotificationResult(
                    success=False,
                    channel="telegram",
                    order_id=order_id,
                    message_id=None,
                    dry_run=False,
                    mode="unconfigured",
                    details="Telegram chưa cấu hình (Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID).",
                )

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                msg_id = str(res_data.get("result", {}).get("message_id", ""))
                return BotNotificationResult(
                    success=True,
                    channel="telegram",
                    order_id=order_id,
                    message_id=msg_id,
                    dry_run=False,
                    mode="live",
                    details=f"Alert dispatched to Telegram chat {self.chat_id}.",
                )
        except Exception as exc:
            logger.error(f"Failed to send Telegram alert: {exc}")
            return BotNotificationResult(
                success=False,
                channel="telegram",
                order_id=order_id,
                message_id=None,
                dry_run=False,
                mode="live",
                details=f"Telegram API Error: {str(exc)}",
            )

    def set_webhook(
        self,
        webhook_url: str,
        secret_token: str | None = None,
        drop_pending_updates: bool = False,
    ) -> dict[str, Any]:
        """Configure webhook URL with optional anti-spoofing secret token on Telegram Bot API."""
        secret = secret_token or os.getenv("TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_SECRET_TOKEN")
        if not self.is_configured:
            logger.info(f"[TelegramBot (DRY RUN)] setWebhook called for {webhook_url} with secret_token={bool(secret)}")
            return {
                "ok": True,
                "result": True,
                "description": f"Webhook set to {webhook_url} (dry run)",
            }

        url = f"https://api.telegram.org/bot{self.token}/setWebhook"
        payload: dict[str, Any] = {
            "url": webhook_url,
            "drop_pending_updates": drop_pending_updates,
        }
        if secret:
            payload["secret_token"] = secret

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            logger.error(f"Failed to set Telegram webhook: {exc}")
    def answer_callback_query(
        self, callback_query_id: str, text: str = "", show_alert: bool = False
    ) -> None:
        """Acknowledge Telegram callback query with optional notification/alert popup."""
        if not self.is_configured or not callback_query_id:
            return
        url = f"https://api.telegram.org/bot{self.token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception as exc:
            logger.warning(f"Could not answer callback query: {exc}")

    def disable_reply_markup(self, chat_id: int | str, message_id: int) -> None:
        """Remove inline action buttons after decision is processed."""
        if not self.is_configured or not chat_id or not message_id:
            return
        url = f"https://api.telegram.org/bot{self.token}/editMessageReplyMarkup"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception as exc:
            logger.warning(f"Could not disable reply markup: {exc}")

    def handle_callback_action(
        self,
        callback_data: str,
        from_user_id: str | int | None = None,
        from_username: str | None = None,
        callback_query_id: str | None = None,
        chat_id: int | str | None = None,
        message_id: int | None = None,
    ) -> dict[str, Any]:
        """Process inline button click callback query with authenticated identity and single decision gate."""
        from preflight.security.rbac import Role
        from preflight.services.decisions import DecisionError, Principal, decide_order

        parts = callback_data.split(":", 1)
        if len(parts) != 2:
            return {"success": False, "message": "Invalid callback data format"}

        action, order_id_str = parts[0], parts[1]
        try:
            order_id: int | str = int(order_id_str)
        except ValueError:
            order_id = order_id_str

        # Map action to decision status
        decision_map = {
            "approve": ("approved", "APPROVED", "✅ Đã duyệt đơn thành công!"),
            "reject": ("rejected", "REJECTED", "❌ Đã từ chối đơn hàng!"),
            "request_changes": ("needs_changes", "CHANGES_REQUESTED", "📝 Đã gửi yêu cầu sửa đổi đơn!"),
        }

        if action not in decision_map:
            return {"success": False, "message": f"Unknown action '{action}'"}

        store_decision, display_decision, user_msg = decision_map[action]

        if not self.store:
            return {"success": False, "message": "Store is not configured"}

        # 1. Lookup channel identity for telegram user id
        identity = self.store.get_channel_identity("telegram", str(from_user_id)) if from_user_id else None
        if not identity:
            msg = "Tài khoản Telegram chưa được liên kết. Liên hệ quản trị."
            if callback_query_id:
                self.answer_callback_query(callback_query_id, text=msg, show_alert=True)
            return {
                "success": False,
                "popup_message": msg,
                "show_alert": True,
                "error": "UNLINKED_ACCOUNT",
            }

        role_raw = identity.get("role", "VIEWER")
        if isinstance(role_raw, str):
            role_enum = getattr(Role, role_raw.strip().upper(), Role.VIEWER)
        elif isinstance(role_raw, int):
            try:
                role_enum = Role(role_raw)
            except ValueError:
                role_enum = Role.VIEWER
        else:
            role_enum = Role.VIEWER


        principal = Principal(
            user_id=identity["user_id"],
            display_name=identity["display_name"],
            role=role_enum,
            channel="telegram",
        )

        try:
            result = decide_order(
                store=self.store,
                order_ref=order_id,
                decision=store_decision,
                note=f"Processed via Telegram Inline Button Action [{action}]",
                principal=principal,
            )
            if callback_query_id:
                self.answer_callback_query(callback_query_id, text=user_msg, show_alert=False)
            if chat_id and message_id:
                self.disable_reply_markup(chat_id, message_id)

            return {
                "success": True,
                "order_id": order_id,
                "decision": display_decision,
                "decided_by": f"telegram:{identity['user_id']}",
                "popup_message": user_msg,
                "decision_result": result.to_dict(),
            }
        except DecisionError as err:
            if err.status_code == 409:
                popup_msg = "Đơn đang bị chặn, không thể duyệt." if "blocked" in err.message.lower() else f"Không thể duyệt: {err.message}"
            elif err.status_code == 422:
                popup_msg = "Cần ghi chú ≥10 ký tự — hãy duyệt trên web."
            else:
                popup_msg = f"Lỗi ({err.status_code}): {err.message}"

            if callback_query_id:
                self.answer_callback_query(callback_query_id, text=popup_msg, show_alert=True)

            return {
                "success": False,
                "popup_message": popup_msg,
                "show_alert": True,
                "error": err.code,
                "status_code": err.status_code,
            }

