"use client";

import { money } from "@/app/lib/derive";
import { catalog } from "@/data/catalog";

export function CatalogView() {
  return (
    <div className="page simple-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">COMPANY DATA</p>
          <h1>Product catalog</h1>
          <p>The active reference used by order validation rules.</p>
        </div>
        <button className="primary-button">Sync catalog</button>
      </div>
      <section className="content-card table-card">
        <div className="panel-toolbar">
          <label className="search">
            <span>⌕</span>
            <input placeholder="Search SKU or product" />
          </label>
          <span className="sync-state">
            <i /> Synced 4 minutes ago
          </span>
        </div>
        <div className="table-wrap">
          <table className="catalog-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product</th>
                <th>Catalog price</th>
                <th>Available</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {catalog.map((item) => (
                <tr key={item.sku}>
                  <td>
                    <strong>{item.sku}</strong>
                  </td>
                  <td>{item.name}</td>
                  <td>{money(item.unitPrice, "USD")}</td>
                  <td>{item.stock}</td>
                  <td>
                    <span
                      className={
                        item.active
                          ? "catalog-state active"
                          : "catalog-state inactive"
                      }
                    >
                      {item.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
