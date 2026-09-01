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

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel side-by-side-modal" style={{ maxWidth: "1100px", width: "95vw" }}>
        <div className="modal-header">
          <div>
            <p className="eyebrow">VISUAL EVIDENCE GROUNDING (ISSUE #6)</p>
            <h2 className="modal-title">Side-by-Side Verification: {order.id}</h2>
            <p className="modal-sub">
              Dual-pane inspection matching source document against extracted catalog entities and validation findings.
            </p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <div className="side-by-side-toolbar" style={{ display: "flex", gap: "10px", padding: "10px 0", borderBottom: "1px solid var(--border-color)" }}>
          <button
            className={`secondary-button ${activeTab === "visual" ? "active-tab" : ""}`}
            onClick={() => setActiveTab("visual")}
          >
            📄 Split View (Raw vs Extracted)
          </button>
          <button
            className={`secondary-button ${activeTab === "json" ? "active-tab" : ""}`}
            onClick={() => setActiveTab("json")}
          >
            {`{ }`} Raw Ingested JSON
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: "70vh", overflowY: "auto", padding: "15px 0" }}>
          {activeTab === "visual" ? (
            <div className="split-pane-container" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              {/* Left Pane: Simulated Document Source */}
              <div className="document-pane" style={{ background: "var(--surface-color, #1a1a24)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color, #333)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", borderBottom: "1px solid #444", paddingBottom: "8px" }}>
                  <strong style={{ color: "var(--accent-blue, #60a5fa)" }}>Source Document (Uploaded)</strong>
                  <span className="badge" style={{ fontSize: "11px" }}>FORMAT: MULTIMODAL_INSPECTION</span>
                </div>
                <div style={{ fontFamily: "monospace", fontSize: "12px", lineHeight: "1.6", background: "#0d1117", padding: "12px", borderRadius: "6px", color: "#e6edf3" }}>
                  <div style={{ color: "#7ee787", fontWeight: "bold" }}>PURCHASE ORDER: {order.id}</div>
                  <div>CUSTOMER: {order.customer}</div>
                  <div>CURRENCY: {order.currency}</div>
                  <div>SUBMITTED AT: {order.submittedAt}</div>
                  <hr style={{ borderColor: "#30363d", margin: "8px 0" }} />
                  <div style={{ fontWeight: "bold", color: "#d2a8ff" }}>DECLARED LINE ITEMS:</div>
                  {order.lineItems.map((item, idx) => (
                    <div key={idx} style={{ padding: "6px 0", borderBottom: "1px dashed #21262d" }}>
                      <div>#{idx + 1} SKU: <span style={{ color: "#58a6ff" }}>{item.sku}</span> ({item.product})</div>
                      <div>Qty: {item.quantity} | Declared Unit Price: {money(item.unitPrice, order.currency)}</div>
                    </div>
                  ))}
                  <div style={{ marginTop: "12px", color: "#7ee787", fontWeight: "bold" }}>
                    TOTAL: {money(order.totalAmount, order.currency)}
                  </div>
                </div>
              </div>

              {/* Right Pane: Extracted & Grounded Catalog Match */}
              <div className="grounding-pane" style={{ background: "var(--surface-color, #1a1a24)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color, #333)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", borderBottom: "1px solid #444", paddingBottom: "8px" }}>
                  <strong style={{ color: "var(--accent-green, #34d399)" }}>Preflight Verification & Findings</strong>
                  <span className="badge" style={{ fontSize: "11px", background: order.status === "Ready" ? "#064e3b" : "#78350f", color: "#fff" }}>
                    {order.status}
                  </span>
                </div>
                <div className="findings-grounding-list">
                  {order.findings.length === 0 ? (
                    <div style={{ padding: "20px", textAlign: "center", background: "#064e3b22", borderRadius: "6px", color: "#34d399" }}>
                      ✔ No violations found. 100% catalog and inventory grounding match.
                    </div>
                  ) : (
                    order.findings.map((f, i) => (
                      <div
                        key={i}
                        style={{
                          background: f.severity === "Error" ? "#450a0a22" : "#78350f22",
                          borderLeft: `4px solid ${f.severity === "Error" ? "#ef4444" : "#f59e0b"}`,
                          padding: "10px",
                          marginBottom: "10px",
                          borderRadius: "0 6px 6px 0",
                        }}
                      >
                        <div style={{ fontWeight: "bold", fontSize: "13px", color: f.severity === "Error" ? "#f87171" : "#fbbf24" }}>
                          [{f.code}] {f.title}
                        </div>
                        <div style={{ fontSize: "12px", margin: "4px 0", color: "#ccc" }}>{f.detail}</div>
                        <div style={{ fontSize: "11px", fontFamily: "monospace", background: "#00000044", padding: "4px 8px", borderRadius: "4px", color: "#a5f3fc" }}>
                          EVIDENCE: {f.evidence}
                        </div>
                      </div>
                    ))
                  )}

                  <div style={{ marginTop: "15px", padding: "10px", background: "#1e293b", borderRadius: "6px" }}>
                    <div style={{ fontSize: "12px", fontWeight: "bold", color: "#94a3b8", marginBottom: "6px" }}>WAREHOUSE STOCK AVAILABILITY</div>
                    {order.lineItems.map((item, idx) => (
                      <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", padding: "3px 0" }}>
                        <span>{item.sku}:</span>
                        <span style={{ color: item.available >= item.quantity ? "#34d399" : "#f87171", fontWeight: "bold" }}>
                          {item.available} in stock (Req: {item.quantity})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <pre style={{ background: "#0d1117", color: "#7ee787", padding: "16px", borderRadius: "8px", overflowX: "auto", fontSize: "12px" }}>
              {JSON.stringify(order, null, 2)}
            </pre>
          )}
        </div>

        <div className="modal-footer" style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "15px" }}>
          <button className="secondary-button" onClick={onClose}>
            Close Inspection
          </button>
        </div>
      </div>
    </div>
  );
}
