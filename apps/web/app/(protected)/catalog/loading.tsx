export default function CatalogLoading() {
  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <div className="skeleton" style={{ width: "130px", height: "14px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "200px", height: "28px", marginBottom: "8px" }} />
          <div className="skeleton" style={{ width: "320px", height: "16px" }} />
        </div>
        <div className="skeleton" style={{ width: "140px", height: "38px", borderRadius: "8px" }} />
      </div>

      <section className="content-card table-card">
        <div className="panel-toolbar">
          <div className="toolbar-filters" style={{ width: "100%" }}>
            <div className="skeleton" style={{ width: "260px", height: "36px", borderRadius: "8px" }} />
            <div className="skeleton" style={{ width: "140px", height: "36px", borderRadius: "8px" }} />
          </div>
        </div>
        <div className="table-wrap">
          <table className="catalog-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product</th>
                <th style={{ textAlign: "right" }}>Catalog price</th>
                <th style={{ textAlign: "right" }}>Available</th>
                <th style={{ textAlign: "center" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((i) => (
                <tr key={i}>
                  <td><div className="skeleton" style={{ width: "80px", height: "16px" }} /></td>
                  <td><div className="skeleton" style={{ width: "180px", height: "16px" }} /></td>
                  <td style={{ textAlign: "right" }}><div className="skeleton" style={{ width: "70px", height: "16px", marginLeft: "auto" }} /></td>
                  <td style={{ textAlign: "right" }}><div className="skeleton" style={{ width: "40px", height: "16px", marginLeft: "auto" }} /></td>
                  <td style={{ textAlign: "center" }}><div className="skeleton" style={{ width: "60px", height: "20px", borderRadius: "10px", margin: "0 auto" }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
