export default function OverviewLoading() {
  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <div className="skeleton" style={{ width: "160px", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "240px", height: "28px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "320px", height: "16px" }} />
        </div>
        <div className="skeleton" style={{ width: "180px", height: "38px", borderRadius: "8px" }} />
      </div>

      <div className="overview-hero skeleton" style={{ minHeight: "140px", opacity: 0.6 }} />

      <div className="overview-columns">
        <section className="content-card">
          <div className="card-heading">
            <div className="skeleton" style={{ width: "140px", height: "20px" }} />
          </div>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="attention-row"
              style={{ borderBottom: "1px solid var(--line)" }}
            >
              <div className="skeleton" style={{ width: "28px", height: "28px", borderRadius: "50%" }} />
              <div>
                <div className="skeleton" style={{ width: "180px", height: "16px", marginBottom: "6px" }} />
                <div className="skeleton" style={{ width: "120px", height: "12px" }} />
              </div>
              <div className="skeleton" style={{ width: "80px", height: "18px" }} />
            </div>
          ))}
        </section>

        <section className="content-card">
          <div className="card-heading">
            <div className="skeleton" style={{ width: "120px", height: "20px" }} />
          </div>
          <div className="bar-chart" style={{ opacity: 0.5 }}>
            {[40, 65, 50, 80, 60].map((h, idx) => (
              <div key={idx}>
                <i className="skeleton" style={{ height: `${h}%` }} />
                <small className="skeleton" style={{ width: "24px", height: "10px", margin: "4px auto 0" }} />
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
