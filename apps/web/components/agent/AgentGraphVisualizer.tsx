"use client";

import React, { useState } from "react";

interface NodeState {
  id: string;
  name: string;
  description: string;
  status: "idle" | "running" | "completed" | "interrupted" | "skipped";
  latency?: string;
}

export function AgentGraphVisualizer() {
  const [activeThread, setActiveThread] = useState<string>("thread-live-01");
  const [selectedNode, setSelectedNode] = useState<string>("human_approval");

  const [nodes, setNodes] = useState<NodeState[]>([
    { id: "ingest", name: "1. Document Ingestion", description: "Parse PO file (PDF/JSON/CSV) & run Self-Reflection Math", status: "completed", latency: "1.2ms" },
    { id: "sku_matching", name: "2. 4-Tier Hybrid RAG", description: "Cascade: Exact -> Fuzzy -> Vector -> LLM Context", status: "completed", latency: "3.4ms" },
    { id: "rules_eval", name: "3. Deterministic Rules", description: "Evaluate stock availability, price tolerance (2%), MOQ", status: "completed", latency: "0.4ms" },
    { id: "human_approval", name: "4. Human In The Loop", description: "HITL Checkpoint: Interrupt & Dispatch Telegram/Zalo card", status: "interrupted", latency: "Awaiting decision" },
    { id: "erp_sync", name: "5. Transactional Outbox", description: "Idempotent delivery to SAP S/4HANA & Odoo adapters", status: "idle" },
    { id: "audit_seal", name: "6. Merkle Audit Seal", description: "SHA-256 Merkle tree certificate generation", status: "idle" },
  ]);

  const runSimulation = () => {
    // Reset and step through
    setNodes((prev) => prev.map((n) => ({ ...n, status: "running" })));
    setTimeout(() => {
      setNodes((prev) =>
        prev.map((n) =>
          n.id === "human_approval"
            ? { ...n, status: "interrupted" }
            : n.id === "erp_sync" || n.id === "audit_seal"
            ? { ...n, status: "idle" }
            : { ...n, status: "completed" }
        )
      );
    }, 800);
  };

  const resumeSimulation = () => {
    setNodes((prev) =>
      prev.map((n) => (n.id === "human_approval" ? { ...n, status: "completed", latency: "Approved by Manager" } : n))
    );
    setTimeout(() => {
      setNodes((prev) =>
        prev.map((n) => ({ ...n, status: "completed" }))
      );
    }, 600);
  };

  return (
    <div className="page agent-graph-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">AGENTIC ORCHESTRATION ENGINE</p>
          <h1>LangGraph Stateful Workflow Visualizer (Issue #39)</h1>
          <p>
            Real-time DAG visualization of stateful AI agent graph transitions, interrupt checkpoints, and transactional outbox state recovery.
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button className="secondary-button" onClick={runSimulation}>
            ▶ Run Step-by-Step Simulation
          </button>
          <button className="primary-button" onClick={resumeSimulation}>
            ✅ Simulate Manager Approve & Resume
          </button>
        </div>
      </div>

      <div className="workspace-grid" style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
        {/* Visual Graph Canvas */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "24px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px" }}>
            <span style={{ fontSize: "14px", fontWeight: "bold", color: "#818cf8" }}>Graph Execution Pipeline: StateGraph(OrderState)</span>
            <span className="badge" style={{ background: "#312e81", color: "#c7d2fe" }}>Active Checkpointer: MemorySaver</span>
          </div>

          <div className="graph-nodes-flow" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {nodes.map((node, idx) => {
              const isSelected = selectedNode === node.id;
              const colorMap = {
                completed: { border: "#10b981", bg: "#064e3b33", badge: "#34d399", text: "COMPLETED" },
                interrupted: { border: "#f59e0b", bg: "#78350f33", badge: "#fbbf24", text: "PAUSED (WAITING HITL)" },
                running: { border: "#3b82f6", bg: "#1e3a8a33", badge: "#60a5fa", text: "RUNNING" },
                idle: { border: "#4b5563", bg: "#1f293733", badge: "#9ca3af", text: "PENDING" },
                skipped: { border: "#6b7280", bg: "#11182733", badge: "#6b7280", text: "SKIPPED" },
              };
              const style = colorMap[node.status];

              return (
                <div key={node.id}>
                  <div
                    onClick={() => setSelectedNode(node.id)}
                    style={{
                      border: `2px solid ${isSelected ? "#818cf8" : style.border}`,
                      background: style.bg,
                      padding: "16px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      boxShadow: isSelected ? "0 0 15px #818cf844" : "none",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: "bold", fontSize: "15px", color: "#fff" }}>{node.name}</div>
                      <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>{node.description}</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: "11px", fontWeight: "bold", padding: "4px 8px", borderRadius: "4px", background: "#00000066", color: style.badge }}>
                        {style.text}
                      </span>
                      {node.latency && <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "4px" }}>{node.latency}</div>}
                    </div>
                  </div>
                  {idx < nodes.length - 1 && (
                    <div style={{ textAlign: "center", color: "#4b5563", fontSize: "16px", margin: "4px 0" }}>
                      ↓
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* State Inspector Sidebar */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <h3 style={{ fontSize: "15px", color: "#fff", marginBottom: "12px" }}>Graph State & Memory Snapshot</h3>
          <div style={{ fontSize: "12px", color: "#9ca3af", marginBottom: "16px" }}>
            Thread ID: <code style={{ color: "#818cf8" }}>{activeThread}</code>
          </div>

          <div style={{ background: "#0d1117", padding: "14px", borderRadius: "6px", fontFamily: "monospace", fontSize: "12px", color: "#e6edf3", maxHeight: "400px", overflowY: "auto" }}>
            <div style={{ color: "#7ee787" }}>// Current State Payload:</div>
            {JSON.stringify(
              {
                thread_id: activeThread,
                current_node: selectedNode,
                checkpoint_status: nodes.find((n) => n.id === selectedNode)?.status,
                variables: {
                  order_id: "PO-2026-8899",
                  findings_count: 2,
                  risk_level: "HIGH",
                  currency: "VND",
                  interrupt_nodes: ["human_approval"],
                  outbox_synced: nodes.find((n) => n.id === "erp_sync")?.status === "completed",
                },
              },
              null,
              2
            )}
          </div>

          <div style={{ marginTop: "16px", padding: "12px", background: "#1e1e38", borderRadius: "6px", fontSize: "12px", color: "#a5b4fc" }}>
            💡 <strong>LangGraph Checkpoint:</strong> Trạng thái workflow được lưu vào SQLite/MemorySaver. Khi Manager bấm Duyệt trên Telegram hoặc Web, luồng sẽ phục hồi ngay lập tức từ checkpoint mà không phải chạy lại từ đầu!
          </div>
        </div>
      </div>
    </div>
  );
}
