"use client";

import { useMemo, useState } from "react";

import { FilterSelect } from "@/components/common/FilterSelect";
import { SearchFilter } from "@/components/common/SearchFilter";
import { money } from "@/app/lib/derive";
import { catalog } from "@/app/lib/seed";

const STATUS_OPTIONS = [
  { label: "All statuses", value: "all" },
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
];

export function CatalogView() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return catalog.filter((item) => {
      if (statusFilter === "active" && !item.active) {
        return false;
      }
      if (statusFilter === "inactive" && item.active) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return `${item.sku} ${item.name}`.toLowerCase().includes(needle);
    });
  }, [query, statusFilter]);

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
          <div className="toolbar-filters">
            <SearchFilter
              value={query}
              onChange={setQuery}
              placeholder="Search SKU or product"
            />
            <FilterSelect
              ariaLabel="Filter by catalog status"
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
            />
          </div>
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
              {rows.map((item) => (
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