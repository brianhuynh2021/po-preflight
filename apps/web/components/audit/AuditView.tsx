"use client";

import { useEffect, useState, useMemo } from "react";
import { Download, RefreshCw, History, ShieldCheck, User } from "lucide-react";
import { FilterSelect } from "@/components/common/FilterSelect";
import { SearchFilter } from "@/components/common/SearchFilter";
import { useRipple } from "@/app/lib/useRipple";
import { api } from "@/app/lib/api/client";
import { auditEntries } from "@/app/lib/seed";
import type { AuditEvent } from "@/app/lib/api/types";

const TYPE_OPTIONS = [
  { label: "All events", value: "all" },
  { label: "Human decisions", value: "DECISION" },
  { label: "System events", value: "AUDIT_BLOCK" },
];

const initialEvents: AuditEvent[] = auditEntries.map((e) => ({
  id: e.id,
  event_type: e.type === "human" ? "DECISION" : "AUDIT_BLOCK",
  timestamp: e.time,
  po_number: e.order,
  action: e.event,
  actor: e.actor,
  detail: e.detail,
}));

export function AuditView() {
  const [events, setEvents] = useState<AuditEvent[]>(initialEvents);
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const { createRipple } = useRipple();

  const fetchAuditEvents = async () => {
    setIsLoading(true);
    try {
      const data = await api.audit.getEvents({ limit: 100 });
      if (data && data.length > 0) {
        setEvents(data);
      }
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    api.audit
      .getEvents({ limit: 100 })
      .then((data) => {
        if (mounted && data && data.length > 0) {
          setEvents(data);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return events.filter((entry) => {
      if (typeFilter !== "all" && entry.event_type !== typeFilter) {
        return false;
      }
      if (!needle) {
        return true;
      }
      return [entry.po_number, entry.actor, entry.action, entry.detail].some((field) =>
        field.toLowerCase().includes(needle),
      );
    });
  }, [events, query, typeFilter]);

  const handleExportCSV = () => {
    if (events.length === 0) return;
    const headers = ["ID", "Loai_su_kien", "Thoi_gian", "Ma_PO", "Hanh_dong", "Nguoi_thuc_hien", "Chi_tiet", "Hash"];
    const csvContent = [
      headers.join(","),
      ...events.map((e) =>
        [
          `"${e.id}"`,
          `"${e.event_type}"`,
          `"${e.timestamp}"`,
          `"${e.po_number}"`,
          `"${e.action}"`,
          `"${e.actor}"`,
          `"${e.detail.replace(/"/g, '""')}"`,
          `"${e.hash || ""}"`,
        ].join(","),
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `audit_trail_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="page simple-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">QUẢN TRỊ &amp; TUÂN THỦ · Governance</p>
          <h1>Nhật ký kiểm toán hệ thống (Audit log)</h1>
          <p>
            Bằng chứng bất biến ghi nhận mọi chu trình: tiếp nhận đơn hàng, đánh giá quy tắc, quyết định phê duyệt và chuỗi băm mật mã SHA-256.
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              void fetchAuditEvents();
            }}
            disabled={isLoading}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <RefreshCw size={15} className={isLoading ? "animate-spin" : ""} />
            <span>Làm mới</span>
          </button>
          <button
            className="secondary-button interactive"
            onClick={(e) => {
              createRipple(e);
              handleExportCSV();
            }}
            disabled={events.length === 0}
            style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}
          >
            <Download size={15} strokeWidth={2} />
            <span>Xuất CSV</span>
          </button>
        </div>
      </div>

      <section className="content-card audit-card">
        <div className="panel-toolbar">
          <SearchFilter
            value={query}
            onChange={setQuery}
            placeholder="Search order, person, or event"
          />
          <FilterSelect
            ariaLabel="Filter by event type"
            value={typeFilter}
            onChange={(value) => setTypeFilter(value)}
            options={TYPE_OPTIONS}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          {rows.map((item) => (
            <div className="audit-row interactive" key={item.id} style={{ padding: "12px 16px" }}>
              <time className="tabular-nums" style={{ fontSize: "0.8rem", color: "var(--color-outline)", width: 140 }}>
                {item.timestamp ? (item.timestamp.includes("T") ? new Date(item.timestamp).toLocaleString("vi-VN") : item.timestamp) : "Vừa xong"}
              </time>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: item.event_type === "DECISION" ? "rgba(59, 130, 246, 0.1)" : "rgba(16, 185, 129, 0.1)",
                  color: item.event_type === "DECISION" ? "#2563eb" : "#10b981",
                }}
              >
                {item.event_type === "DECISION" ? <User size={14} /> : <ShieldCheck size={14} />}
              </span>
              <div style={{ flex: 1, paddingLeft: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <strong>{item.action}</strong>
                  <span className="badge" style={{ fontSize: "0.7rem", padding: "1px 5px" }}>
                    {item.event_type}
                  </span>
                </div>
                <small style={{ display: "block", color: "var(--color-on-surface-variant)", marginTop: 2 }}>
                  {item.detail}
                </small>
                {item.hash && (
                  <code style={{ fontSize: "0.7rem", color: "var(--color-outline)", background: "var(--color-surface-container)", padding: "1px 4px", borderRadius: 3, display: "inline-block", marginTop: 4 }}>
                    SHA-256: {item.hash}
                  </code>
                )}
              </div>
              <span style={{ fontSize: "0.85rem", color: "var(--color-on-surface)" }}>{item.actor}</span>
              <b className="tabular-nums" style={{ marginLeft: 16, color: "var(--color-primary)" }}>
                {item.po_number}
              </b>
            </div>
          ))}

          {rows.length === 0 && (
            <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--color-outline)" }}>
              <History size={32} style={{ opacity: 0.3, margin: "0 auto var(--space-2)" }} />
              <p>Chưa có sự kiện kiểm toán nào được ghi nhận.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}