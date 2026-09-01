from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from preflight.agent.graph import build_preflight_graph
from preflight.api.deps import get_audit_store, get_catalog
from preflight.models import Product
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import AuditStore

from langgraph.checkpoint.memory import MemorySaver

router = APIRouter(prefix="/api/v1/agent", tags=["LangGraph Agentic Orchestrator"])

# Shared in-memory checkpointer for thread persistence across requests
_SERVER_CHECKPOINTER = MemorySaver()


def _get_server_graph(catalog: dict[str, Product], store: AuditStore):
    return build_preflight_graph(catalog, store, checkpointer=_SERVER_CHECKPOINTER)



class AgentRunRequest(BaseModel):
    po_number: str = Field(..., description="Purchase Order number", example="PO-2026-88")
    customer: str = Field(..., description="Customer enterprise name", example="Northstar Retail")
    line_items: list[dict[str, Any]] = Field(
        ...,
        description="Line items with sku, quantity, and unit_price",
        example=[
            {"sku": "LAPTOP-A14", "quantity": 2, "unit_price": 18500000},
            {"sku": "dây mạng 3m bấm sẵn", "quantity": 10, "unit_price": 72000},
        ],
    )
    thread_id: str | None = Field(None, description="Optional custom thread ID")


class AgentResumeRequest(BaseModel):
    decision: str = Field(..., description="Approval decision: APPROVED or REJECTED", example="APPROVED")
    decided_by: str = Field(..., description="Actor username or ID", example="brianhuynh")
    notes: str | None = Field(None, description="Optional reviewer notes", example="Approved with price override")


@router.post(
    "/run",
    summary="Run Order through LangGraph Stateful Workflow",
    description=(
        "Executes an order through Ingestion -> 4-Tier SKU RAG -> Deterministic Rules. "
        "If clean, automatically syncs to ERP. If violations detected, dispatches Telegram alert "
        "and interrupts state at human_approval node waiting for manager sign-off."
    ),
)
def run_agent_workflow(
    payload: AgentRunRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    thread_id = payload.thread_id or payload.po_number
    config = {"configurable": {"thread_id": thread_id}}

    graph = _get_server_graph(catalog, store)
    initial_state = {
        "thread_id": thread_id,
        "po_number": payload.po_number,
        "customer": payload.customer,
        "line_items": payload.line_items,
        "audit_trail": [],
    }

    state = graph.invoke(initial_state, config=config)
    next_nodes = list(graph.get_state(config).next)

    return {
        "thread_id": thread_id,
        "status": state.get("status"),
        "risk_level": state.get("risk_level"),
        "findings_count": len(state.get("findings", [])),
        "findings": state.get("findings", []),
        "matched_skus": state.get("matched_skus", {}),
        "is_interrupted": len(next_nodes) > 0,
        "waiting_for_nodes": next_nodes,
        "erp_synced": state.get("erp_synced", False),
        "erp_tx_id": state.get("erp_tx_id"),
        "audit_trail": state.get("audit_trail", []),
    }


@router.post(
    "/resume/{thread_id}",
    summary="Resume Interrupted Workflow with Human Decision",
    description="Resume a paused LangGraph thread with manager approval or rejection, completing ERP sync.",
)
def resume_agent_workflow(
    thread_id: str,
    payload: AgentResumeRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:

    config = {"configurable": {"thread_id": thread_id}}
    graph = _get_server_graph(catalog, store)

    current_state = graph.get_state(config)
    if not current_state or not current_state.values:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found.")

    # Update state with decision
    graph.update_state(
        config,
        {
            "decision": payload.decision.upper(),
            "decided_by": payload.decided_by,
            "decision_notes": payload.notes,
        },
    )

    # Resume graph execution
    resumed_state = graph.invoke(None, config=config)
    next_nodes = list(graph.get_state(config).next)

    return {
        "thread_id": thread_id,
        "status": resumed_state.get("status"),
        "decision": resumed_state.get("decision"),
        "is_interrupted": len(next_nodes) > 0,
        "erp_synced": resumed_state.get("erp_synced", False),
        "erp_tx_id": resumed_state.get("erp_tx_id"),
        "audit_trail": resumed_state.get("audit_trail", []),
    }


@router.get(
    "/state/{thread_id}",
    summary="Inspect Workflow Thread State & Checkpoint",
    description="Inspect current snapshot values and next execution steps of a LangGraph workflow thread.",
)
def get_workflow_state(
    thread_id: str,
    catalog: dict[str, Product] = Depends(get_catalog),
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id}}
    graph = _get_server_graph(catalog, store)

    snapshot = graph.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail=f"No workflow thread found for '{thread_id}'.")

    return {
        "thread_id": thread_id,
        "values": snapshot.values,
        "next_nodes": list(snapshot.next),
        "checkpoint_id": getattr(snapshot.config.get("configurable", {}), "checkpoint_id", None),
    }
