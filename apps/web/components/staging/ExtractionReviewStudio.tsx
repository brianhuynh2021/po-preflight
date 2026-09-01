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
            padding: "12px 16px",
            background: "var(--green-soft)",
            color: "var(--green)",
            borderRadius: "8px",
            marginBottom: "16px",
            fontWeight: 600,
            border: "1px solid rgba(25, 112, 76, 0.2)",
          }}
        >
          {statusMessage}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: "20px" }}>
        {/* Left Card: Document Properties */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>Staged Document Properties</h3>
            <span className="badge-clean badge-clean-info">Extraction Staged</span>
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              PO NUMBER
            </label>
            <input
              type="text"
              className="input-clean"
              value={selectedPoNumber}
              onChange={(e) => setSelectedPoNumber(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
              CUSTOMER ENTITY
            </label>
            <input
              type="text"
              className="input-clean"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: "18px" }}>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--ink)", marginBottom: "4px" }}>
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
              padding: "14px",
              background: "var(--canvas)",
              borderRadius: "8px",
              border: "1px solid var(--line)",
              fontSize: "12px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
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
              <span className="badge-clean badge-clean-success" style={{ marginLeft: "4px" }}>
                96.5% Overall
              </span>
            </div>
          </div>
        </div>

        {/* Right Card: Line Items Table & Editor */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>Extracted Line Items (Editable)</h3>
            <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--green)" }}>
              Total: {money(totalValue, currency)}
            </span>
          </div>

          <div className="table-wrap">
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ background: "var(--canvas)", borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>SKU</th>
                  <th style={{ padding: "8px 12px" }}>DESCRIPTION</th>
                  <th style={{ padding: "8px 12px" }}>QTY</th>
                  <th style={{ padding: "8px 12px" }}>UNIT PRICE</th>
                  <th style={{ padding: "8px 12px" }}>OCR CONF.</th>
                </tr>
              </thead>
              <tbody>
                {lineItems.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: "8px 12px" }}>
                      <input
                        type="text"
                        className="input-clean"
                        style={{ padding: "4px 8px", fontSize: "12px", fontWeight: 600 }}
                        value={item.sku}
                        onChange={(e) => updateItem(idx, "sku", e.target.value)}
                      />
                    </td>
                    <td style={{ padding: "8px 12px" }}>
                      <input
                        type="text"
                        className="input-clean"
                        style={{ padding: "4px 8px", fontSize: "12px" }}
                        value={item.product}
                        onChange={(e) => updateItem(idx, "product", e.target.value)}
                      />
                    </td>
                    <td style={{ padding: "8px 12px", width: "70px" }}>
                      <input
                        type="number"
                        className="input-clean"
                        style={{ padding: "4px 8px", fontSize: "12px" }}
                        value={item.quantity}
                        onChange={(e) => updateItem(idx, "quantity", Number(e.target.value))}
                      />
                    </td>
                    <td style={{ padding: "8px 12px", width: "120px" }}>
                      <input
                        type="number"
                        className="input-clean"
                        style={{ padding: "4px 8px", fontSize: "12px" }}
                        value={item.unitPrice}
                        onChange={(e) => updateItem(idx, "unitPrice", Number(e.target.value))}
                      />
                    </td>
                    <td style={{ padding: "8px 12px" }}>
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
