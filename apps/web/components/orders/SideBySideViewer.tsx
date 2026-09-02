"use client";

import { useState } from "react";
import type { PurchaseOrder } from "@/app/lib/types";
import { money } from "@/app/lib/derive";
import { api } from "@/app/lib/api/client";
import { XCircle, AlertTriangle, CheckCircle2 } from "lucide-react";

interface SideBySideViewerProps {
  order: PurchaseOrder;
  onClose: () => void;
}

export function SideBySideViewer({ order, onClose }: SideBySideViewerProps) {
  const [activeTab, setActiveTab] = useState<"visual" | "json">("visual");

  const lines = order.lines || [];
  const totalValue = order.value || 0;
  const sourceUrl = api.orders.getSourceUrl(order.id);
  const sourceFile = order.sourceFile || "";
  const ext = sourceFile.slice(sourceFile.lastIndexOf(".")).toLowerCase();

  const isPdf = ext === ".pdf";
  const isImage = [".png", ".jpg", ".jpeg", ".webp"].includes(ext);

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal" style={{ maxWidth: "1200px", width: "95vw" }}>
        <div className="modal-header">
          <div>
            <p className="eyebrow">ĐỐI CHIẾU DỮ LIỆU GỐC &amp; KẾT QUẢ KIỂM ĐỊNH</p>
            <h2>Kiểm tra trực quan Side-by-Side: {order.id}</h2>
            <p style={{ margin: "4px 0 0", color: "var(--color-outline)", fontSize: "0.875rem" }}>
              So sánh trực quan hai khung hình giữa tài liệu gốc đã tải lên và các dòng hàng chuẩn hóa cùng phát hiện kiểm tra.
            </p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Đóng cửa sổ">
            ✕
          </button>
        </div>

        <div style={{ display: "flex", gap: "var(--space-2)", margin: "var(--space-4) 0", borderBottom: "1px solid var(--color-outline-variant)", paddingBottom: "var(--space-3)" }}>
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

        <div style={{ maxHeight: "70vh", overflowY: "auto", padding: "var(--space-1) 0" }}>
          {activeTab === "visual" ? (
            <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "var(--space-5)" }}>
              {/* Left Pane: Real Source File or Pre */}
              <div className="content-card" style={{ padding: "var(--space-4)", display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)", borderBottom: "1px solid var(--color-outline-variant)", paddingBottom: "var(--space-2)" }}>
                  <strong style={{ fontSize: "0.9rem" }}>Tài liệu gốc ({sourceFile || "Tệp đính kèm"})</strong>
                  <span className="badge" style={{ fontSize: "0.75rem" }}>
                    {ext.toUpperCase().replace(".", "") || "DOCUMENT"}
                  </span>
                </div>

                <div style={{ flex: 1, minHeight: 480, display: "flex", flexDirection: "column", background: "var(--color-surface-container-low)", borderRadius: "var(--radius-md)", overflow: "hidden" }}>
                  {isPdf ? (
                    <iframe
                      src={sourceUrl}
                      title={`Tài liệu PDF ${order.id}`}
                      style={{ width: "100%", height: 500, border: "none" }}
                    />
                  ) : isImage ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={sourceUrl}
                      alt={`Hình ảnh hóa đơn ${order.id}`}
                      style={{ maxWidth: "100%", maxHeight: 500, objectFit: "contain", margin: "auto" }}
                    />
                  ) : (
                    <div
                      style={{
                        fontFamily: "ui-monospace, monospace",
                        fontSize: "0.8rem",
                        lineHeight: 1.6,
                        padding: "var(--space-4)",
                        color: "var(--color-on-surface)",
                        overflowY: "auto",
                      }}
                    >
                      <div style={{ color: "var(--color-primary)", fontWeight: 700 }}>ĐƠN ĐẶT HÀNG (PO): {order.id}</div>
                      <div>Khách hàng: {order.customer}</div>
                      <div>Tiền tệ: {order.currency}</div>
                      <div>Thời gian tiếp nhận: {order.submittedAt}</div>
                      <hr style={{ borderColor: "var(--color-outline-variant)", margin: "12px 0" }} />
                      <div style={{ fontWeight: 700, color: "var(--color-outline)" }}>DÒNG HÀNG TRÍCH XUẤT:</div>
                      {lines.map((item, idx) => (
                        <div key={idx} style={{ padding: "6px 0", borderBottom: "1px dashed var(--color-outline-variant)" }}>
                          <div>
                            #{idx + 1} SKU: <strong>{item.sku}</strong> ({item.product})
                          </div>
                          <div style={{ color: "var(--color-outline)", fontSize: "0.75rem" }}>
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

              {/* Right Pane: Validation Findings & Grounding */}
              <div className="content-card" style={{ padding: "var(--space-4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)", borderBottom: "1px solid var(--color-outline-variant)", paddingBottom: "var(--space-2)" }}>
                  <strong style={{ fontSize: "0.9rem" }}>Kết quả kiểm định &amp; Bằng chứng đối chiếu</strong>
                  <span className={`status-badge status-${order.status.toLowerCase().replace(/ /g, "-")}`}>
                    {order.status}
                  </span>
                </div>

                <div style={{ marginBottom: "var(--space-4)" }}>
                  <div style={{ fontSize: "0.8rem", color: "var(--color-outline)", marginBottom: "8px", fontWeight: 600 }}>
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
                            <p style={{ margin: "2px 0 4px", color: "var(--color-on-surface-variant)" }}>{finding.detail}</p>
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

                <div style={{ borderTop: "1px solid var(--color-outline-variant)", paddingTop: "var(--space-3)" }}>
                  <div style={{ fontSize: "0.8rem", color: "var(--color-outline)", marginBottom: "8px", fontWeight: 600 }}>
                    ĐỐI CHIẾU DANH MỤC SẢN PHẨM:
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
                          <tr key={idx}>
                            <td>
                              <strong>{line.sku}</strong>
                            </td>
                            <td className="tabular-nums" style={{ textAlign: "right" }}>
                              {line.quantity}
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
                background: "var(--color-surface-container-low)",
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
    </div>
  );
}
