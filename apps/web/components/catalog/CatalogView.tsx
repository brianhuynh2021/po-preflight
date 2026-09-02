"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileUp, RefreshCw, X } from "lucide-react";

import { FilterSelect } from "@/components/common/FilterSelect";
import { SearchFilter } from "@/components/common/SearchFilter";
import { money } from "@/app/lib/derive";
import { catalog as seedCatalog } from "@/app/lib/seed";
import { ApiError, api, describeError } from "@/app/lib/api/client";
import { useRipple } from "@/app/lib/useRipple";
import type { Product } from "@/app/lib/types";

const STATUS_OPTIONS = [
  { label: "All statuses", value: "all" },
  { label: "Active", value: "active" },
  { label: "Inactive", value: "inactive" },
];

export function CatalogView() {
  const [items, setItems] = useState<Product[]>(seedCatalog);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string; errors?: Array<{ row?: number; column?: string; message?: string }> } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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
            baseUom: it.base_uom || "PCS",
            moq: it.moq || 1,
            packSize: it.pack_size || 1,
            category: it.category || null,
            barcode: it.barcode || null,
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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setFeedback(null);
    try {
      const res = await api.catalog.importCSV(file);
      setFeedback({
        type: "success",
        message: res.message || `Đã nhập thành công ${res.total_skus} sản phẩm.`,
      });
      await syncCatalog();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.data && typeof err.data === "object" && "errors" in err.data) {
        const prob = err.data as { detail?: string; errors?: Array<{ row?: number; column?: string; message?: string }> };
        setFeedback({
          type: "error",
          message: prob.detail || "Tệp CSV chứa dữ liệu không hợp lệ",
          errors: prob.errors,
        });
      } else {
        setFeedback({
          type: "error",
          message: describeError(err),
        });
      }
    } finally {
      setIsImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

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
      return `${item.sku} ${item.name} ${item.category || ""}`.toLowerCase().includes(needle);
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
        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              fileInputRef.current?.click();
            }}
            disabled={isImporting || isSyncing}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <FileUp size={15} strokeWidth={2} className={isImporting ? "animate-spin" : ""} />
            <span>{isImporting ? "Đang xử lý..." : "Nhập catalog CSV"}</span>
          </button>
          <button
            className="primary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void syncCatalog();
            }}
            disabled={isSyncing || isImporting}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <RefreshCw size={15} strokeWidth={2} className={isSyncing ? "animate-spin" : ""} />
            <span>{isSyncing ? "Đang đồng bộ..." : "Sync catalog"}</span>
          </button>
        </div>
      </div>

      {feedback && (
        <div
          style={{
            margin: "0 0 var(--space-4) 0",
            padding: "var(--space-3) var(--space-4)",
            borderRadius: "var(--radius-md)",
            border: feedback.type === "success" ? "1px solid #10b981" : "1px solid #ef4444",
            backgroundColor: feedback.type === "success" ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              {feedback.type === "success" ? (
                <CheckCircle2 size={18} color="#10b981" />
              ) : (
                <AlertCircle size={18} color="#ef4444" />
              )}
              <strong style={{ color: feedback.type === "success" ? "#10b981" : "#ef4444" }}>
                {feedback.message}
              </strong>
            </div>
            <button
              onClick={() => setFeedback(null)}
              style={{ background: "transparent", border: "none", cursor: "pointer", padding: 4 }}
            >
              <X size={16} />
            </button>
          </div>
          {feedback.errors && feedback.errors.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: "var(--space-5)", fontSize: "0.875rem", color: "#dc2626" }}>
              {feedback.errors.map((err, idx) => (
                <li key={idx}>
                  {err.row ? `Dòng ${err.row}: ` : ""}{err.column ? `Cột '${err.column}' — ` : ""}{err.message}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

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
                <th style={{ textAlign: "center" }}>ĐVT (UOM)</th>
                <th style={{ textAlign: "center" }}>MOQ</th>
                <th style={{ textAlign: "center" }}>Pack size</th>
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
                    {money(item.unitPrice, "VND")}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "right" }}>
                    {item.stock}
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <span className="badge" style={{ fontSize: "0.8rem", padding: "2px 6px" }}>
                      {item.baseUom || "PCS"}
                    </span>
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "center" }}>
                    {item.moq || 1}
                  </td>
                  <td className="tabular-nums" style={{ textAlign: "center" }}>
                    {item.packSize || 1}
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