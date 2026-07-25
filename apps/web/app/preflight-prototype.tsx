"use client";

import { useMemo, useState } from "react";

type OrderStatus = "Ready" | "Review required" | "Blocked" | "Approved";
type Section = "Overview" | "Orders" | "Catalog" | "Rules" | "Audit log";

type Order = {
  id: string;
  customer: string;
  submitted: string;
  source: string;
  value: number;
  currency: string;
  status: OrderStatus;
  findings: number;
  owner: string;
  lines: Array<{
    sku: string;
    product: string;
    quantity: number;
    available: number;
    unitPrice: number;
    catalogPrice: number;
  }>;
  issues: Array<{
    severity: "Review" | "Blocked";
    title: string;
    detail: string;
    evidence: string;
  }>;
};

const seedOrders: Order[] = [
  {
    id: "PO-10428",
    customer: "Northstar Retail",
    submitted: "Today, 10:42 AM",
    source: "northstar-po-10428.pdf",
    value: 18420,
    currency: "USD",
    status: "Review required",
    findings: 2,
    owner: "Maya Chen",
    lines: [
      { sku: "LMP-200", product: "Arc desk lamp", quantity: 60, available: 38, unitPrice: 74, catalogPrice: 72 },
      { sku: "CHR-110", product: "Morrow task chair", quantity: 30, available: 81, unitPrice: 466, catalogPrice: 466 },
    ],
    issues: [
      {
        severity: "Review",
        title: "Unit price differs from catalog",
        detail: "LMP-200 is priced 2.8% above the current catalog price.",
        evidence: "PO: $74.00  ·  Catalog: $72.00  ·  Difference: +$120.00",
      },
      {
        severity: "Review",
        title: "Requested quantity exceeds available stock",
        detail: "The order requests 60 units of LMP-200, but only 38 are available.",
        evidence: "Requested: 60  ·  Available: 38  ·  Shortfall: 22",
      },
    ],
  },
  {
    id: "PO-10431",
    customer: "Bluebird Supply",
    submitted: "Today, 9:18 AM",
    source: "bluebird-order.txt",
    value: 6980,
    currency: "USD",
    status: "Blocked",
    findings: 1,
    owner: "Unassigned",
    lines: [
      { sku: "DSK-404", product: "Unknown product", quantity: 10, available: 0, unitPrice: 698, catalogPrice: 0 },
    ],
    issues: [
      {
        severity: "Blocked",
        title: "SKU does not exist in the catalog",
        detail: "DSK-404 cannot be matched to an active product and must be corrected before approval.",
        evidence: "Received SKU: DSK-404  ·  Catalog matches: 0",
      },
    ],
  },
  {
    id: "PO-10421",
    customer: "Acme Stores",
    submitted: "Yesterday, 4:36 PM",
    source: "acme-po-10421.json",
    value: 12480,
    currency: "USD",
    status: "Ready",
    findings: 0,
    owner: "Daniel Ortiz",
    lines: [
      { sku: "TB-320", product: "Tanner meeting table", quantity: 8, available: 24, unitPrice: 960, catalogPrice: 960 },
      { sku: "CHR-110", product: "Morrow task chair", quantity: 10, available: 81, unitPrice: 480, catalogPrice: 480 },
    ],
    issues: [],
  },
  {
    id: "PO-10417",
    customer: "Atlas Hospitality",
    submitted: "Yesterday, 1:12 PM",
    source: "atlas-10417.csv",
    value: 24860,
    currency: "USD",
    status: "Approved",
    findings: 0,
    owner: "Maya Chen",
    lines: [
      { sku: "CHR-110", product: "Morrow task chair", quantity: 55, available: 81, unitPrice: 452, catalogPrice: 452 },
    ],
    issues: [],
  },
];

const catalog = [
  { sku: "CHR-110", product: "Morrow task chair", price: "$466.00", stock: 81, state: "Active" },
  { sku: "LMP-200", product: "Arc desk lamp", price: "$72.00", stock: 38, state: "Active" },
  { sku: "TB-320", product: "Tanner meeting table", price: "$960.00", stock: 24, state: "Active" },
  { sku: "STG-410", product: "Rowan storage unit", price: "$1,240.00", stock: 0, state: "Inactive" },
];

const rules = [
  { name: "Unknown SKU", description: "Block line items that do not match the company catalog.", severity: "Block", owner: "Operations" },
  { name: "Inactive product", description: "Block products that are not available for new orders.", severity: "Block", owner: "Operations" },
  { name: "Catalog price mismatch", description: "Require review when the received price differs from the active catalog.", severity: "Review", owner: "Sales" },
  { name: "Insufficient stock", description: "Require review when requested quantity exceeds available inventory.", severity: "Review", owner: "Operations" },
  { name: "Duplicate PO number", description: "Block a PO number already recorded for the same customer.", severity: "Block", owner: "Finance" },
];

const money = (value: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);

function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status status-${status.toLowerCase().replaceAll(" ", "-")}`}>{status}</span>;
}

export default function PreflightPrototype() {
  const [section, setSection] = useState<Section>("Orders");
  const [orders, setOrders] = useState(seedOrders);
  const [selectedId, setSelectedId] = useState("PO-10428");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"All" | OrderStatus>("All");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [decisionOpen, setDecisionOpen] = useState(false);
  const [decisionNote, setDecisionNote] = useState("");
  const [toast, setToast] = useState("");
  const [activity, setActivity] = useState([
    { title: "Validation completed", detail: "2 findings generated by catalog and inventory rules", time: "10:43 AM", type: "system" },
    { title: "Order extracted", detail: "12 fields and 2 line items recognized", time: "10:42 AM", type: "system" },
    { title: "Order submitted", detail: "Uploaded by Olivia Park through the web portal", time: "10:42 AM", type: "human" },
  ]);

  const filteredOrders = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return orders.filter((order) => {
      const matchesText = !normalized || `${order.id} ${order.customer}`.toLowerCase().includes(normalized);
      const matchesFilter = filter === "All" || order.status === filter;
      return matchesText && matchesFilter;
    });
  }, [filter, orders, query]);

  const selected = orders.find((order) => order.id === selectedId) ?? orders[0];
  const attentionCount = orders.filter((order) => order.status === "Review required" || order.status === "Blocked").length;

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  };

  const approveSelected = () => {
    setOrders((current) => current.map((order) => order.id === selected.id ? { ...order, status: "Approved" } : order));
    setActivity((current) => [{ title: "Order approved", detail: decisionNote || "Approved after reviewing validation evidence", time: "Just now", type: "human" }, ...current]);
    setDecisionOpen(false);
    setDecisionNote("");
    showToast(`${selected.id} was approved and recorded in the audit log.`);
  };

  const requestChanges = () => {
    setDecisionOpen(false);
    showToast(`A change request was sent to the owner of ${selected.id}.`);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>Preflight</span>
        </div>
        <div className="workspace-switcher">
          <span className="workspace-avatar">N</span>
          <span><strong>Northwind Co.</strong><small>Operations workspace</small></span>
          <span aria-hidden="true">⌄</span>
        </div>
        <nav aria-label="Primary navigation">
          {(["Overview", "Orders", "Catalog", "Rules", "Audit log"] as Section[]).map((item) => (
            <button key={item} className={section === item ? "nav-item active" : "nav-item"} onClick={() => setSection(item)}>
              <span className="nav-icon" aria-hidden="true">{item === "Overview" ? "⌂" : item === "Orders" ? "▤" : item === "Catalog" ? "□" : item === "Rules" ? "✓" : "◷"}</span>
              {item}
              {item === "Orders" && attentionCount > 0 ? <span className="nav-count">{attentionCount}</span> : null}
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="processing-card">
          <span className="live-dot" />
          <div><strong>Processing is healthy</strong><small>Last checked just now</small></div>
        </div>
        <button className="profile">
          <span className="profile-avatar">MC</span>
          <span><strong>Maya Chen</strong><small>Operations manager</small></span>
          <span aria-hidden="true">⋯</span>
        </button>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="mobile-brand"><span className="brand-mark">O</span><strong>Preflight</strong></div>
          <div className="topbar-actions">
            <button className="icon-button" aria-label="Help">?</button>
            <button className="icon-button notification-button" aria-label="Notifications">♢<span /></button>
          </div>
        </header>

        {section === "Orders" ? (
          <div className="page orders-page">
            <div className="page-heading">
              <div><p className="eyebrow">ORDER OPERATIONS</p><h1>Purchase orders</h1><p>Review extracted orders, resolve findings, and record controlled decisions.</p></div>
              <button className="primary-button" onClick={() => setUploadOpen(true)}><span aria-hidden="true">＋</span> Upload purchase order</button>
            </div>

            <div className="metrics-row">
              <div className="metric"><span>Needs attention</span><strong>{attentionCount}</strong><small><i className="metric-dot amber" /> Review or correction required</small></div>
              <div className="metric"><span>Ready for approval</span><strong>{orders.filter((o) => o.status === "Ready").length}</strong><small><i className="metric-dot green" /> All validation rules passed</small></div>
              <div className="metric"><span>Approved today</span><strong>{orders.filter((o) => o.status === "Approved").length}</strong><small><i className="metric-dot blue" /> Average decision time 6m</small></div>
              <div className="metric metric-chart"><span>Orders this week</span><strong>42</strong><div className="spark" aria-label="Orders increased during the week"><i style={{height:"28%"}}/><i style={{height:"48%"}}/><i style={{height:"38%"}}/><i style={{height:"70%"}}/><i style={{height:"56%"}}/><i style={{height:"84%"}}/><i style={{height:"66%"}}/></div></div>
            </div>

            <div className="workspace-grid">
              <section className="queue-panel" aria-label="Order queue">
                <div className="panel-toolbar">
                  <label className="search"><span aria-hidden="true">⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search PO or customer" /></label>
                  <select value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)} aria-label="Filter orders by status">
                    <option>All</option><option>Review required</option><option>Blocked</option><option>Ready</option><option>Approved</option>
                  </select>
                </div>
                <div className="queue-header"><span>Order</span><span>Status</span><span>Value</span></div>
                <div className="queue-list">
                  {filteredOrders.map((order) => (
                    <button key={order.id} className={selected.id === order.id ? "order-row selected" : "order-row"} onClick={() => setSelectedId(order.id)}>
                      <span className="order-identity"><strong>{order.id}</strong><small>{order.customer}</small><em>{order.submitted}</em></span>
                      <span><StatusBadge status={order.status} />{order.findings > 0 ? <small className="finding-count">{order.findings} {order.findings === 1 ? "finding" : "findings"}</small> : null}</span>
                      <span className="order-value"><strong>{money(order.value)}</strong><small>{order.currency}</small></span>
                    </button>
                  ))}
                  {filteredOrders.length === 0 ? <div className="empty-state">No orders match this view.</div> : null}
                </div>
              </section>

              <section className="detail-panel" aria-label={`${selected.id} details`}>
                <div className="detail-header">
                  <div><div className="detail-title"><h2>{selected.id}</h2><StatusBadge status={selected.status} /></div><p>{selected.customer} · Submitted {selected.submitted.toLowerCase()}</p></div>
                  <button className="more-button" aria-label="More order actions">•••</button>
                </div>
                <div className="order-summary">
                  <div><span>Order value</span><strong>{money(selected.value)}</strong></div>
                  <div><span>Line items</span><strong>{selected.lines.length}</strong></div>
                  <div><span>Owner</span><strong>{selected.owner}</strong></div>
                  <div><span>Source</span><strong className="source-name">{selected.source}</strong></div>
                </div>

                <div className="detail-body">
                  <div className="section-title"><div><h3>Validation findings</h3><p>Evidence from active company rules</p></div><span className="finding-pill">{selected.issues.length}</span></div>
                  {selected.issues.length ? (
                    <div className="findings">
                      {selected.issues.map((issue) => (
                        <article className={`finding finding-${issue.severity.toLowerCase()}`} key={issue.title}>
                          <div className="finding-symbol" aria-hidden="true">{issue.severity === "Blocked" ? "×" : "!"}</div>
                          <div><div className="finding-top"><strong>{issue.title}</strong><span>{issue.severity}</span></div><p>{issue.detail}</p><code>{issue.evidence}</code></div>
                        </article>
                      ))}
                    </div>
                  ) : <div className="clear-state"><span>✓</span><div><strong>All validation rules passed</strong><p>This order has no pricing, catalog, stock, or duplicate findings.</p></div></div>}

                  <div className="section-title line-title"><div><h3>Normalized line items</h3><p>Extracted values compared with company data</p></div><button className="text-button">View source</button></div>
                  <div className="table-wrap"><table><thead><tr><th>SKU / Product</th><th>Qty</th><th>Available</th><th>Unit price</th><th>Catalog</th></tr></thead><tbody>{selected.lines.map((line) => <tr key={line.sku}><td><strong>{line.sku}</strong><small>{line.product}</small></td><td>{line.quantity}</td><td className={line.available < line.quantity ? "cell-warning" : ""}>{line.available}</td><td className={line.catalogPrice > 0 && line.unitPrice !== line.catalogPrice ? "cell-warning" : ""}>${line.unitPrice.toFixed(2)}</td><td>{line.catalogPrice ? `$${line.catalogPrice.toFixed(2)}` : "—"}</td></tr>)}</tbody></table></div>

                  <div className="section-title timeline-title"><div><h3>Activity</h3><p>Complete evidence and decision history</p></div></div>
                  <div className="timeline">{activity.map((event, index) => <div className="timeline-event" key={`${event.title}-${index}`}><span className={`timeline-mark ${event.type}`}>{event.type === "human" ? "M" : "✓"}</span><div><strong>{event.title}</strong><p>{event.detail}</p></div><time>{event.time}</time></div>)}</div>
                </div>

                <div className="decision-bar">
                  <button className="secondary-button" onClick={requestChanges}>Request changes</button>
                  <button className="approve-button" onClick={() => setDecisionOpen(true)} disabled={selected.status === "Blocked" || selected.status === "Approved"}>{selected.status === "Approved" ? "Approved" : selected.status === "Blocked" ? "Resolve block first" : "Review and approve"}</button>
                </div>
              </section>
            </div>
          </div>
        ) : null}

        {section === "Overview" ? <Overview orders={orders} onOpenOrders={() => setSection("Orders")} onUpload={() => setUploadOpen(true)} /> : null}
        {section === "Catalog" ? <CatalogView /> : null}
        {section === "Rules" ? <RulesView /> : null}
        {section === "Audit log" ? <AuditView /> : null}
      </main>

      {uploadOpen ? <div className="modal-backdrop" role="presentation" onMouseDown={() => setUploadOpen(false)}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="upload-title" onMouseDown={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setUploadOpen(false)} aria-label="Close">×</button><div className="modal-icon">↑</div><h2 id="upload-title">Upload a purchase order</h2><p>Preflight will extract the order and run company validation rules. You will review the result before any approval.</p><label className="drop-zone"><input type="file" accept=".pdf,.csv,.json,.txt" onChange={(event) => { if (event.target.files?.length) { setUploadOpen(false); showToast(`${event.target.files[0].name} was added to the processing queue.`); } }} /><span className="upload-symbol">＋</span><strong>Drop a file here or choose a file</strong><small>PDF, CSV, JSON, or TXT · Maximum 20 MB</small></label><div className="modal-note"><span>i</span><p><strong>Human review is always required.</strong><br/>Preflight never creates an ERP order automatically in this prototype.</p></div></section></div> : null}

      {decisionOpen ? <div className="modal-backdrop" role="presentation" onMouseDown={() => setDecisionOpen(false)}><section className="modal decision-modal" role="dialog" aria-modal="true" aria-labelledby="decision-title" onMouseDown={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setDecisionOpen(false)} aria-label="Close">×</button><span className="review-label">APPROVAL DECISION</span><h2 id="decision-title">Approve {selected.id}?</h2><p>This decision will be attributed to Maya Chen and added to the permanent audit history.</p>{selected.issues.length ? <div className="decision-warning"><strong>{selected.issues.length} validation findings acknowledged</strong><span>You are approving this order with documented exceptions.</span></div> : null}<label className="note-field"><span>Decision note {selected.issues.length ? "(required)" : "(optional)"}</span><textarea value={decisionNote} onChange={(event) => setDecisionNote(event.target.value)} placeholder="Explain the reason for this decision..." rows={4}/></label><div className="modal-actions"><button className="secondary-button" onClick={() => setDecisionOpen(false)}>Cancel</button><button className="approve-button" disabled={selected.issues.length > 0 && !decisionNote.trim()} onClick={approveSelected}>Confirm approval</button></div></section></div> : null}

      {toast ? <div className="toast" role="status"><span>✓</span>{toast}</div> : null}
    </div>
  );
}

function Overview({ orders, onOpenOrders, onUpload }: { orders: Order[]; onOpenOrders: () => void; onUpload: () => void }) {
  return <div className="page simple-page"><div className="page-heading"><div><p className="eyebrow">GOOD MORNING, MAYA</p><h1>Operations overview</h1><p>Two orders need attention. Everything else is moving normally.</p></div><button className="primary-button" onClick={onUpload}>＋ Upload purchase order</button></div><div className="overview-hero"><div><span className="overview-label">TODAY&apos;S PRIORITY</span><h2>Resolve two order exceptions before the 2:00 PM fulfillment cut-off.</h2><p>One price and inventory review, and one blocked catalog item.</p><button className="light-button" onClick={onOpenOrders}>Review priority orders →</button></div><div className="radial"><strong>86%</strong><span>straight-through<br/>validation</span></div></div><div className="overview-columns"><section className="content-card"><div className="card-heading"><div><h2>Attention queue</h2><p>Prioritized by business impact</p></div><button onClick={onOpenOrders} className="text-button">View all</button></div>{orders.filter((order) => order.status === "Review required" || order.status === "Blocked").map((order) => <button className="attention-row" key={order.id} onClick={onOpenOrders}><span className={`attention-icon ${order.status === "Blocked" ? "red" : "amber"}`}>{order.status === "Blocked" ? "×" : "!"}</span><span><strong>{order.id} · {order.customer}</strong><small>{order.findings} validation {order.findings === 1 ? "finding" : "findings"}</small></span><b>{money(order.value)}</b><span>→</span></button>)}</section><section className="content-card"><div className="card-heading"><div><h2>Weekly flow</h2><p>Processed purchase orders</p></div><span className="positive">+18%</span></div><div className="bar-chart"><div><i style={{height:"42%"}}/><small>Mon</small></div><div><i style={{height:"60%"}}/><small>Tue</small></div><div><i style={{height:"54%"}}/><small>Wed</small></div><div><i style={{height:"78%"}}/><small>Thu</small></div><div><i className="today" style={{height:"66%"}}/><small>Fri</small></div></div></section></div></div>;
}

function CatalogView() {
  return <div className="page simple-page"><div className="page-heading"><div><p className="eyebrow">COMPANY DATA</p><h1>Product catalog</h1><p>The active reference used by order validation rules.</p></div><button className="primary-button">Sync catalog</button></div><section className="content-card table-card"><div className="panel-toolbar"><label className="search"><span>⌕</span><input placeholder="Search SKU or product" /></label><span className="sync-state"><i/> Synced 4 minutes ago</span></div><div className="table-wrap"><table className="catalog-table"><thead><tr><th>SKU</th><th>Product</th><th>Catalog price</th><th>Available</th><th>Status</th></tr></thead><tbody>{catalog.map((item) => <tr key={item.sku}><td><strong>{item.sku}</strong></td><td>{item.product}</td><td>{item.price}</td><td>{item.stock}</td><td><span className={item.state === "Active" ? "catalog-state active" : "catalog-state inactive"}>{item.state}</span></td></tr>)}</tbody></table></div></section></div>;
}

function RulesView() {
  return <div className="page simple-page"><div className="page-heading"><div><p className="eyebrow">POLICY CONTROL</p><h1>Validation rules</h1><p>Deterministic controls applied to every normalized order.</p></div><button className="primary-button">＋ Add rule</button></div><section className="content-card rules-card">{rules.map((rule) => <div className="rule-row" key={rule.name}><span className={`rule-symbol ${rule.severity.toLowerCase()}`}>{rule.severity === "Block" ? "×" : "!"}</span><div><strong>{rule.name}</strong><p>{rule.description}</p></div><span className={`severity severity-${rule.severity.toLowerCase()}`}>{rule.severity}</span><span className="rule-owner">{rule.owner}</span><label className="switch"><input type="checkbox" defaultChecked/><span/></label></div>)}</section></div>;
}

function AuditView() {
  return <div className="page simple-page"><div className="page-heading"><div><p className="eyebrow">GOVERNANCE</p><h1>Audit log</h1><p>Immutable evidence for extraction, validation, and human decisions.</p></div><button className="secondary-button">Export CSV</button></div><section className="content-card audit-card"><div className="panel-toolbar"><label className="search"><span>⌕</span><input placeholder="Search order, person, or event" /></label><select><option>All events</option><option>Human decisions</option><option>System events</option></select></div>{[{time:"10:43 AM",event:"Validation completed",actor:"Preflight Rules",order:"PO-10428",detail:"2 findings generated"},{time:"10:42 AM",event:"Order submitted",actor:"Olivia Park",order:"PO-10428",detail:"Web portal upload"},{time:"9:19 AM",event:"Order blocked",actor:"Preflight Rules",order:"PO-10431",detail:"Unknown SKU DSK-404"},{time:"Yesterday",event:"Order approved",actor:"Maya Chen",order:"PO-10417",detail:"No exceptions"}].map((item) => <div className="audit-row" key={`${item.order}-${item.event}`}><time>{item.time}</time><span className="audit-dot"/><div><strong>{item.event}</strong><small>{item.detail}</small></div><span>{item.actor}</span><b>{item.order}</b></div>)}</section></div>;
}
