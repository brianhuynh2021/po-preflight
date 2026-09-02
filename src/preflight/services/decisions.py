from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from preflight.rules import DecisionValidationError, validate_order_decision
from preflight.security.rbac import Role
from preflight.store import BaseAuditStore


@dataclass(frozen=True)
class Principal:
    user_id: str
    display_name: str
    role: Role
    channel: Literal["web", "telegram", "zalo", "api", "agent"]


@dataclass(frozen=True)
class DecisionResult:
    decision_id: int
    po_number: str
    decision: str
    actor: str
    note: str
    created_at: str
    previous_status: str
    new_status: str
    display_name: str
    channel: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "po_number": self.po_number,
            "decision": self.decision,
            "actor": self.actor,
            "display_name": self.display_name,
            "channel": self.channel,
            "note": self.note,
            "created_at": self.created_at,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
        }


class DecisionError(Exception):
    """Business or governance error raised during order decision execution."""

    def __init__(self, message: str, status_code: int = 400, code: str = "DECISION_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def decide_order(
    store: BaseAuditStore,
    *,
    order_ref: str | int,
    decision: str,
    note: str | None = None,
    principal: Principal,
    event_bus: Any | None = None,
) -> DecisionResult:
    """Single entry point for executing and auditing all order governance decisions across channels.
    
    Guarantees:
    1. Order existence check (404 if missing)
    2. RBAC enforcement: principal.role >= MANAGER (403 if insufficient)
    3. SOX 404 / Financial governance rule validation (409/422)
    4. Immutable audit trail and cryptographic decision logging
    5. Real-time event broadcasting
    """
    clean_decision = decision.lower().strip()
    clean_note = (note or "").strip()

    # 1. Load Order
    ref_str = str(order_ref).strip()
    row = store.get_order(ref_str)
    if not row:
        row = store.get_order_by_po(ref_str)
    if not row:
        raise DecisionError(f"Order '{order_ref}' not found in preflight audit store.", status_code=404, code="ORDER_NOT_FOUND")

    # 2. RBAC Role Verification
    role_priority = {Role.VIEWER: 1, Role.AUDITOR: 2, Role.MANAGER: 3, Role.ADMIN: 4}
    user_prio = role_priority.get(principal.role, 0)
    required_prio = role_priority[Role.MANAGER]
    if user_prio < required_prio:
        role_name = getattr(principal.role, "name", str(principal.role))
        raise DecisionError(
            f"Insufficient permissions: Role MANAGER or higher required to decide orders (current: {role_name}).",
            status_code=403,
            code="FORBIDDEN",
        )


    # 3. Governance Constraints Validation
    findings_data = json.loads(row.get("findings_json", "[]")) if row.get("findings_json") else []
    error_count = sum(1 for f in findings_data if f.get("severity") == "error")

    current_status = row.get("status", "review_required")
    try:
        validate_order_decision(
            current_status=current_status,
            decision=clean_decision,
            note=clean_note,
            error_count=error_count,
        )
    except DecisionValidationError as exc:
        raise DecisionError(exc.message, status_code=exc.status_code, code="GOVERNANCE_VIOLATION") from exc

    # 4. Record Decision
    po_number = row["po_number"]
    actor_str = f"{principal.channel}:{principal.user_id}"
    created_at = datetime.now(UTC).isoformat()

    decision_id = store.record_decision(
        po_number=po_number,
        decision=clean_decision,
        actor=actor_str,
        note=clean_note,
        display_name=principal.display_name,
        channel=principal.channel,
    )

    new_status = "approved" if clean_decision == "approved" else ("rejected" if clean_decision == "rejected" else "needs_changes")

    # 5. Broadcast SSE Real-Time Event
    if event_bus is not None:
        try:
            event_bus.publish(
                "order.decided",
                {
                    "order_id": str(row["id"]),
                    "po_number": po_number,
                    "decision": clean_decision,
                    "actor": actor_str,
                    "display_name": principal.display_name,
                    "channel": principal.channel,
                    "note": clean_note,
                    "previous_status": current_status,
                    "new_status": new_status,
                    "created_at": created_at,
                },
            )
        except Exception:
            pass

    return DecisionResult(
        decision_id=decision_id,
        po_number=po_number,
        decision=clean_decision,
        actor=actor_str,
        note=clean_note,
        created_at=created_at,
        previous_status=current_status,
        new_status=new_status,
        display_name=principal.display_name,
        channel=principal.channel,
    )
