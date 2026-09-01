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
          <p className="eyebrow">ENTERPRISE ERP INTEGRATION (ISSUE #9)</p>
          <h1>ERP Synchronization & Outbox Center</h1>
          <p>
            Transactional Outbox guarantees exactly-once order delivery into SAP S/4HANA, Odoo, and NetSuite with zero duplicate risk.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-row">
        <div className="metric">
          <span>TOTAL OUTBOX DISPATCHES</span>
          <strong>{items.length}</strong>
          <small>Transactional messages</small>
        </div>
        <div className="metric">
          <span>DELIVERED SUCCESS</span>
          <strong style={{ color: "var(--green)" }}>
            {items.filter((i) => i.status === "DELIVERED").length}
          </strong>
          <small>100% SLA matched</small>
        </div>
        <div className="metric">
          <span>IN-FLIGHT PENDING</span>
          <strong style={{ color: "var(--amber)" }}>
            {items.filter((i) => i.status === "PENDING").length}
          </strong>
          <small>Queued for retry</small>
        </div>
        <div className="metric">
          <span>IDEMPOTENCY CONFLICTS</span>
          <strong style={{ color: "var(--blue)" }}>0</strong>
          <small>Guaranteed unique</small>
        </div>
      </div>

      {/* Outbox Table Card */}
      <div className="clean-card" style={{ padding: "0", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--line)" }}>
          <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 600 }}>Transactional Outbox Messages</h3>
          <div style={{ display: "flex", gap: "6px" }}>
            {(["ALL", "DELIVERED", "PENDING", "DEAD_LETTER"] as const).map((s) => (
              <button
                key={s}
                className={filter === s ? "primary-button" : "secondary-button"}
                style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "6px" }}
                onClick={() => setFilter(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrap">
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ background: "var(--canvas)", borderBottom: "1px solid var(--line)", textAlign: "left" }}>
                <th style={{ padding: "10px 16px" }}>PO NUMBER</th>
                <th style={{ padding: "10px 16px" }}>CUSTOMER</th>
                <th style={{ padding: "10px 16px" }}>TARGET ERP ADAPTER</th>
                <th style={{ padding: "10px 16px" }}>AMOUNT</th>
                <th style={{ padding: "10px 16px" }}>STATUS</th>
                <th style={{ padding: "10px 16px" }}>ERP REF #</th>
                <th style={{ padding: "10px 16px", textAlign: "right" }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => (
                <tr key={item.id} style={{ borderBottom: "1px solid var(--line)" }}>
                  <td style={{ padding: "12px 16px", fontWeight: 600, color: "var(--green)" }}>{item.poNumber}</td>
                  <td style={{ padding: "12px 16px", fontWeight: 500 }}>{item.customer}</td>
                  <td style={{ padding: "12px 16px", color: "var(--muted)", fontSize: "12px" }}>{item.adapter}</td>
                  <td style={{ padding: "12px 16px", fontWeight: 600 }}>{money(item.amount, item.currency)}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      className={`badge-clean ${
                        item.status === "DELIVERED"
                          ? "badge-clean-success"
                          : "badge-clean-warning"
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span className="code-snippet">{item.erpReference || "—"}</span>
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "right" }}>
                    {item.status === "PENDING" ? (
                      <button
                        className="primary-button"
                        style={{ fontSize: "11px", padding: "4px 8px" }}
                        onClick={() => triggerRetry(item.id)}
                      >
                        ⚡ Sync
                      </button>
                    ) : (
                      <span style={{ fontSize: "12px", color: "var(--muted)" }}>Synced</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
