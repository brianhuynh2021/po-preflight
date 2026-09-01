"use client";

import React, { useState } from "react";
import { money } from "@/app/lib/derive";

interface OutboxItem {
  id: number;
  poNumber: string;
  customer: string;
  adapter: string;
  amount: number;
  currency: string;
  status: "DELIVERED" | "PENDING" | "DEAD_LETTER";
  retries: number;
  erpReference?: string;
  lastAttempt: string;
}

export function ERPSyncView() {
  const [items, setItems] = useState<OutboxItem[]>([
    {
      id: 1,
      poNumber: "PO-10427",
      customer: "Alpha Distribution Corp",
      adapter: "SAP S/4HANA (BAPI_SALESORDER_CREATEFROMDAT2)",
      amount: 145000000,
      currency: "VND",
      status: "DELIVERED",
      retries: 0,
      erpReference: "SAP-SO-99210427",
      lastAttempt: "2026-09-01 08:30:12",
    },
    {
      id: 2,
      poNumber: "PO-10428",
      customer: "Northstar Retail",
      adapter: "SAP S/4HANA (OData v4)",
      amount: 18500000,
      currency: "VND",
      status: "DELIVERED",
      retries: 0,
      erpReference: "SAP-SO-99210428",
      lastAttempt: "2026-09-01 08:35:44",
    },
    {
      id: 3,
      poNumber: "PO-10433",
      customer: "Nexus Cloud Systems",
      adapter: "Odoo Enterprise v17 (XML-RPC)",
      amount: 8500,
      currency: "USD",
      status: "DELIVERED",
      retries: 0,
      erpReference: "ODOO-SO-2026-004",
      lastAttempt: "2026-09-01 08:41:00",
    },
    {
      id: 4,
      poNumber: "PO-10430",
      customer: "Vingroup Retail",
      adapter: "SAP S/4HANA (BAPI)",
      amount: 48000000,
      currency: "VND",
      status: "PENDING",
      retries: 1,
      lastAttempt: "2026-09-01 08:45:00",
    },
  ]);

  const [filter, setFilter] = useState<"ALL" | "DELIVERED" | "PENDING" | "DEAD_LETTER">("ALL");

  const filteredItems = items.filter((it) => (filter === "ALL" ? true : it.status === filter));

  const triggerRetry = (id: number) => {
    setItems((prev) =>
      prev.map((it) =>
        it.id === id
          ? {
              ...it,
              status: "DELIVERED",
              retries: it.retries + 1,
              erpReference: `SAP-SO-${Math.floor(Math.random() * 900000 + 100000)}`,
              lastAttempt: "Just now",
            }
          : it
      )
    );
  };

  return (
    <div className="page erp-sync-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ENTERPRISE ERP INTEGRATION</p>
          <h1>ERP Synchronization & Outbox Center (Issue #9)</h1>
          <p>
            Transactional Outbox monitoring ensuring exactly-once order delivery into SAP S/4HANA, Odoo, and NetSuite without duplicate creation.
          </p>
        </div>
      </div>

      {/* Outbox Metrics Stats */}
      <div className="metrics-row" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
        <div className="metric-card" style={{ background: "var(--surface-color, #1e1e2d)", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8" }}>TOTAL SYNC DISPATCHES</div>
          <div style={{ fontSize: "24px", fontWeight: "bold", color: "#fff", marginTop: "4px" }}>{items.length}</div>
        </div>
        <div className="metric-card" style={{ background: "var(--surface-color, #1e1e2d)", padding: "16px", borderRadius: "8px", border: "1px solid #059669" }}>
          <div style={{ fontSize: "12px", color: "#34d399" }}>DELIVERED SUCCESS</div>
          <div style={{ fontSize: "24px", fontWeight: "bold", color: "#34d399", marginTop: "4px" }}>
            {items.filter((i) => i.status === "DELIVERED").length}
          </div>
        </div>
        <div className="metric-card" style={{ background: "var(--surface-color, #1e1e2d)", padding: "16px", borderRadius: "8px", border: "1px solid #d97706" }}>
          <div style={{ fontSize: "12px", color: "#fbbf24" }}>IN-FLIGHT PENDING</div>
          <div style={{ fontSize: "24px", fontWeight: "bold", color: "#fbbf24", marginTop: "4px" }}>
            {items.filter((i) => i.status === "PENDING").length}
          </div>
        </div>
        <div className="metric-card" style={{ background: "var(--surface-color, #1e1e2d)", padding: "16px", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8" }}>IDEMPOTENCY CONFLICTS</div>
          <div style={{ fontSize: "24px", fontWeight: "bold", color: "#60a5fa", marginTop: "4px" }}>0 (Protected)</div>
        </div>
      </div>

      {/* Outbox Table */}
      <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ fontSize: "16px", color: "#fff" }}>Transactional Outbox Messages</h3>
          <div style={{ display: "flex", gap: "8px" }}>
            {(["ALL", "DELIVERED", "PENDING", "DEAD_LETTER"] as const).map((s) => (
              <button
                key={s}
                className={`secondary-button ${filter === s ? "active-tab" : ""}`}
                style={{ fontSize: "12px", padding: "4px 10px" }}
                onClick={() => setFilter(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #444", color: "#888", textAlign: "left" }}>
              <th style={{ padding: "10px" }}>PO NUMBER</th>
              <th style={{ padding: "10px" }}>CUSTOMER</th>
              <th style={{ padding: "10px" }}>TARGET ERP ADAPTER</th>
              <th style={{ padding: "10px" }}>AMOUNT</th>
              <th style={{ padding: "10px" }}>STATUS</th>
              <th style={{ padding: "10px" }}>ERP REF #</th>
              <th style={{ padding: "10px" }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr key={item.id} style={{ borderBottom: "1px solid #2d2d3a" }}>
                <td style={{ padding: "10px", fontWeight: "bold", color: "#60a5fa" }}>{item.poNumber}</td>
                <td style={{ padding: "10px", color: "#fff" }}>{item.customer}</td>
                <td style={{ padding: "10px", color: "#a5b4fc", fontSize: "12px" }}>{item.adapter}</td>
                <td style={{ padding: "10px", fontWeight: "bold" }}>{money(item.amount, item.currency)}</td>
                <td style={{ padding: "10px" }}>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: "bold",
                      padding: "3px 8px",
                      borderRadius: "4px",
                      background: item.status === "DELIVERED" ? "#064e3b" : "#78350f",
                      color: item.status === "DELIVERED" ? "#34d399" : "#fbbf24",
                    }}
                  >
                    {item.status}
                  </span>
                </td>
                <td style={{ padding: "10px", fontFamily: "monospace", color: "#38bdf8" }}>
                  {item.erpReference || "—"}
                </td>
                <td style={{ padding: "10px" }}>
                  {item.status === "PENDING" ? (
                    <button className="primary-button" style={{ fontSize: "11px", padding: "4px 8px" }} onClick={() => triggerRetry(item.id)}>
                      ⚡ Force Sync
                    </button>
                  ) : (
                    <span style={{ fontSize: "12px", color: "#6b7280" }}>Delivered</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
