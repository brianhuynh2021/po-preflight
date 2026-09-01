from __future__ import annotations

import functools
from typing import Any, Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from preflight.agent.nodes import (
    audit_rules_node,
    erp_sync_node,
    hitl_dispatch_node,
    human_approval_node,
    ingestion_node,
    sku_resolution_node,
)
from preflight.agent.state import PreflightAgentState
from preflight.models import Product
from preflight.store import AuditStore


def route_after_audit(state: PreflightAgentState) -> Literal["erp_sync", "hitl_dispatch"]:
    """Conditional Edge: Route clean orders directly to ERP, or risky orders to HITL Bot."""
    risk = state.get("risk_level", "LOW")
    if risk == "LOW":
        return "erp_sync"
    return "hitl_dispatch"


def route_after_human_approval(state: PreflightAgentState) -> Literal["erp_sync", "__end__"]:
    """Conditional Edge: Route approved orders to ERP, or rejected orders to END."""
    status = state.get("status", "approved")
    if status == "approved":
        return "erp_sync"
    return "__end__"


def build_preflight_graph(
    catalog: dict[str, Product],
    store: AuditStore,
    checkpointer: Any | None = None,
    with_interrupt: bool = True,
):
    """Build and compile the LangGraph Preflight Orchestration StateGraph."""
    if checkpointer is None:
        checkpointer = MemorySaver()

    # Wrap node functions with catalog and store dependencies
    bound_ingestion = functools.partial(ingestion_node, catalog=catalog, store=store)
    bound_sku = functools.partial(sku_resolution_node, catalog=catalog, store=store)
    bound_audit = functools.partial(audit_rules_node, catalog=catalog, store=store)
    bound_hitl = functools.partial(hitl_dispatch_node, catalog=catalog, store=store)
    bound_approval = functools.partial(human_approval_node, catalog=catalog, store=store)
    bound_erp = functools.partial(erp_sync_node, catalog=catalog, store=store)

    # Initialize StateGraph
    builder = StateGraph(PreflightAgentState)

    # Add Nodes
    builder.add_node("ingestion", bound_ingestion)
    builder.add_node("sku_resolution", bound_sku)
    builder.add_node("audit_rules", bound_audit)
    builder.add_node("hitl_dispatch", bound_hitl)
    builder.add_node("human_approval", bound_approval)
    builder.add_node("erp_sync", bound_erp)

    # Add Edges
    builder.add_edge(START, "ingestion")
    builder.add_edge("ingestion", "sku_resolution")
    builder.add_edge("sku_resolution", "audit_rules")

    # Conditional branching after Audit
    builder.add_conditional_edges(
        "audit_rules",
        route_after_audit,
        {
            "erp_sync": "erp_sync",
            "hitl_dispatch": "hitl_dispatch",
        },
    )

    builder.add_edge("hitl_dispatch", "human_approval")

    # Conditional branching after Human Approval
    builder.add_conditional_edges(
        "human_approval",
        route_after_human_approval,
        {
            "erp_sync": "erp_sync",
            "__end__": END,
        },
    )

    builder.add_edge("erp_sync", END)

    # Compile graph with checkpointing and optional interrupt
    interrupt_nodes = ["human_approval"] if with_interrupt else []
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_nodes,
    )
