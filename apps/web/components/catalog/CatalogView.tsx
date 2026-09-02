"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Database, FileUp, RefreshCw, X } from "lucide-react";

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
  const [isSyncingERP, setIsSyncingERP] = useState(false);
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
            onHand: it.on_hand != null ? Number(it.on_hand) : Number(it.stock),
            reservedErp: it.reserved_erp != null ? Number(it.reserved_erp) : 0,
            allocatedLocal: it.allocated_local != null ? Number(it.allocated_local) : 0,
            atp: it.atp != null ? Number(it.atp) : Number(it.stock),
            asOf: it.as_of || null,
            isStale: Boolean(it.is_stale),
          })),
        );
      }
    } catch {
      // Keep current state
    } finally {
      setIsSyncing(false);
    }
  }, []);

  const handleSyncERPInventory = async () => {
    setIsSyncingERP(true);
    setFeedback(null);
    try {
      const res = await api.inventory.sync();
      setFeedback({
        type: "success",
        message: `Đã đồng bộ thành công ${res.count} mã tồn kho từ ERP (${res.adapter}).`,
      });
      await syncCatalog();
    } catch (err) {
      setFeedback({
        type: "error",
        message: `Lỗi đồng bộ tồn kho ERP: ${describeError(err)}`,
      });
    } finally {
      setIsSyncingERP(false);
    }
  };

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
          <p className="eyebrow">COMPANY MASTER DATA — Product catalog</p>
          <h1>Danh mục sản phẩm & Tồn kho ATP</h1>
          <p>Bảng giá chuẩn (Catalog price), đơn vị tính quy đổi, tồn kho ERP và hạn mức phân bổ khả dụng (ATP).</p>
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
            disabled={isImporting || isSyncing || isSyncingERP}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <FileUp size={15} strokeWidth={2} className={isImporting ? "animate-spin" : ""} />
            <span>{isImporting ? "Đang xử lý..." : "Nhập CSV"}</span>
          </button>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void handleSyncERPInventory();
            }}
            disabled={isSyncingERP || isSyncing || isImporting}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Database size={15} strokeWidth={2} className={isSyncingERP ? "animate-spin" : ""} />
            <span>{isSyncingERP ? "Đang đồng bộ ERP..." : "Đồng bộ tồn ERP"}</span>
          </button>
          <button
            className="primary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void syncCatalog();
            }}
            disabled={isSyncing || isImporting || isSyncingERP}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <RefreshCw size={15} strokeWidth={2} className={isSyncing ? "animate-spin" : ""} />
            <span>{isSyncing ? "Đang tải..." : "Làm mới"}</span>
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
            <i /> Tồn kho đồng bộ trực tiếp với ERP
          </span>
        </div>
        <div className="table-wrap">
          <table className="catalog-table">
            <thead>
              <tr>
                <th>Mã SKU</th>
                <th>Tên sản phẩm</th>
                <th style={{ textAlign: "right" }}>Giá niêm yết (Catalog price)</th>
                <th style={{ textAlign: "right" }}>Tồn kho ERP</th>
                <th style={{ textAlign: "right" }}>Giữ chỗ / Cục bộ</th>
                <th style={{ textAlign: "right" }}>Khả dụng (ATP)</th>
                <th style={{ textAlign: "center" }}>ĐVT</th>
                <th style={{ textAlign: "center" }}>MOQ / Quy cách</th>
                <th style={{ textAlign: "center" }}>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => {
                const atpVal = item.atp != null ? item.atp : item.stock;
                const onHandVal = item.onHand != null ? item.onHand : item.stock;
                const reservedVal = (item.reservedErp || 0) + (item.allocatedLocal || 0);

                return (
                  <tr key={item.sku}>
                    <td>
                      <strong>{item.sku}</strong>
                    </td>
                    <td>
                      <div>{item.name}</div>
                      {item.asOf && (
                        <div style={{ fontSize: "0.75rem", color: item.isStale ? "#ef4444" : "var(--color-muted-text)" }}>
                          {item.isStale ? "⚠️ Dữ liệu cũ: " : "🕒 Cập nhật: "}{new Date(item.asOf).toLocaleTimeString()}
                        </div>
                      )}
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "right" }}>
                      {money(item.unitPrice, "VND")}
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "right", color: "var(--color-muted-text)" }}>
                      {onHandVal}
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "right", color: reservedVal > 0 ? "#b45309" : "var(--color-muted-text)" }}>
                      {reservedVal > 0 ? `-${reservedVal}` : "0"}
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "right" }}>
                      <strong style={{ color: atpVal <= 5 ? (atpVal === 0 ? "#ef4444" : "#f59e0b") : "#10b981" }}>
                        {atpVal}
                      </strong>
                    </td>
                    <td style={{ textAlign: "center" }}>
                      <span className="badge" style={{ fontSize: "0.8rem", padding: "2px 6px" }}>
                        {item.baseUom || "PCS"}
                      </span>
                    </td>
                    <td className="tabular-nums" style={{ textAlign: "center" }}>
                      {item.moq || 1} / {item.packSize || 1}
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
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}