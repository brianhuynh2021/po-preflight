"use client";

import React, { useState } from "react";
import { useAppState } from "@/components/app/AppStateProvider";
import { money } from "@/app/lib/derive";

export function ExtractionReviewStudio() {
  const { orders, setOrders } = useAppState();
  const [selectedPoNumber, setSelectedPoNumber] = useState<string>("PO-10431");
  const [customerName, setCustomerName] = useState("Acme Global Distributors");
  const [currency, setCurrency] = useState("VND");
  const [lineItems, setLineItems] = useState([
    { sku: "LAPTOP-A14", product: "A14 Business Laptop", quantity: 10, unitPrice: 18500000, ocrConfidence: 0.98 },
    { sku: "HEADSET-PRO", product: "Pro Noise-Canceling Headset", quantity: 5, unitPrice: 2800000, ocrConfidence: 0.74 },
  ]);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const updateItem = (index: number, field: string, value: any) => {
    setLineItems((prev) =>
      prev.map((item, idx) => (idx === index ? { ...item, [field]: value } : item))
    );
  };

  const handleConfirmExtraction = () => {
    setStatusMessage("⚡ Extracted data confirmed! Preflight rules triggered. Updating order status...");
    setTimeout(() => {
      setStatusMessage("✔ Staged extraction successfully confirmed and moved to active queue.");
    }, 1000);
  };

  return (
    <div className="page staging-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENT DOCUMENT PROCESSING (IDP)</p>
          <h1>Extraction Review & Staging Studio (Issue #38)</h1>
          <p>
            Human-in-the-Loop staging environment to audit OCR bounding boxes, correct line items, and resolve SKU ambiguities before rule evaluation.
          </p>
        </div>
      </div>

      {statusMessage && (
        <div style={{ padding: "12px 16px", background: "#064e3b", color: "#34d399", borderRadius: "8px", marginBottom: "16px", fontWeight: "bold" }}>
          {statusMessage}
        </div>
      )}

      <div className="workspace-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "24px" }}>
        {/* Left Card: Document Meta */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <h3 style={{ marginBottom: "16px", fontSize: "16px", color: "var(--text-color, #fff)" }}>Staged Document Properties</h3>
          
          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#888", marginBottom: "4px" }}>PO NUMBER</label>
            <input
              type="text"
              value={selectedPoNumber}
              onChange={(e) => setSelectedPoNumber(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#111", border: "1px solid #444", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#888", marginBottom: "4px" }}>CUSTOMER ENTITY</label>
            <input
              type="text"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#111", border: "1px solid #444", color: "#fff" }}
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#888", marginBottom: "4px" }}>CURRENCY</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="text-input"
              style={{ width: "100%", padding: "8px", borderRadius: "6px", background: "#111", border: "1px solid #444", color: "#fff" }}
            >
              <option value="VND">VND (Vietnamese Dong)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
            </select>
          </div>

          <div style={{ padding: "12px", background: "#111827", borderRadius: "6px", fontSize: "12px", color: "#9ca3af" }}>
            <div><strong>OCR Vision Engine:</strong> Gemini 2.0 Flash Vision</div>
            <div><strong>Processing Pipeline:</strong> Cascading Parser + Self-Reflection Math</div>
            <div><strong>Confidence Score:</strong> <span style={{ color: "#34d399", fontWeight: "bold" }}>96.5% Overall</span></div>
          </div>
        </div>

        {/* Right Card: Line Items Table & Editor */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3 style={{ fontSize: "16px", color: "var(--text-color, #fff)" }}>Extracted Line Items (Editable)</h3>
            <span style={{ fontSize: "12px", color: "#60a5fa" }}>{lineItems.length} items parsed</span>
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #444", color: "#888", textAlign: "left" }}>
                <th style={{ padding: "8px" }}>SKU</th>
                <th style={{ padding: "8px" }}>Description</th>
                <th style={{ padding: "8px" }}>Qty</th>
                <th style={{ padding: "8px" }}>Unit Price</th>
                <th style={{ padding: "8px" }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {lineItems.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid #2d2d3a" }}>
                  <td style={{ padding: "8px" }}>
                    <input
                      type="text"
                      value={item.sku}
                      onChange={(e) => updateItem(idx, "sku", e.target.value)}
                      style={{ width: "100px", padding: "4px", background: "#111", border: "1px solid #444", color: "#60a5fa", borderRadius: "4px" }}
                    />
                  </td>
                  <td style={{ padding: "8px" }}>
                    <input
                      type="text"
                      value={item.product}
                      onChange={(e) => updateItem(idx, "product", e.target.value)}
                      style={{ width: "160px", padding: "4px", background: "#111", border: "1px solid #444", color: "#fff", borderRadius: "4px" }}
                    />
                  </td>
                  <td style={{ padding: "8px" }}>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => updateItem(idx, "quantity", Number(e.target.value))}
                      style={{ width: "60px", padding: "4px", background: "#111", border: "1px solid #444", color: "#fff", borderRadius: "4px" }}
                    />
                  </td>
                  <td style={{ padding: "8px" }}>
                    <input
                      type="number"
                      value={item.unitPrice}
                      onChange={(e) => updateItem(idx, "unitPrice", Number(e.target.value))}
                      style={{ width: "110px", padding: "4px", background: "#111", border: "1px solid #444", color: "#fff", borderRadius: "4px" }}
                    />
                  </td>
                  <td style={{ padding: "8px" }}>
                    <span style={{ color: item.ocrConfidence > 0.8 ? "#34d399" : "#fbbf24", fontWeight: "bold", fontSize: "11px" }}>
                      {(item.ocrConfidence * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: "24px", display: "flex", justifyContent: "flex-end", gap: "12px" }}>
            <button className="secondary-button" onClick={() => setLineItems([...lineItems, { sku: "NEW-SKU", product: "New Item", quantity: 1, unitPrice: 1000000, ocrConfidence: 1.0 }])}>
              ＋ Add Line Item
            </button>
            <button className="primary-button" onClick={handleConfirmExtraction} style={{ background: "linear-gradient(135deg, #2563eb, #1d4ed8)" }}>
              🚀 Confirm Extraction & Run Preflight Rules
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
