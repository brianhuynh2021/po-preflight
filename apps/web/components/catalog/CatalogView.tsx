"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { FilterSelect } from "@/components/common/FilterSelect";
import { SearchFilter } from "@/components/common/SearchFilter";
import { money } from "@/app/lib/derive";
import { catalog as seedCatalog } from "@/app/lib/seed";
import { api } from "@/app/lib/api/client";
import { useRipple } from "@/app/lib/useRipple";

const STATUS_OPTIONS = [
  { label: "All statuses", value: "all" },
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
];

export function CatalogView() {
  const [items, setItems] = useState(seedCatalog);
  const [isSyncing, setIsSyncing] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const { createRipple } = useRipple();

  const syncCatalog = useCallback(async () => {
    setIsSyncing(true);
    try {
      const liveItems = await api.catalog.list();
      if (Array.isArray(liveItems) && liveItems.length > 0) {
        setItems(
          liveItems.map((it) => ({
            sku: it.sku,
            name: it.name,
            unitPrice: Number(it.unit_price),
            stock: Number(it.stock),
            active: Boolean(it.active),
          })),
        );
      }

    } catch {
      // Keep current state
    } finally {
      setIsSyncing(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void syncCatalog();
  }, [syncCatalog]);


  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((item) => {
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
  }, [items, query, statusFilter]);


  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">COMPANY DATA</p>
          <h1>Product catalog</h1>
          <p>The active reference used by order validation rules.</p>
        </div>
        <button
          className="primary-button interactive"
          onClick={(e) => {
            createRipple(e);
            void syncCatalog();
          }}
          disabled={isSyncing}
          style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
        >
          <RefreshCw size={15} strokeWidth={2} className={isSyncing ? "animate-spin" : ""} />
          <span>{isSyncing ? "Đang đồng bộ..." : "Sync catalog"}</span>
        </button>

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
                <th style={{ textAlign: "right" }}>Catalog price</th>
                <th style={{ textAlign: "right" }}>Available</th>
                <th style={{ textAlign: "center" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <tr key={item.sku}>
                  <td>
                    <strong>{item.sku}</strong>
                  </td>
                  <td>{item.name}</td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {money(item.unitPrice, "USD")}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {item.stock}
                  </td>
                  <td style={{ textAlign: "center" }}>
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