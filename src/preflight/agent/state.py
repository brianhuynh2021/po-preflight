from __future__ import annotations

from typing import Any, TypedDict


class PreflightAgentState(TypedDict, total=False):
    # Workflow metadata & thread
    thread_id: str
    po_number: str
    customer: str
    raw_content: str | None
    source_file: str | None

    # Normalized Domain Objects
    order: dict[str, Any]
    line_items: list[dict[str, Any]]
    matched_skus: dict[str, Any]

    # Preflight Findings & Analysis
    findings: list[dict[str, Any]]
    status: str  # "ready_for_approval" | "review_required" | "blocked" | "approved" | "rejected"
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH"

    # Human-In-The-Loop (HITL) Decision
    decision_required: bool
    decision: str | None  # "APPROVED" | "REJECTED" | "CHANGES_REQUESTED"
    decided_by: str | None
    decision_notes: str | None

    # Bot Notification Tracking
    telegram_notified: bool
    zalo_notified: bool

    # Downstream ERP Synchronization
    erp_synced: bool
    erp_tx_id: str | None
    idempotency_key: str | None

    # Execution Trace & Audit Log
    audit_trail: list[str]
    error: str | None
