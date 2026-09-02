"use client";

import React, { useState } from "react";
import { Play, RotateCcw, Clock } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

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
  const { createRipple } = useRipple();
  const [selectedThread] = useState("thread-demo-8899");
  const [activeStep, setActiveStep] = useState<string>("human_approval");
  const [isResumed, setIsResumed] = useState(false);

  const nodes: NodeState[] = [
    {
      id: "document_ingestion",
      name: "Bóc tách tài liệu & OCR",
      category: "INGEST",
      status: "COMPLETED",
      latencyMs: 142,
      description: "Động cơ OCR: Trích xuất tiêu đề, các dòng chi tiết và đối chiếu số học.",
      outputPayload: {
        po_number: "PO-2026-8899",
        customer: "Vingroup Retail",
        declared_total: 108440000,
        math_check: "PASS (Khớp 100%)",
      },
    },
    {
      id: "hybrid_sku_rag",
      name: "Khớp mã 4 tầng (4-Tier RAG)",
      category: "RAG",
      status: "COMPLETED",
      latencyMs: 12,
      description: "Thác lọc mã: Bí danh khách hàng -> Khớp chính xác -> Mờ Fuzzy -> Ngữ nghĩa Vector.",
      outputPayload: {
        resolved_skus: 3,
        tier_breakdown: { tier_1: 1, tier_2: 1, tier_3: 1 },
      },
    },
    {
      id: "deterministic_rules",
      name: "Động cơ Quy tắc Nghiệp vụ",
      category: "RULES",
      status: "COMPLETED",
      latencyMs: 4,
      description: "Đánh giá dung sai giá, lượng tồn kho khả dụng và đơn hàng trùng lặp.",
      outputPayload: {
        findings_count: 2,
        blocking_errors: 1,
        severity: "BLOCKED",
      },
    },
    {
      id: "human_approval",
      name: "Điểm dừng Duyệt người dùng (HITL)",
      category: "HITL",
      status: isResumed ? "COMPLETED" : "PAUSED",
      latencyMs: isResumed ? 1200 : 0,
      description: "Checkpoint lưu trạng thái phiên và gửi thông báo phê duyệt tới Telegram Bot.",
      outputPayload: isResumed
        ? { decision: "APPROVED", actor: "Operations Director", note: "VIP customer override" }
        : { checkpoint: "paused_before_node", pending_approval: true },
    },
    {
      id: "erp_outbox_dispatch",
      name: "Ghi sổ ERP Transactional Outbox",
      category: "ERP",
      status: isResumed ? "COMPLETED" : "PENDING",
      latencyMs: isResumed ? 18 : 0,
      description: "Ghi nhận bản tin Outbox vào cơ sở dữ liệu và gửi sang ERP qua Adapter.",
      outputPayload: isResumed
        ? { erp_status: "DELIVERED", transaction_id: "MISA-SO-20268899" }
        : { status: "awaiting_approval" },
    },
  ];

  const selectedNode = nodes.find((n) => n.id === activeStep) || nodes[0];

  const handleSimulateResume = (e: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    setIsResumed(true);
  };

  const handleReset = (e: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    setIsResumed(false);
  };

  return (
    <div className="page agent-graph-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">QUY TRÌNH LANGGRAPH AI STATEFUL</p>
          <h1>Sơ đồ Luồng Tác vụ Stateful LangGraph</h1>
          <p>
            Giám sát trực quan tiến trình thực thi đồ thị tác vụ, điểm lưu trạng thái (Checkpointer) và các điểm ngắt duyệt người dùng (HITL).
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          {!isResumed && (
            <button className="primary-button interactive" onClick={handleSimulateResume} style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}>
              <Play size={16} />
              <span>Tiếp tục luồng (Resume DAG)</span>
            </button>
          )}
          {isResumed && (
            <button className="secondary-button interactive" onClick={handleReset} style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}>
              <RotateCcw size={16} />
              <span>Đặt lại điểm lưu (Reset)</span>
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "var(--space-5)" }}>
        {/* Left: DAG Pipeline Canvas */}
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <div>
              <h3 style={{ fontSize: "1.1rem", margin: "0 0 4px" }}>Luồng thực thi: {selectedThread}</h3>
              <small style={{ color: "var(--muted)" }}>Checkpointer: MemorySaver (Trạng thái theo luồng)</small>
            </div>
            <span
              className={`badge-clean ${
                isResumed ? "badge-clean-success" : "badge-clean-warning"
              }`}
            >
              {isResumed ? "● HOÀN THÀNH" : "⏸ ĐANG TẠM DỪNG (HITL)"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", padding: "10px 0" }}>
            {nodes.map((node, index) => {
              const isSelected = activeStep === node.id;

              return (
                <div
                  key={node.id}
                  onClick={() => setActiveStep(node.id)}
                  style={{
                    padding: "var(--space-3)",
                    background: isSelected ? "rgba(16,185,129,0.08)" : "var(--canvas)",
                    border: isSelected ? "2px solid var(--color-primary)" : "1px solid var(--line)",
                    borderRadius: "var(--radius-md)",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                      <span style={{ fontSize: "0.875rem", fontWeight: 800, color: "var(--color-primary)" }}>
                        #{index + 1}
                      </span>
                      <strong style={{ fontSize: "0.95rem", color: "var(--ink)" }}>{node.name}</strong>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--muted)", display: "inline-flex", alignItems: "center", gap: 3 }}>
                        <Clock size={12} /> {node.latencyMs}ms
                      </span>
                      <span
                        className={`badge-clean ${
                          node.status === "COMPLETED"
                            ? "badge-clean-success"
                            : node.status === "PAUSED"
                            ? "badge-clean-warning"
                            : "badge-clean-neutral"
                        }`}
                        style={{ fontSize: "0.7rem" }}
                      >
                        {node.status === "COMPLETED" ? "Đã xong" : node.status === "PAUSED" ? "Tạm dừng" : "Đang chờ"}
                      </span>
                    </div>
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: "0.8125rem", color: "var(--muted)" }}>
                    {node.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Node Payload & Inspector */}
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <h3 style={{ fontSize: "1.1rem", margin: 0 }}>Chi tiết nút tác vụ</h3>
            <span className="badge-clean badge-clean-info">{selectedNode.category}</span>
          </div>

          <h4 style={{ margin: "0 0 8px", fontSize: "1rem", color: "var(--ink)" }}>{selectedNode.name}</h4>
          <p style={{ fontSize: "0.875rem", color: "var(--muted)", margin: "0 0 16px", lineHeight: 1.5 }}>
            {selectedNode.description}
          </p>

          <div style={{ background: "var(--canvas)", padding: "12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--line)" }}>
            <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--muted)", marginBottom: "6px" }}>
              DỮ LIỆU ĐẦU RA (STATE PAYLOAD):
            </div>
            <pre style={{ margin: 0, fontSize: "0.75rem", color: "var(--ink)", overflowX: "auto", fontFamily: "ui-monospace, monospace" }}>
              {JSON.stringify(selectedNode.outputPayload || {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
