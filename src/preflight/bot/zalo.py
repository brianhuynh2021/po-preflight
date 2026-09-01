from __future__ import annotations

from typing import Any
from preflight.bot.schemas import BotNotificationResult


def format_zalo_notification(order: dict[str, Any]) -> dict[str, Any]:
    """Format Zalo ZNS / Official Account transaction message payload."""
    po_num = order.get("po_number", "N/A")
    cust = order.get("customer", "N/A")
    status = order.get("status", "review_required")
    risk = order.get("risk_level", "MEDIUM")
    total_val = order.get("total_value", 0)
    curr = order.get("currency", "VND")
    findings = order.get("findings", [])

    return {
        "template_id": "PO_PREFLIGHT_ALERT_TEMPLATE",
        "template_data": {
            "order_code": po_num,
            "customer_name": cust,
            "total_amount": f"{total_val:,.0f} {curr}",
            "status": status.upper(),
            "risk_level": risk,
            "violation_count": str(len(findings)),
            "action_url": f"http://localhost:3000?order={po_num}",
        },
    }


class ZaloBotService:
    """Zalo OA Notification Service."""

    def __init__(self, app_id: str | None = None, secret: str | None = None):
        self.app_id = app_id
        self.secret = secret

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.secret)

    def send_order_alert(self, order: dict[str, Any]) -> BotNotificationResult:
        order_id = order.get("id", order.get("po_number", "unknown"))
        payload = format_zalo_notification(order)

        # Mock / Dry-run dispatch
        return BotNotificationResult(
            success=True,
            channel="zalo",
            order_id=order_id,
            message_id="zalo_msg_mock_9988",
            dry_run=True,
            details=f"Zalo notification prepared for Order #{order_id} (Template: PO_PREFLIGHT_ALERT_TEMPLATE).",
        )
