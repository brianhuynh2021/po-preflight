export default function AuditLogLoading() {
  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <div className="skeleton" style={{ width: "120px", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "160px", height: "28px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "380px", height: "16px" }} />
        </div>
        <div className="skeleton" style={{ width: "130px", height: "38px", borderRadius: "8px" }} />
      </div>

      <section className="content-card audit-card">
        <div className="panel-toolbar">
          <div className="skeleton" style={{ width: "280px", height: "36px", borderRadius: "8px" }} />
          <div className="skeleton" style={{ width: "160px", height: "36px", borderRadius: "8px" }} />
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="audit-row" style={{ borderBottom: "1px solid var(--line)" }}>
            <div className="skeleton" style={{ width: "70px", height: "14px" }} />
            <div className="skeleton" style={{ width: "10px", height: "10px", borderRadius: "50%" }} />
            <div>
              <div className="skeleton" style={{ width: "160px", height: "16px", marginBottom: "6px" }} />
              <div className="skeleton" style={{ width: "220px", height: "12px" }} />
            </div>
            <div className="skeleton" style={{ width: "100px", height: "14px" }} />
            <div className="skeleton" style={{ width: "80px", height: "16px" }} />
          </div>
        ))}
      </section>
    </div>
  );
}
