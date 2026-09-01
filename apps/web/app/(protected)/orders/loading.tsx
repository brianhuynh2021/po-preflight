export default function OrdersLoading() {
  return (
    <div className="page orders-page page-enter">
      <div className="page-heading">
        <div>
          <div className="skeleton" style={{ width: "140px", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "200px", height: "28px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "360px", height: "16px" }} />
        </div>
        <div className="skeleton" style={{ width: "180px", height: "38px", borderRadius: "8px" }} />
      </div>

      <div className="metrics-row">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric">
            <div className="skeleton" style={{ width: "100px", height: "14px", marginBottom: "8px" }} />
            <div className="skeleton" style={{ width: "60px", height: "28px", marginBottom: "8px" }} />
            <div className="skeleton" style={{ width: "130px", height: "12px" }} />
          </div>
        ))}
      </div>

      <div className="workspace-grid">
        <section className="queue-panel">
          <div className="panel-toolbar">
            <div className="skeleton" style={{ width: "100%", height: "36px", borderRadius: "8px" }} />
          </div>
          <div className="queue-list">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="order-row"
                style={{ padding: "16px 15px", borderBottom: "1px solid var(--line)" }}
              >
                <div>
                  <div className="skeleton" style={{ width: "90px", height: "16px", marginBottom: "6px" }} />
                  <div className="skeleton" style={{ width: "130px", height: "12px" }} />
                </div>
                <div className="skeleton" style={{ width: "70px", height: "22px", borderRadius: "12px" }} />
                <div className="skeleton" style={{ width: "60px", height: "18px" }} />
              </div>
            ))}
          </div>
        </section>

        <section className="detail-panel">
          <div className="detail-header">
            <div>
              <div className="skeleton" style={{ width: "140px", height: "28px", marginBottom: "8px" }} />
              <div className="skeleton" style={{ width: "200px", height: "14px" }} />
            </div>
            <div className="skeleton" style={{ width: "100px", height: "32px", borderRadius: "6px" }} />
          </div>
          <div className="order-summary skeleton" style={{ minHeight: "68px", margin: "16px 0" }} />
          <div className="detail-body">
            <div className="skeleton" style={{ width: "180px", height: "20px", marginBottom: "16px" }} />
            <div className="skeleton" style={{ width: "100%", height: "140px", borderRadius: "8px", marginBottom: "20px" }} />
            <div className="skeleton" style={{ width: "160px", height: "20px", marginBottom: "16px" }} />
            <div className="skeleton" style={{ width: "100%", height: "160px", borderRadius: "8px" }} />
          </div>
        </section>
      </div>
    </div>
  );
}
