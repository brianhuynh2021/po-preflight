"use client";

import React, { useState } from "react";
import { money } from "@/app/lib/derive";

export function ExtractionReviewStudio() {
  const [selectedPoNumber, setSelectedPoNumber] = useState<string>("PO-10431");
  const [customerName, setCustomerName] = useState("Acme Global Distributors");
  const [currency, setCurrency] = useState("VND");
  const [lineItems, setLineItems] = useState([
    { sku: "LAPTOP-A14", product: "A14 Business Laptop", quantity: 10, unitPrice: 18500000, ocrConfidence: 0.98 },
    { sku: "HEADSET-PRO", product: "Pro Noise-Canceling Headset", quantity: 5, unitPrice: 2800000, ocrConfidence: 0.74 },
  ]);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const updateItem = (index: number, field: string, value: string | number) => {
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

  const totalValue = lineItems.reduce((acc, it) => acc + it.quantity * it.unitPrice, 0);

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
        <div>
          <button className="primary-button" onClick={handleConfirmExtraction}>
            ✓ Confirm & Run Preflight Rules
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          style={{
            padding: "var(--space-3) var(--space-4)",
            background: "var(--green-soft)",
            color: "var(--green)",
            borderRadius: "var(--radius-sm)",
            marginBottom: "var(--space-4)",
            fontWeight: 600,
            fontSize: "var(--text-sm)",
            border: "1px solid rgba(25, 112, 76, 0.2)",
            boxShadow: "var(--elev-1)",
          }}
        >
          {statusMessage}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: "var(--space-5)" }}>
        {/* Left Card: Document Properties */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>Staged Document Properties</h3>
            <span className="badge-clean badge-clean-info">Extraction Staged</span>
          </div>

          <div style={{ marginBottom: "var(--space-3)" }}>
            <label style={{ display: "block", fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--ink)", marginBottom: "var(--space-1)" }}>
              PO NUMBER
            </label>
            <input
              type="text"
              className="input-clean"
              value={selectedPoNumber}
              onChange={(e) => setSelectedPoNumber(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "var(--space-3)" }}>
            <label style={{ display: "block", fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--ink)", marginBottom: "var(--space-1)" }}>
              CUSTOMER ENTITY
            </label>
            <input
              type="text"
              className="input-clean"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "var(--space-4)" }}>
            <label style={{ display: "block", fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--ink)", marginBottom: "var(--space-1)" }}>
              CURRENCY
            </label>
            <select
              className="input-clean"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
            >
              <option value="VND">VND (Vietnamese Dong)</option>
              <option value="USD">USD (US Dollar)</option>
              <option value="EUR">EUR (Euro)</option>
            </select>
          </div>

          <div
            style={{
              padding: "var(--space-3)",
              background: "var(--canvas)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--line)",
              fontSize: "var(--text-xs)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-2)",
            }}
          >
            <div>
              <span style={{ color: "var(--muted)" }}>OCR Vision Engine:</span>{" "}
              <strong>Gemini 2.0 Flash Vision</strong>
            </div>
            <div>
              <span style={{ color: "var(--muted)" }}>Processing Pipeline:</span>{" "}
              <strong>Cascading Parser + Self-Reflection Math</strong>
            </div>
            <div>
              <span style={{ color: "var(--muted)" }}>Confidence Score:</span>{" "}
              <span className="badge-clean badge-clean-success" style={{ marginLeft: "var(--space-1)" }}>
                96.5% Overall
              </span>
            </div>
          </div>
        </div>

        {/* Right Card: Line Items Table & Editor */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>Extracted Line Items (Editable)</h3>
            <span style={{ fontSize: "var(--text-xs)", fontWeight: 600, color: "var(--green)" }}>
              Total: {money(totalValue, currency)}
            </span>
          </div>

          <div className="table-wrap">
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--text-sm)" }}>
              <thead>
                <tr style={{ background: "var(--canvas)", borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                  <th style={{ padding: "var(--space-2) var(--space-3)" }}>SKU</th>
                  <th style={{ padding: "var(--space-2) var(--space-3)" }}>DESCRIPTION</th>
                  <th style={{ padding: "var(--space-2) var(--space-3)" }}>QTY</th>
                  <th style={{ padding: "var(--space-2) var(--space-3)" }}>UNIT PRICE</th>
                  <th style={{ padding: "var(--space-2) var(--space-3)" }}>OCR CONF.</th>
                </tr>
              </thead>
              <tbody>
                {lineItems.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: "var(--space-2) var(--space-3)" }}>
                      <input
                        type="text"
                        className="input-clean"
                        style={{ padding: "var(--space-1) var(--space-2)", fontSize: "var(--text-xs)", fontWeight: 600 }}
                        value={item.sku}
                        onChange={(e) => updateItem(idx, "sku", e.target.value)}
                      />
                    </td>
                    <td style={{ padding: "var(--space-2) var(--space-3)" }}>
                      <input
                        type="text"
                        className="input-clean"
                        style={{ padding: "var(--space-1) var(--space-2)", fontSize: "var(--text-xs)" }}
                        value={item.product}
                        onChange={(e) => updateItem(idx, "product", e.target.value)}
                      />
                    </td>
                    <td style={{ padding: "var(--space-2) var(--space-3)", width: "70px" }}>
                      <input
                        type="number"
                        className="input-clean"
                        style={{ padding: "var(--space-1) var(--space-2)", fontSize: "var(--text-xs)" }}
                        value={item.quantity}
                        onChange={(e) => updateItem(idx, "quantity", Number(e.target.value))}
                      />
                    </td>
                    <td style={{ padding: "var(--space-2) var(--space-3)", width: "120px" }}>
                      <input
                        type="number"
                        className="input-clean"
                        style={{ padding: "var(--space-1) var(--space-2)", fontSize: "var(--text-xs)" }}
                        value={item.unitPrice}
                        onChange={(e) => updateItem(idx, "unitPrice", Number(e.target.value))}
                      />
                    </td>
                    <td style={{ padding: "var(--space-2) var(--space-3)" }}>
                      <span
                        className={`badge-clean ${
                          item.ocrConfidence >= 0.9 ? "badge-clean-success" : "badge-clean-warning"
                        }`}
                      >
                        {(item.ocrConfidence * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

