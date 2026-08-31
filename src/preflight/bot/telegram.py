from __future__ import annotations

import os
from typing import Any
import urllib.request
import json
import logging

from preflight.bot.schemas import BotNotificationResult
from preflight.store import AuditStore

logger = logging.getLogger("PreflightBot")


def format_telegram_po_card(order: dict[str, Any]) -> str:
    """Format rich HTML card for Telegram purchase order alerts."""
    po_num = order.get("po_number", "N/A")
    cust = order.get("customer", "N/A")
    status = order.get("status", "review_required")
    risk = order.get("risk_level", "MEDIUM")
    total_val = order.get("total_value", 0)
    curr = order.get("currency", "VND")
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
        f"💰 <b>Tổng giá trị:</b> <code>{total_val:,.0f} {curr}</code>\n"
        f"📊 <b>Trạng thái:</b> {status_badge}\n"
        f"🛡️ <b>Mức độ rủi ro:</b> {risk_emoji} <b>{risk}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    # Line items summary
    text += f"📦 <b>Sản phẩm ({len(lines)} dòng):</b>\n"
    for idx, item in enumerate(lines[:3], 1):
        sku = item.get("sku", "N/A")
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        text += f"  {idx}. <code>{sku}</code> × {qty} (đơn giá: {price:,.0f})\n"
    if len(lines) > 3:
        text += f"  <i>...và {len(lines) - 3} sản phẩm khác</i>\n"

    # Findings / Violations
    text += f"\n🔍 <b>Chi tiết vi phạm ({len(findings)} cảnh báo):</b>\n"
    if findings:
        for f in findings:
            sev = f.get("severity", "warning")
            code = f.get("code", "")
            msg = f.get("message", "")
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
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.store = store

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_order_alert(self, order: dict[str, Any], web_base_url: str = "http://localhost:3000") -> BotNotificationResult:
        """Send PO Preflight alert card with inline action buttons to Telegram."""
        order_id = order.get("id", order.get("po_number", "unknown"))
        text = format_telegram_po_card(order)
        keyboard = build_approval_inline_keyboard(order_id, web_base_url=web_base_url)

        if not self.is_configured:
            logger.info(f"[TelegramBot (DRY RUN)] Dispatched PO alert for Order #{order_id}")
            return BotNotificationResult(
                success=True,
                channel="telegram",
                order_id=order_id,
                message_id="mock_msg_12345",
                dry_run=True,
                details=f"Dry-run alert for Order #{order_id} generated successfully (No Telegram token configured).",
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
                details=f"Telegram API Error: {str(exc)}",
            )

    def handle_callback_action(
        self,
        callback_data: str,
        from_username: str | None = None,
        callback_query_id: str | None = None,
    ) -> dict[str, Any]:
        """Process inline button click callback query."""
        parts = callback_data.split(":", 1)
        if len(parts) != 2:
            return {"success": False, "message": "Invalid callback data format"}

        action, order_id_str = parts[0], parts[1]
        try:
            order_id = int(order_id_str)
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
        decided_by = f"Telegram:@{from_username}" if from_username else "Telegram:Manager"

        # Record decision in store if available
        if self.store is not None:
            po_num = str(order_id)
            if isinstance(order_id, int) or (isinstance(order_id, str) and order_id.isdigit()):
                order = self.store.get_order(int(order_id))
                if order:
                    po_num = order["po_number"]
            try:
                self.store.record_decision(
                    po_number=po_num,
                    decision=store_decision,
                    actor=decided_by,
                    note=f"Processed via Telegram Inline Button Action [{action}]",
                )
            except Exception as exc:
                logger.warning(f"Could not record decision in store: {exc}")

        return {
            "success": True,
            "order_id": order_id,
            "decision": display_decision,
            "decided_by": decided_by,
            "popup_message": user_msg,
        }
