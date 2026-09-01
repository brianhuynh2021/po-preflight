"use client";

import React, { useState } from "react";

interface NodeState {
  id: string;
  name: string;
  category: "INGEST" | "RAG" | "RULES" | "HITL" | "ERP";
  status: "COMPLETED" | "ACTIVE" | "PENDING" | "PAUSED";
  latencyMs: number;
  description: string;
  outputPayload?: Record<string, unknown>;
}

export function AgentGraphVisualizer() {
  const [selectedThread] = useState("thread-demo-8899");
  const [activeStep, setActiveStep] = useState<string>("human_approval");
  const [isResumed, setIsResumed] = useState(false);

  const nodes: NodeState[] = [
    {
      id: "document_ingestion",
      name: "Document Ingestion & OCR",
      category: "INGEST",
      status: "COMPLETED",
      latencyMs: 142,
      description: "Cascading OCR engine: extracts header, line items, and performs zero-hallucination math grounding.",
      outputPayload: {
        po_number: "PO-2026-8899",
        customer: "Vingroup Retail",
        declared_total: 108440000,
        math_check: "PASS (100% matched)",
      },
    },
    {
      id: "hybrid_sku_rag",
      name: "4-Tier Hybrid RAG Matcher",
      category: "RAG",
      status: "COMPLETED",
      latencyMs: 12,
      description: "Waterfall resolution: Tier 0 Alias -> Tier 1 Exact -> Tier 2 Fuzzy -> Tier 3 Vector.",
      outputPayload: {
        resolved_skus: 3,
        tier_breakdown: { tier_1: 1, tier_2: 1, tier_3: 1 },
      },
    },
    {
      id: "deterministic_rules",
      name: "Deterministic Policy Engine",
      category: "RULES",
      status: "COMPLETED",
      latencyMs: 4,
      description: "Evaluates pricing tolerance (2%), inventory availability, and duplicate order signatures.",
      outputPayload: {
        findings_count: 2,
        blocking_errors: 1,
        severity: "BLOCKED",
      },
    },
    {
      id: "human_approval",
      name: "HITL Checkpoint Interruption",
      category: "HITL",
      status: isResumed ? "COMPLETED" : "PAUSED",
      latencyMs: isResumed ? 1200 : 0,
      description: "StateGraph checkpoint saves execution state and pushes mobile approval request to Telegram / Webhook.",
      outputPayload: isResumed
        ? { decision: "APPROVED", actor: "Operations Director", note: "VIP customer override" }
        : { checkpoint: "paused_before_node", pending_approval: true },
    },
    {
      id: "erp_outbox_dispatch",
      name: "Transactional Outbox Sync",
      category: "ERP",
      status: isResumed ? "COMPLETED" : "PENDING",
      latencyMs: isResumed ? 48 : 0,
      description: "Atomic idempotency delivery into SAP S/4HANA / Odoo without duplicate order risk.",
      outputPayload: isResumed
        ? { erp_reference: "SAP-SO-20268899", idempotency_key: "373a8527101d02ec" }
        : { status: "awaiting_approval" },
    },
  ];

  const selectedNode = nodes.find((n) => n.id === activeStep) || nodes[0];

  const handleSimulateResume = () => {
    setIsResumed(true);
  };

  return (
    <div className="page agent-graph-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">LANGGRAPH MULTI-AGENT WORKFLOW (ISSUE #39)</p>
          <h1>LangGraph Stateful Workflow Visualizer</h1>
          <p>
            Real-time inspection of cyclical agent StateGraph execution, checkpoint persistence, and Human-in-the-Loop interruptions.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          {!isResumed && (
            <button className="primary-button" onClick={handleSimulateResume}>
              ▶ Resume StateGraph Execution
            </button>
          )}
          {isResumed && (
            <button className="secondary-button" onClick={() => setIsResumed(false)}>
              ↺ Reset Checkpoint
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "20px" }}>
        {/* Left: DAG Pipeline Canvas */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div>
              <h3>Active Execution DAG: {selectedThread}</h3>
              <small style={{ color: "var(--muted)" }}>Checkpointer: MemorySaver (Thread State Anchored)</small>
            </div>
            <span
              className={`badge-clean ${
                isResumed ? "badge-clean-success" : "badge-clean-warning"
              }`}
            >
              {isResumed ? "● COMPLETED" : "⏸ INTERRUPTED (HITL)"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px", padding: "10px 0" }}>
            {nodes.map((node, index) => {
              const isSelected = activeStep === node.id;
              const isCurrentPause = node.id === "human_approval" && !isResumed;

              return (
                <div
                  key={node.id}
                  className={`dag-node ${isSelected ? "active-step" : ""}`}
                  style={{
                    cursor: "pointer",
                    borderLeft: isCurrentPause ? "4px solid var(--amber)" : undefined,
                  }}
                  onClick={() => setActiveStep(node.id)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "24px",
                          height: "24px",
                          borderRadius: "50%",
                          background: node.status === "COMPLETED" ? "var(--green-soft)" : isCurrentPause ? "var(--amber-soft)" : "var(--canvas)",
                          color: node.status === "COMPLETED" ? "var(--green)" : isCurrentPause ? "var(--amber)" : "var(--muted)",
                          fontSize: "11px",
                          fontWeight: 700,
                        }}
                      >
                        {index + 1}
                      </span>
                      <strong style={{ fontSize: "14px", color: "var(--ink)" }}>{node.name}</strong>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className="code-snippet">{node.latencyMs}ms</span>
                      <span
                        className={`badge-clean ${
                          node.status === "COMPLETED"
                            ? "badge-clean-success"
                            : node.status === "PAUSED"
                            ? "badge-clean-warning"
                            : "badge-clean-info"
                        }`}
                      >
                        {node.status}
                      </span>
                    </div>
                  </div>
                  <p style={{ margin: "8px 0 0", fontSize: "12.5px", color: "var(--muted)" }}>
                    {node.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: State Inspector & Telemetry */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>State Inspector: {selectedNode.name}</h3>
            <span className="code-snippet">{selectedNode.category}</span>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "11px", color: "var(--muted)", fontWeight: 600, marginBottom: "4px" }}>
              STEP SUMMARY
            </label>
            <p style={{ fontSize: "13px", color: "var(--ink)", margin: 0, lineHeight: 1.5 }}>
              {selectedNode.description}
            </p>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "11px", color: "var(--muted)", fontWeight: 600, marginBottom: "6px" }}>
              STATE PAYLOAD (JSON)
            </label>
            <pre
              style={{
                background: "var(--canvas)",
                padding: "12px",
                borderRadius: "8px",
                border: "1px solid var(--line)",
                fontSize: "12px",
                fontFamily: "ui-monospace, monospace",
                overflowX: "auto",
                margin: 0,
                color: "var(--ink)",
              }}
            >
              {JSON.stringify(selectedNode.outputPayload, null, 2)}
            </pre>
          </div>

          <div style={{ borderTop: "1px solid var(--line)", paddingTop: "14px", marginTop: "14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--muted)" }}>
              <span>Execution Engine:</span>
              <strong style={{ color: "var(--ink)" }}>LangGraph Core v0.2</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "var(--muted)", marginTop: "6px" }}>
              <span>State Reducer:</span>
              <strong style={{ color: "var(--ink)" }}>Immutable Append</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
