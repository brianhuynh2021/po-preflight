from __future__ import annotations

from typing import Any
from preflight.agent.graph import build_preflight_graph
from preflight.agent.state import PreflightAgentState
from preflight.models import Product
from preflight.store import AuditStore


def execute_order_workflow(
    initial_state: dict[str, Any],
    catalog: dict[str, Product],
    store: AuditStore,
    thread_id: str | None = None,
) -> tuple[dict[str, Any], Any]:
    """Execute order through LangGraph Preflight StateGraph."""
    thread = thread_id or str(initial_state.get("po_number", "thread_default"))
    config = {"configurable": {"thread_id": thread}}

    graph = build_preflight_graph(catalog, store)
    final_state = graph.invoke(initial_state, config=config)
    return final_state, graph


def resume_order_workflow(
    decision: str,
    decided_by: str,
    catalog: dict[str, Product],
    store: AuditStore,
    thread_id: str,
    graph: Any,
    notes: str | None = None,
) -> dict[str, Any]:
    """Resume an interrupted LangGraph state with human approval payload."""
    config = {"configurable": {"thread_id": thread_id}}

    # Update state with human decision
    graph.update_state(
        config,
        {
            "decision": decision,
            "decided_by": decided_by,
            "decision_notes": notes,
        },
    )

    # Continue execution from interrupt point
    resumed_state = graph.invoke(None, config=config)
    return resumed_state


__all__ = [
    "PreflightAgentState",
    "build_preflight_graph",
    "execute_order_workflow",
    "resume_order_workflow",
]
