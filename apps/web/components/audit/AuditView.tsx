"use client";

export function AuditView() {
  return (
    <div className="page simple-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">GOVERNANCE</p>
          <h1>Audit log</h1>
          <p>
            Immutable evidence for extraction, validation, and human decisions.
          </p>
        </div>
        <button className="secondary-button">Export CSV</button>
      </div>
      <section className="content-card audit-card">
        <div className="panel-toolbar">
          <label className="search">
            <span>⌕</span>
            <input placeholder="Search order, person, or event" />
          </label>
          <select>
            <option>All events</option>
            <option>Human decisions</option>
            <option>System events</option>
          </select>
        </div>
        {[
          {
            time: "10:43 AM",
            event: "Validation completed",
            actor: "Preflight Rules",
            order: "PO-10428",
            detail: "2 findings generated",
          },
          {
            time: "10:42 AM",
            event: "Order submitted",
            actor: "Olivia Park",
            order: "PO-10428",
            detail: "Web portal upload",
          },
          {
            time: "9:19 AM",
            event: "Order blocked",
            actor: "Preflight Rules",
            order: "PO-10431",
            detail: "Unknown SKU DSK-404",
          },
          {
            time: "Yesterday",
            event: "Order approved",
            actor: "Maya Chen",
            order: "PO-10417",
            detail: "No exceptions",
          },
        ].map((item) => (
          <div className="audit-row" key={`${item.order}-${item.event}`}>
            <time>{item.time}</time>
            <span className="audit-dot" />
            <div>
              <strong>{item.event}</strong>
              <small>{item.detail}</small>
            </div>
            <span>{item.actor}</span>
            <b>{item.order}</b>
          </div>
        ))}
      </section>
    </div>
  );
}
