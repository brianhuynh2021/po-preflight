import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "PO Preflight — Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #090d16 0%, #0f172a 50%, #1e1b4b 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "space-between",
          padding: "80px",
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#ffffff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "12px",
              background: "#4f46e5",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              fontWeight: 800,
            }}
          >
            ✈
          </div>
          <div style={{ fontSize: "28px", fontWeight: 800, letterSpacing: "-0.02em" }}>
            PO Preflight
          </div>
          <div
            style={{
              marginLeft: "12px",
              padding: "4px 12px",
              borderRadius: "20px",
              background: "rgba(79, 70, 229, 0.2)",
              border: "1px solid rgba(129, 140, 248, 0.3)",
              fontSize: "14px",
              color: "#a5b4fc",
            }}
          >
            Nhật Minh Technology
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px", maxWidth: "900px" }}>
          <div
            style={{
              fontSize: "48px",
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: "-0.03em",
              background: "linear-gradient(to right, #ffffff, #e2e8f0, #94a3b8)",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa
          </div>
          <div style={{ fontSize: "22px", color: "#94a3b8", lineHeight: 1.4 }}>
            Zero-Hallucination OCR • 4-Tier Hybrid RAG SKU Matcher • Phê duyệt 1 chạm Telegram/Zalo • Đồng bộ SAP & Odoo ERP
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            width: "100%",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
            paddingTop: "24px",
            fontSize: "16px",
            color: "#64748b",
          }}
        >
          <div>📞 Hotline: 0984 883 750 • ✉ huynh2102@gmail.com</div>
          <div>📍 Khu phố 5, P. Tân Khai, Đồng Nai</div>
        </div>
      </div>
    ),
    {
      ...size,
    }
  );
}
