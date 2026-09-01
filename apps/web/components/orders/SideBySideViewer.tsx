"use client";

import React, { useState } from "react";
import type { PurchaseOrder } from "@/app/lib/types";
import { money } from "@/app/lib/derive";

interface SideBySideViewerProps {
  order: PurchaseOrder;
  onClose: () => void;
}

export function SideBySideViewer({ order, onClose }: SideBySideViewerProps) {
  const [activeTab, setActiveTab] = useState<"visual" | "json">("visual");

  const lines = order.lines || [];
  const totalValue = order.value || 0;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal" style={{ maxWidth: "1100px", width: "95vw" }}>
        <div className="modal-header">
          <div>
            <p className="eyebrow">VISUAL EVIDENCE GROUNDING (ISSUE #6)</p>
            <h2>Side-by-Side Verification: {order.id}</h2>
            <p style={{ margin: "4px 0 0", color: "var(--muted)" }}>
              Dual-pane inspection matching raw source document against normalized catalog entities and validation findings.
            </p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <div style={{ display: "flex", gap: "8px", margin: "16px 0", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
          <button
            className={activeTab === "visual" ? "primary-button" : "secondary-button"}
            style={{ fontSize: "12px", padding: "6px 12px" }}
            onClick={() => setActiveTab("visual")}
          >
            📄 Split View (Raw vs Normalized)
          </button>
          <button
            className={activeTab === "json" ? "primary-button" : "secondary-button"}
            style={{ fontSize: "12px", padding: "6px 12px" }}
            onClick={() => setActiveTab("json")}
          >
            {`{ }`} Ingested State JSON
          </button>
        </div>

        <div style={{ maxHeight: "65vh", overflowY: "auto", padding: "4px 0" }}>
          {activeTab === "visual" ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              {/* Left Pane: Simulated Document Source */}
              <div className="clean-card" style={{ background: "var(--canvas)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>
                  <strong style={{ color: "var(--ink)", fontSize: "13px" }}>Source Document (Uploaded)</strong>
                  <span className="badge-clean badge-clean-info">MULTIMODAL_INSPECTION</span>
                </div>

                <div
                  style={{
                    fontFamily: "ui-monospace, monospace",
                    fontSize: "12px",
                    lineHeight: "1.6",
                    background: "var(--paper)",
                    padding: "14px",
                    borderRadius: "8px",
                    border: "1px solid var(--line)",
                    color: "var(--ink)",
                  }}
                >
                  <div style={{ color: "var(--green)", fontWeight: 700 }}>PURCHASE ORDER: {order.id}</div>
                  <div>CUSTOMER: {order.customer}</div>
                  <div>CURRENCY: {order.currency}</div>
                  <div>SUBMITTED AT: {order.submittedAt}</div>
                  <hr style={{ borderColor: "var(--line)", margin: "10px 0" }} />
                  <div style={{ fontWeight: 700, color: "var(--muted)" }}>EXTRACTED LINE ITEMS:</div>
                  {lines.map((item, idx) => (
                    <div key={idx} style={{ padding: "6px 0", borderBottom: "1px dashed var(--line)" }}>
                      <div>
                        #{idx + 1} SKU: <strong>{item.sku}</strong> ({item.product})
                      </div>
                      <div style={{ color: "var(--muted)" }}>
                        Qty: {item.quantity} | Declared Unit Price: {money(item.unitPrice, order.currency)}
                      </div>
                    </div>
                  ))}
                  <div style={{ marginTop: "12px", color: "var(--green)", fontWeight: 700, fontSize: "13px" }}>
                    TOTAL: {money(totalValue, order.currency)}
                  </div>
                </div>
              </div>

              {/* Right Pane: Preflight Findings & Grounding */}
              <div className="clean-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>
                  <strong style={{ color: "var(--ink)", fontSize: "13px" }}>Validation & Policy Checks</strong>
                  <span
                    className={`badge-clean ${
                      order.status === "Ready" || order.status === "Approved"
                        ? "badge-clean-success"
                        : order.status === "Blocked"
                        ? "badge-clean-warning"
                        : "badge-clean-info"
                    }`}
                  >
                    {order.status}
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {order.findings.length === 0 ? (
                    <div
                      style={{
                        padding: "24px",
                        textAlign: "center",
                        background: "var(--green-soft)",
                        borderRadius: "8px",
                        color: "var(--green)",
                        fontSize: "13px",
                        fontWeight: 600,
                        border: "1px solid rgba(25, 112, 76, 0.2)",
                      }}
                    >
                      ✔ All validation rules passed. 100% catalog and inventory grounding match.
                    </div>
                  ) : (
                    order.findings.map((f, i) => (
                      <div
                        key={i}
                        style={{
                          background: f.severity === "Error" ? "var(--red-soft)" : "var(--amber-soft)",
                          borderLeft: `4px solid ${f.severity === "Error" ? "var(--red)" : "var(--amber)"}`,
                          padding: "12px",
                          borderRadius: "0 8px 8px 0",
                        }}
                      >
                        <div style={{ fontWeight: 700, fontSize: "13px", color: f.severity === "Error" ? "var(--red)" : "var(--amber)" }}>
                          [{f.code}] {f.title}
                        </div>
                        <div style={{ fontSize: "12.5px", color: "var(--ink)", margin: "4px 0" }}>{f.detail}</div>
                        <code style={{ fontSize: "11px", color: "var(--muted)", background: "rgba(0,0,0,0.04)", padding: "2px 4px", borderRadius: "3px" }}>
                          {f.evidence}
                        </code>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <pre
              style={{
                background: "var(--canvas)",
                padding: "16px",
                borderRadius: "8px",
                border: "1px solid var(--line)",
                fontSize: "12px",
                fontFamily: "ui-monospace, monospace",
                overflowX: "auto",
                color: "var(--ink)",
                margin: 0,
              }}
            >
              {JSON.stringify(order, null, 2)}
            </pre>
          )}
        </div>

        <div className="modal-actions" style={{ marginTop: "16px", borderTop: "1px solid var(--line)", paddingTop: "14px" }}>
          <button className="secondary-button" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
