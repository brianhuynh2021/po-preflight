from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error
from typing import Any

from preflight.bot.schemas import BotNotificationResult
from preflight.store import BaseAuditStore


def format_zalo_notification(order: dict[str, Any], web_base_url: str = "http://localhost:3000") -> dict[str, Any]:
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
            "action_url": f"{web_base_url}/orders?search={po_num}",
        },
        "recipient": {"user_id": "MANAGER_ZALO_UID"},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "media",
                    "elements": [
                        {
                            "media_type": "image",
                            "url": "https://raw.githubusercontent.com/brianhuynh2021/po-preflight/dev/docs/logo.png",
                        }
                    ],
                    "title": f"📋 PO Preflight Alert — {po_num}",
                    "subtitle": f"Khách: {cust} | {total_val:,.0f} {curr} | Trạng thái: {status.upper()}",
                    "buttons": [
                        {
                            "title": "✅ Duyệt Đơn",
                            "type": "oa.query.show",
                            "payload": f"APPROVE:{po_num}",
                        },
                        {
                            "title": "❌ Từ Chối",
                            "type": "oa.query.show",
                            "payload": f"REJECT:{po_num}",
                        },
                        {
                            "title": "🔍 Mở Portal",
                            "type": "oa.open.url",
                            "url": f"{web_base_url}/orders?search={po_num}",
                        },
                    ],
                },
            }
        },
    }



class ZaloBotService:
    """Official Zalo OA OpenAPI v3 & Webhook Handler."""

    def __init__(
        self,
        app_id: str | None = None,
        secret_key: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        store: BaseAuditStore | None = None,
        dry_run: bool = False,
    ):
        self.app_id = app_id or os.getenv("ZALO_APP_ID", "")
        self.secret_key = secret_key or os.getenv("ZALO_SECRET_KEY", "")
        self.access_token = access_token or os.getenv("ZALO_ACCESS_TOKEN", "")
        self.refresh_token = refresh_token or os.getenv("ZALO_REFRESH_TOKEN", "")
        self.store = store
        self.dry_run = dry_run or os.getenv("ZALO_DRY_RUN", "true").lower() == "true"

    @property
    def is_configured(self) -> bool:
        return bool(self.app_id and self.secret_key)

    def refresh_access_token(self) -> str | None:
        """Exchange refresh_token for a fresh access_token via Zalo OAuth2."""
        if not self.app_id or not self.secret_key or not self.refresh_token:
            return None

        url = "https://oauth.zaloapp.com/v4/oa/access_token"
        data = {
            "app_id": self.app_id,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        encoded_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={
                "Content-Type": "application/json",
                "secret_key": self.secret_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                new_token = res_json.get("access_token")
                if new_token:
                    self.access_token = new_token
                return new_token
        except Exception:
            return None

    def send_order_alert(self, order: dict[str, Any], web_base_url: str = "http://localhost:3000") -> BotNotificationResult:
        """Dispatch Zalo OA interactive notification card."""
        order_id = order.get("id", order.get("po_number", "unknown"))
        payload = format_zalo_notification(order, web_base_url=web_base_url)

        if self.dry_run or not self.access_token:
            return BotNotificationResult(
                success=True,
                channel="zalo",
                order_id=order_id,
                message_id="zalo_msg_simulated_9988",
                dry_run=True,
                details=f"Zalo interactive alert dispatched for Order #{order_id} (Dry Run).",
            )

        try:
            req_data = json.dumps(payload).encode("utf-8")
            url = "https://openapi.zalo.me/v3.0/oa/message/cs"
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "access_token": self.access_token,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                msg_id = res_json.get("data", {}).get("message_id") or "zalo_live_msg"
                return BotNotificationResult(
                    success=True,
                    channel="zalo",
                    order_id=order_id,
                    message_id=msg_id,
                    dry_run=False,
                    details="Zalo OA message delivered successfully.",
                )
        except Exception as exc:
            return BotNotificationResult(
                success=False,
                channel="zalo",
                order_id=order_id,
                message_id=None,
                dry_run=False,
                details=f"Zalo delivery failed: {exc}",
            )

    def verify_webhook_signature(self, raw_body: bytes, timestamp: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature from Zalo Webhook callback. Fails closed if secret_key is missing."""
        if not self.secret_key or not signature or not timestamp:
            return False
        
        # Zalo signature format: sha256(app_id + raw_body + timestamp + secret_key)
        body_text = raw_body.decode('utf-8', errors='ignore') if isinstance(raw_body, bytes) else str(raw_body)
        data_to_sign = f"{self.app_id}{body_text}{timestamp}{self.secret_key}".encode("utf-8")
        expected_sig = hashlib.sha256(data_to_sign).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def process_webhook_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Parse incoming user click event and update preflight order state through single DecisionService."""
        from preflight.security.rbac import Role
        from preflight.services.decisions import DecisionError, Principal, decide_order

        event_name = event_data.get("event_name", "")
        payload_str = event_data.get("message", {}).get("text", "") or event_data.get("user_id_by_app", "")
        sender_id = str(
            event_data.get("sender", {}).get("id")
            or event_data.get("user_id_by_app", "")
            or event_data.get("recipient", {}).get("id", "")
        )

        if ":" in payload_str and self.store:
            action, po_number = payload_str.split(":", 1)
            action_lower = action.lower()

            if action_lower not in ["approve", "approved", "reject", "rejected", "needs_changes", "request_changes"]:
                return {"status": "ignored", "event_name": event_name}

            decision = "approved" if action_lower in ["approve", "approved"] else ("rejected" if action_lower in ["reject", "rejected"] else "needs_changes")

            identity = self.store.get_channel_identity("zalo", sender_id) if sender_id else None
            if not identity:
                return {
                    "status": "error",
                    "error": "UNLINKED_ACCOUNT",
                    "message": "Zalo account is not linked to any system user. Contact admin.",
                    "status_code": 403,
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
                channel="zalo",
            )

            try:
                result = decide_order(
                    store=self.store,
                    order_ref=po_number,
                    decision=decision,
                    note="Processed via Zalo OA 1-touch interactive card",
                    principal=principal,
                )
                return {
                    "status": "success",
                    "action": decision,
                    "po_number": po_number,
                    "result": result.to_dict(),
                }
            except DecisionError as err:
                return {
                    "status": "error",
                    "error": err.code,
                    "message": err.message,
                    "status_code": err.status_code,
                }

        return {"status": "ignored", "event_name": event_name}

