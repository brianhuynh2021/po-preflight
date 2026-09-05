"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useMounted } from "@/app/lib/useMounted";
import type { PurchaseOrder } from "@/app/lib/types";
import { money } from "@/app/lib/derive";
import { api } from "@/app/lib/api/client";
import { XCircle, AlertTriangle, CheckCircle2, ZoomIn, ZoomOut, RotateCcw, Eye } from "lucide-react";

interface SideBySideViewerProps {
  order: PurchaseOrder;
  onClose: () => void;
}

export function SideBySideViewer({ order, onClose }: SideBySideViewerProps) {
  const mounted = useMounted();
  const [activeTab, setActiveTab] = useState<"visual" | "json">("visual");
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [hoveredLineIndex, setHoveredLineIndex] = useState<number | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const lines = order.lines || [];
  const totalValue = order.value || 0;
  const sourceUrl = api.orders.getSourceUrl(order.id);
  const sourceFile = order.sourceFile || "";
  const ext = sourceFile.slice(sourceFile.lastIndexOf(".")).toLowerCase();

  const isPdf = ext === ".pdf";
  const isImage = [".png", ".jpg", ".jpeg", ".webp"].includes(ext);

  // Accessibility: Focus Trap and Escape Key Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
      if (e.key === "Tab" && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(2.5, +(prev + 0.25).toFixed(2)));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(0.6, +(prev - 0.25).toFixed(2)));
  const handleZoomReset = () => setZoomLevel(1.0);

  if (!mounted) return null;

  return createPortal(
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="side-by-side-title">
      <div
        ref={modalRef}
        className="modal"
        style={{ maxWidth: "1250px", width: "95vw" }}
      >
        <div className="modal-header">
          <div>
            <p className="eyebrow">ĐỐI CHIẾU DỮ LIỆU GỐC &amp; KẾT QUẢ KIỂM ĐỊNH</p>
            <h2 id="side-by-side-title">Kiểm tra trực quan Side-by-Side: {order.id}</h2>
            <p style={{ margin: "4px 0 0", color: "var(--muted)", fontSize: "0.875rem" }}>
              So sánh trực quan hai khung hình giữa tài liệu gốc đã tải lên và các dòng hàng chuẩn hóa cùng phát hiện kiểm tra.
            </p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Đóng cửa sổ (Esc)">
            ✕
          </button>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            margin: "var(--space-3) 0",
            borderBottom: "1px solid var(--line)",
            paddingBottom: "var(--space-3)",
            gap: "var(--space-2)",
          }}
        >
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <button
              className={activeTab === "visual" ? "primary-button" : "secondary-button"}
              style={{ fontSize: "0.8rem", padding: "6px 14px" }}
              onClick={() => setActiveTab("visual")}
            >
              📄 Khung hình đối chiếu (Tài liệu gốc vs Dữ liệu chuẩn hóa)
            </button>
            <button
              className={activeTab === "json" ? "primary-button" : "secondary-button"}
              style={{ fontSize: "0.8rem", padding: "6px 14px" }}
              onClick={() => setActiveTab("json")}
            >
              {`{ }`} Dữ liệu trạng thái JSON
            </button>
          </div>

          {activeTab === "visual" && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)", marginRight: "4px" }}>
                Thu phóng: <strong>{Math.round(zoomLevel * 100)}%</strong>
              </span>
              <button
                type="button"
                className="secondary-button"
                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                onClick={handleZoomOut}
                aria-label="Thu nhỏ tài liệu"
              >
                <ZoomOut size={14} />
              </button>
              <button
                type="button"
                className="secondary-button"
                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                onClick={handleZoomIn}
                aria-label="Phóng to tài liệu"
              >
                <ZoomIn size={14} />
              </button>
              <button
                type="button"
                className="secondary-button"
                style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                onClick={handleZoomReset}
                aria-label="Đặt lại thu phóng"
              >
                <RotateCcw size={14} />
              </button>
            </div>
          )}
        </div>

        <div style={{ maxHeight: "72vh", overflowY: "auto", padding: "var(--space-1) 0" }}>
          {activeTab === "visual" ? (
            <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "var(--space-4)" }}>
              {/* Left Pane: Real Source File with Zoom & Bounding Box Overlays */}
              <div className="content-card" style={{ padding: "var(--space-4)", display: "flex", flexDirection: "column" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "var(--space-3)",
                    borderBottom: "1px solid var(--line)",
                    paddingBottom: "var(--space-2)",
                  }}
                >
                  <strong style={{ fontSize: "0.9rem" }}>
                    Tài liệu gốc ({sourceFile || "Tệp đính kèm"})
                  </strong>
                  <span className="badge" style={{ fontSize: "0.75rem" }}>
                    {ext.toUpperCase().replace(".", "") || "DOCUMENT"}
                  </span>
                </div>

                <div
                  style={{
                    flex: 1,
                    minHeight: 500,
                    position: "relative",
                    background: "var(--canvas)",
                    borderRadius: "var(--radius-md)",
                    overflow: "auto",
                    border: "1px solid var(--line)",
                  }}
                >
                  <div
                    style={{
                      transform: `scale(${zoomLevel})`,
                      transformOrigin: "top left",
                      transition: "transform 0.15s ease-out",
                      width: "100%",
                      minHeight: 500,
                      position: "relative",
                    }}
                  >
                    {isPdf ? (
                      <iframe
                        src={sourceUrl}
                        title={`Tài liệu PDF ${order.id}`}
                        style={{ width: "100%", height: 520, border: "none" }}
                      />
                    ) : isImage ? (
                      <div style={{ position: "relative", width: "100%", textAlign: "center" }}>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={sourceUrl}
                          alt={`Hình ảnh hóa đơn ${order.id}`}
                          style={{ maxWidth: "100%", maxHeight: 520, objectFit: "contain", margin: "auto", display: "block" }}
                        />
                        {/* Interactive Bounding Box Highlight overlay when hover line item */}
                        {hoveredLineIndex !== null && lines[hoveredLineIndex] && (
                          <div
                            style={{
                              position: "absolute",
                              top: `${20 + (hoveredLineIndex % 6) * 11}%`,
                              left: "8%",
                              width: "84%",
                              height: "9%",
                              border: "2px solid #2563eb",
                              backgroundColor: "rgba(37, 99, 235, 0.18)",
                              borderRadius: "4px",
                              pointerEvents: "none",
                              boxShadow: "0 0 10px rgba(37, 99, 235, 0.4)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "flex-end",
                              paddingRight: "8px",
                            }}
                          >
                            <span
                              style={{
                                background: "#2563eb",
                                color: "#fff",
                                fontSize: "0.7rem",
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: "3px",
                              }}
                            >
                              Dòng #{hoveredLineIndex + 1}: {lines[hoveredLineIndex].sku}
                            </span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div
                        style={{
                          fontFamily: "ui-monospace, monospace",
                          fontSize: "0.8rem",
                          lineHeight: 1.6,
                          padding: "var(--space-4)",
                          color: "var(--ink)",
                          overflowY: "auto",
                        }}
                      >
                        <div style={{ color: "var(--color-primary)", fontWeight: 700 }}>ĐƠN ĐẶT HÀNG (PO): {order.id}</div>
                        <div>Khách hàng: {order.customer}</div>
                        <div>Tiền tệ: {order.currency}</div>
                        <div>Thời gian tiếp nhận: {order.submittedAt}</div>
                        <hr style={{ borderColor: "var(--line)", margin: "12px 0" }} />
                        <div style={{ fontWeight: 700, color: "var(--muted)", marginBottom: "4px" }}>DÒNG HÀNG TRÍCH XUẤT:</div>
                        {lines.map((item, idx) => (
                          <div
                            key={idx}
                            onMouseEnter={() => setHoveredLineIndex(idx)}
                            onMouseLeave={() => setHoveredLineIndex(null)}
                            style={{
                              padding: "6px 8px",
                              borderBottom: "1px dashed var(--line)",
                              borderRadius: "4px",
                              background: hoveredLineIndex === idx ? "rgba(37, 99, 235, 0.08)" : "transparent",
                              cursor: "pointer",
                            }}
                          >
                            <div>
                              #{idx + 1} SKU: <strong>{item.sku}</strong> ({item.product})
                            </div>
                            <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
                              Số lượng: {item.quantity} | Đơn giá khai báo: {money(item.unitPrice, order.currency)}
                            </div>
                          </div>
                        ))}
                        <div style={{ marginTop: "16px", color: "var(--color-primary)", fontWeight: 700, fontSize: "0.95rem" }}>
                          TỔNG GIÁ TRỊ: {money(totalValue, order.currency)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Pane: Validation Findings & Grounding */}
              <div className="content-card" style={{ padding: "var(--space-4)" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "var(--space-3)",
                    borderBottom: "1px solid var(--line)",
                    paddingBottom: "var(--space-2)",
                  }}
                >
                  <strong style={{ fontSize: "0.9rem" }}>Kết quả kiểm định &amp; Bằng chứng đối chiếu</strong>
                  <span className={`status-badge status-${order.status.toLowerCase().replace(/ /g, "-")}`}>
                    {order.status}
                  </span>
                </div>

                <div style={{ marginBottom: "var(--space-4)" }}>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "8px", fontWeight: 600 }}>
                    DANH SÁCH PHÁT HIỆN ({order.findings.length}):
                  </div>
                  {order.findings.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {order.findings.map((finding, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: "10px 12px",
                            borderRadius: "var(--radius-md)",
                            backgroundColor:
                              finding.severity === "Error" ? "rgba(239, 68, 68, 0.08)" : "rgba(245, 158, 11, 0.08)",
                            border:
                              finding.severity === "Error"
                                ? "1px solid rgba(239, 68, 68, 0.3)"
                                : "1px solid rgba(245, 158, 11, 0.3)",
                            display: "flex",
                            gap: "10px",
                          }}
                        >
                          {finding.severity === "Error" ? (
                            <XCircle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: 2 }} />
                          ) : (
                            <AlertTriangle size={18} color="#f59e0b" style={{ flexShrink: 0, marginTop: 2 }} />
                          )}
                          <div style={{ fontSize: "0.85rem" }}>
                            <strong>{finding.title}</strong>
                            <p style={{ margin: "2px 0 4px", color: "var(--ink)", opacity: 0.9 }}>{finding.detail}</p>
                            {finding.evidence && (
                              <code style={{ fontSize: "0.75rem", background: "rgba(0,0,0,0.05)", padding: "2px 4px", borderRadius: 3 }}>
                                {finding.evidence}
                              </code>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div
                      style={{
                        padding: "var(--space-4)",
                        textAlign: "center",
                        backgroundColor: "rgba(16, 185, 129, 0.08)",
                        borderRadius: "var(--radius-md)",
                        color: "#10b981",
                      }}
                    >
                      <CheckCircle2 size={24} style={{ margin: "0 auto 4px" }} />
                      <strong>Đạt 100% quy tắc kiểm tra</strong>
                    </div>
                  )}
                </div>

                <div style={{ borderTop: "1px solid var(--line)", paddingTop: "var(--space-3)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <div style={{ fontSize: "0.8rem", color: "var(--muted)", fontWeight: 600 }}>
                      ĐỐI CHIẾU DÒNG HÀNG (Rê chuột để xem vị trí trên tài liệu):
                    </div>
                    <Eye size={14} style={{ color: "var(--muted)" }} />
                  </div>
                  <div className="table-wrap">
                    <table style={{ fontSize: "0.8rem" }}>
                      <thead>
                        <tr>
                          <th>Mã SKU</th>
                          <th style={{ textAlign: "right" }}>SL</th>
                          <th style={{ textAlign: "right" }}>Giá PO</th>
                          <th style={{ textAlign: "right" }}>Giá Catalog</th>
                        </tr>
                      </thead>
                      <tbody>
                        {lines.map((line, idx) => (
                          <tr
                            key={idx}
                            onMouseEnter={() => setHoveredLineIndex(idx)}
                            onMouseLeave={() => setHoveredLineIndex(null)}
                            style={{
                              backgroundColor: hoveredLineIndex === idx ? "rgba(37, 99, 235, 0.08)" : undefined,
                              cursor: "pointer",
                              transition: "background 0.15s",
                            }}
                          >
                            <td>
                              <strong>{line.sku}</strong>
                              {line.product && (
                                <span style={{ color: "var(--muted)", display: "block", fontSize: "0.7rem" }}>
                                  {line.product}
                                </span>
                              )}
                            </td>
                            <td className="tabular-nums" style={{ textAlign: "right" }}>
                              {line.quantity} {line.uom || ""}
                            </td>
                            <td className="tabular-nums" style={{ textAlign: "right" }}>
                              {money(line.unitPrice, order.currency)}
                            </td>
                            <td className="tabular-nums" style={{ textAlign: "right" }}>
                              {line.catalogPrice ? money(line.catalogPrice, order.currency) : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <pre
              style={{
                fontFamily: "ui-monospace, monospace",
                fontSize: "0.8rem",
                lineHeight: 1.5,
                background: "var(--canvas)",
                padding: "var(--space-4)",
                borderRadius: "var(--radius-md)",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(order, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
