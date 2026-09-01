"use client";

import { useMemo, useState } from "react";
import {
  Search,
  Plus,
  Split,
  Check,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  User,
} from "lucide-react";

import type { ActivityEvent, OrderStatus, PurchaseOrder } from "@/app/lib/types";
import { useAppState } from "@/components/app/AppStateProvider";
import { money } from "@/app/lib/derive";
import { StatusBadge } from "@/components/common/StatusBadge";
import { SubmittedAt } from "@/components/common/SubmittedAt";
import { UploadModal } from "@/components/orders/UploadModal";
import { DecisionModal } from "@/components/orders/DecisionModal";
import { SideBySideViewer } from "@/components/orders/SideBySideViewer";
import { useRipple } from "@/app/lib/useRipple";

export function OrdersView() {
  const { orders, setOrders, activity, setActivity } = useAppState();
  const { createRipple } = useRipple();

  const [selectedId, setSelectedId] = useState("PO-10428");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"All" | OrderStatus>("All");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [sideBySideOpen, setSideBySideOpen] = useState(false);
  const [decisionNote, setDecisionNote] = useState("");
  const [toast, setToast] = useState("");

  const filteredOrders = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return orders.filter((order) => {
      const matchesText =
        !normalized ||
        `${order.id} ${order.customer}`.toLowerCase().includes(normalized);
      const matchesFilter = filter === "All" || order.status === filter;
      return matchesText && matchesFilter;
    });
  }, [filter, orders, query]);

  const selected = orders.find((order) => order.id === selectedId) ?? orders[0];
  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  };

  const approveSelected = () => {
    setOrders((current) =>
      current.map((order) =>
        order.id === selected.id ? { ...order, status: "Approved" } : order,
      ),
    );
    setActivity((current) => [
      {
        title: "Order approved",
        detail: decisionNote || "Approved after reviewing validation evidence",
        time: "Just now",
        type: "human",
      } as ActivityEvent,
      ...current,
    ]);
    setDecisionOpen(false);
    setDecisionNote("");
    showToast(`${selected.id} was approved and recorded in the audit log.`);
  };

  const requestChanges = () => {
    setDecisionOpen(false);
    showToast(`A change request was sent to the owner of ${selected.id}.`);
  };

  return (
    <div className="page orders-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ORDER OPERATIONS</p>
          <h1>Purchase orders</h1>
          <p>
            Review extracted orders, resolve findings, and record controlled
            decisions.
          </p>
        </div>
        <button
          className="primary-button interactive"
          onClick={(e) => {
            createRipple(e);
            setUploadOpen(true);
          }}
          style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
        >
          <Plus size={16} strokeWidth={2.2} aria-hidden="true" />
          <span>Upload purchase order</span>
        </button>
      </div>

      <OrdersMetrics orders={orders} attentionCount={attentionCount} />

      <div className="workspace-grid">
        <OrderQueue
          orders={filteredOrders}
          selectedId={selected.id}
          query={query}
          filter={filter}
          onQueryChange={setQuery}
          onFilterChange={setFilter}
          onSelect={setSelectedId}
        />

        <OrderDetail
          order={selected}
          activity={activity}
          onOpenDecision={() => setDecisionOpen(true)}
          onOpenSideBySide={() => setSideBySideOpen(true)}
          onRequestChanges={requestChanges}
        />
      </div>

      {sideBySideOpen ? (
        <SideBySideViewer
          order={selected}
          onClose={() => setSideBySideOpen(false)}
        />
      ) : null}

      {uploadOpen ? (
        <UploadModal
          onClose={() => setUploadOpen(false)}
          onFile={(name) => {
            setUploadOpen(false);
            showToast(`${name} was added to the processing queue.`);
          }}
        />
      ) : null}

      {decisionOpen ? (
        <DecisionModal
          order={selected}
          note={decisionNote}
          onNoteChange={setDecisionNote}
          onClose={() => setDecisionOpen(false)}
          onConfirm={approveSelected}
        />
      ) : null}

      {toast ? (
        <div className="toast" role="status">
          <Check size={16} strokeWidth={2.5} />
          <span>{toast}</span>
        </div>
      ) : null}
    </div>
  );
}

function OrdersMetrics({
  orders,
  attentionCount,
}: {
  orders: PurchaseOrder[];
  attentionCount: number;
}) {
  return (
    <div className="metrics-row">
      <div className="metric">
        <span>Needs attention</span>
        <strong className="tabular-nums">{attentionCount}</strong>
        <small>
          <i className="metric-dot amber" /> Review or correction required
        </small>
      </div>
      <div className="metric">
        <span>Ready for approval</span>
        <strong className="tabular-nums">{orders.filter((o) => o.status === "Ready").length}</strong>
        <small>
          <i className="metric-dot green" /> All validation rules passed
        </small>
      </div>
      <div className="metric">
        <span>Approved today</span>
        <strong className="tabular-nums">{orders.filter((o) => o.status === "Approved").length}</strong>
        <small>
          <i className="metric-dot blue" /> Average decision time 6m
        </small>
      </div>
      <div className="metric metric-chart">
        <span>Orders this week</span>
        <strong className="tabular-nums">42</strong>
        <div className="spark" aria-label="Orders increased during the week">
          <i style={{ height: "28%" }} />
          <i style={{ height: "48%" }} />
          <i style={{ height: "38%" }} />
          <i style={{ height: "70%" }} />
          <i style={{ height: "56%" }} />
          <i style={{ height: "84%" }} />
          <i style={{ height: "66%" }} />
        </div>
      </div>
    </div>
  );
}

function OrderQueue({
  orders,
  selectedId,
  query,
  filter,
  onQueryChange,
  onFilterChange,
  onSelect,
}: {
  orders: PurchaseOrder[];
  selectedId: string;
  query: string;
  filter: "All" | OrderStatus;
  onQueryChange: (value: string) => void;
  onFilterChange: (value: "All" | OrderStatus) => void;
  onSelect: (id: string) => void;
}) {
  const { createRipple } = useRipple();

  return (
    <section className="queue-panel" aria-label="Order queue">
      <div className="panel-toolbar">
        <label className="search">
          <Search size={15} strokeWidth={2} style={{ opacity: 0.6 }} aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search PO or customer"
          />
        </label>
        <select
          value={filter}
          onChange={(event) => onFilterChange(event.target.value as typeof filter)}
          aria-label="Filter orders by status"
        >
          <option>All</option>
          <option>Review required</option>
          <option>Blocked</option>
          <option>Ready</option>
          <option>Approved</option>
        </select>
      </div>
      <div className="queue-header">
        <span>Order</span>
        <span>Status</span>
        <span>Value</span>
      </div>
      <div className="queue-list">
        {orders.map((order) => (
          <button
            key={order.id}
            className={selectedId === order.id ? "order-row selected interactive" : "order-row interactive"}
            onClick={(e) => {
              createRipple(e);
              onSelect(order.id);
            }}
          >
            <span className="order-identity">
              <strong>{order.id}</strong>
              <small>{order.customer}</small>
              <em>
                <SubmittedAt iso={order.submittedAt} />
              </em>
            </span>
            <span>
              <StatusBadge status={order.status} />
              {order.findings.length > 0 ? (
                <small className="finding-count tabular-nums">
                  {order.findings.length}{" "}
                  {order.findings.length === 1 ? "finding" : "findings"}
                </small>
              ) : null}
            </span>
            <span className="order-value">
              <strong className="tabular-nums">{money(order.value, order.currency)}</strong>
              <small>{order.currency}</small>
            </span>
          </button>
        ))}
        {orders.length === 0 ? (
          <div className="empty-state">
            <FileText size={28} strokeWidth={1.5} style={{ opacity: 0.4, marginBottom: "8px" }} />
            <p>No orders match this view.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function OrderDetail({
  order,
  activity,
  onOpenDecision,
  onOpenSideBySide,
  onRequestChanges,
}: {
  order: PurchaseOrder;
  activity: ActivityEvent[];
  onOpenDecision: () => void;
  onOpenSideBySide: () => void;
  onRequestChanges: () => void;
}) {
  const { createRipple } = useRipple();

  return (
    <section className="detail-panel" aria-label={`${order.id} details`}>
      <div className="detail-header">
        <div>
          <div className="detail-title">
            <h2>{order.id}</h2>
            <StatusBadge status={order.status} />
          </div>
          <p>
            {order.customer} · Submitted <SubmittedAt iso={order.submittedAt} />
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              onOpenSideBySide();
            }}
            style={{ fontSize: "12px", padding: "6px 10px", display: "inline-flex", alignItems: "center", gap: "6px" }}
          >
            <Split size={14} strokeWidth={2} />
            <span>Side-by-Side</span>
          </button>
        </div>
      </div>
      <div className="order-summary">
        <div>
          <span>Order value</span>
          <strong className="tabular-nums">{money(order.value, order.currency)}</strong>
        </div>
        <div>
          <span>Line items</span>
          <strong className="tabular-nums">{order.lines.length}</strong>
        </div>
        <div>
          <span>Owner</span>
          <strong>{order.owner}</strong>
        </div>
        <div>
          <span>Source</span>
          <strong className="source-name">{order.sourceFile}</strong>
        </div>
      </div>

      <div className="detail-body">
        <div className="section-title">
          <div>
            <h3>Validation findings</h3>
            <p>Evidence from active company rules</p>
          </div>
          <span className="finding-pill tabular-nums">{order.findings.length}</span>
        </div>
        {order.findings.length ? (
          <div className="findings">
            {order.findings.map((finding) => (
              <article
                className={`finding finding-${finding.severity === "Error" ? "blocked" : "review"}`}
                key={`${finding.code}-${finding.sku ?? ""}`}
              >
                <div className="finding-symbol" aria-hidden="true" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {finding.severity === "Error" ? (
                    <XCircle size={16} strokeWidth={2.2} />
                  ) : (
                    <AlertTriangle size={15} strokeWidth={2.2} />
                  )}
                </div>
                <div>
                  <div className="finding-top">
                    <strong>{finding.title}</strong>
                    <span>{finding.severity}</span>
                  </div>
                  <p>{finding.detail}</p>
                  <code>{finding.evidence}</code>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="clear-state">
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
              <CheckCircle2 size={20} strokeWidth={2.2} />
            </span>
            <div>
              <strong>All validation rules passed</strong>
              <p>
                This order has no pricing, catalog, stock, or duplicate
                findings.
              </p>
            </div>
          </div>
        )}

        <div className="section-title line-title">
          <div>
            <h3>Normalized line items</h3>
            <p>Extracted values compared with company data</p>
          </div>
          <button className="text-button interactive" onClick={createRipple}>
            View source
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>SKU / Product</th>
                <th style={{ textAlign: "right" }}>Qty</th>
                <th style={{ textAlign: "right" }}>Available</th>
                <th style={{ textAlign: "right" }}>Unit price</th>
                <th style={{ textAlign: "right" }}>Catalog</th>
              </tr>
            </thead>
            <tbody>
              {order.lines.map((line) => (
                <tr key={line.sku}>
                  <td>
                    <strong>{line.sku}</strong>
                    <small>{line.product}</small>
                  </td>
                  <td
                    className="tabular-nums"
                    style={{ textAlign: "right" }}
                  >
                    {line.quantity}
                  </td>
                  <td
                    className={`tabular-nums ${line.available < line.quantity ? "cell-warning" : ""}`}
                    style={{ textAlign: "right" }}
                  >
                    {line.available}
                  </td>
                  <td
                    className={`tabular-nums ${line.catalogPrice > 0 && line.unitPrice !== line.catalogPrice ? "cell-warning" : ""}`}
                    style={{ textAlign: "right" }}
                  >
                    ${line.unitPrice.toFixed(2)}
                  </td>
                  <td
                    className="tabular-nums"
                    style={{ textAlign: "right" }}
                  >
                    {line.catalogPrice
                      ? `$${line.catalogPrice.toFixed(2)}`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="section-title timeline-title">
          <div>
            <h3>Activity</h3>
            <p>Complete evidence and decision history</p>
          </div>
        </div>
        <div className="timeline">
          {activity.map((event, index) => (
            <div className="timeline-event" key={`${event.title}-${index}`}>
              <span
                className={`timeline-mark ${event.type}`}
                style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
              >
                {event.type === "human" ? (
                  <User size={13} strokeWidth={2.2} />
                ) : (
                  <Check size={13} strokeWidth={2.5} />
                )}
              </span>
              <div>
                <strong>{event.title}</strong>
                <p>{event.detail}</p>
              </div>
              <time>{event.time}</time>
            </div>
          ))}
        </div>
      </div>

      <div className="decision-bar">
        <button
          className="secondary-button interactive"
          onClick={(e) => {
            createRipple(e);
            onRequestChanges();
          }}
        >
          Request changes
        </button>
        <button
          className="approve-button interactive"
          onClick={(e) => {
            createRipple(e);
            onOpenDecision();
          }}
          disabled={
            order.status === "Blocked" || order.status === "Approved"
          }
        >
          {order.status === "Approved"
            ? "Approved"
            : order.status === "Blocked"
              ? "Resolve block first"
              : "Review and approve"}
        </button>
      </div>
    </section>
  );
}
