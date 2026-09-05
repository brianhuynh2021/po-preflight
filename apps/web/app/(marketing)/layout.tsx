import type { ReactNode } from "react";
import Link from "next/link";

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="marketing-layout" style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--canvas)" }}>
      {/* 0. Top Enterprise Announcement & Hotline Bar */}
      <div
        style={{
          background: "var(--paper)",
          color: "var(--muted)",
          padding: "7px 32px",
          fontSize: "0.8125rem",
          fontWeight: 500,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "10px",
          borderBottom: "1px solid var(--line)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            style={{
              background: "rgba(16, 185, 129, 0.12)",
              color: "var(--color-primary)",
              padding: "2px 8px",
              borderRadius: "9999px",
              fontSize: "0.7rem",
              fontWeight: 800,
              letterSpacing: "0.04em",
              border: "1px solid rgba(16, 185, 129, 0.25)",
            }}
          >
            PILOT 14 NGÀY
          </span>
          <span style={{ color: "var(--ink)", fontWeight: 600 }}>
            Miễn phí 14 ngày dùng thử toàn bộ luồng tiền kiểm đơn hàng B2B &amp; kết nối ERP
          </span>
          <Link
            href="/#pilot"
            style={{
              color: "var(--color-primary)",
              fontWeight: 700,
              textDecoration: "none",
              fontSize: "0.8125rem",
            }}
          >
            Đăng ký ngay →
          </Link>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "20px", fontSize: "0.78125rem" }}>
          <a
            href="tel:02873006868"
            style={{ color: "var(--muted)", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}
          >
            <span>📞</span>
            <span>Hotline: <strong style={{ color: "var(--ink)" }}>(028) 7300 6868</strong></span>
          </a>
          <a
            href="mailto:contact@popreflight.vn"
            style={{ color: "var(--muted)", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}
          >
            <span>✉️</span>
            <span>contact@popreflight.vn</span>
          </a>
        </div>
      </div>

      {/* 1. Header Navigation Bar */}
      <header
        className="marketing-header"
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          borderBottom: "1px solid var(--line)",
          padding: "12px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: "0 2px 10px rgba(0,0,0,0.03)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: "12px", textDecoration: "none", color: "inherit" }}>
            <span
              style={{
                width: "38px",
                height: "38px",
                background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                color: "#fff",
                borderRadius: "10px",
                display: "grid",
                placeItems: "center",
                fontWeight: 900,
                fontSize: "1.2rem",
                boxShadow: "0 4px 12px rgba(16,185,129,0.35)",
              }}
            >
              ✈
            </span>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "nowrap" }}>
                <span style={{ fontSize: "1.15rem", fontWeight: 800, letterSpacing: "-0.025em", color: "var(--ink)", whiteSpace: "nowrap" }}>
                  PO Preflight
                </span>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    padding: "1px 7px",
                    borderRadius: "9999px",
                    background: "rgba(16, 185, 129, 0.1)",
                    color: "var(--color-primary)",
                    fontWeight: 700,
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    whiteSpace: "nowrap",
                  }}
                >
                  B2B Edition
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 500 }}>
                Cổng Tiền Phê Duyệt Đơn Hàng Doanh Nghiệp
              </div>
            </div>
          </Link>
        </div>

        <nav className="marketing-nav-links" style={{ display: "flex", alignItems: "center", gap: "28px", fontSize: "0.875rem", fontWeight: 600 }}>
          <Link href="/" style={{ color: "var(--ink)", textDecoration: "none" }}>
            Trang Chủ
          </Link>
          <Link href="/#demo-video" style={{ color: "var(--muted)", textDecoration: "none" }}>
            Video Demo (60s)
          </Link>
          <Link href="/#features" style={{ color: "var(--muted)", textDecoration: "none" }}>
            Tính Năng
          </Link>
          <Link href="/pricing" style={{ color: "var(--muted)", textDecoration: "none" }}>
            Bảng Giá
          </Link>
          <Link href="/security" style={{ color: "var(--muted)", textDecoration: "none" }}>
            Bảo Mật &amp; Tuân Thủ
          </Link>
          <Link href="/#contact" style={{ color: "var(--muted)", textDecoration: "none" }}>
            Liên Hệ
          </Link>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link
            href="/overview"
            className="primary-button"
            style={{
              fontSize: "0.875rem",
              padding: "9px 18px",
              textDecoration: "none",
              fontWeight: 700,
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              boxShadow: "0 2px 8px rgba(16, 185, 129, 0.3)",
            }}
          >
            Vào Ứng Dụng (App) →
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>{children}</main>

      {/* Modern SaaS Footer */}
      <footer id="contact" style={{ borderTop: "1px solid var(--line)", background: "var(--paper)", color: "var(--muted)", padding: "56px 32px 28px", fontSize: "0.875rem" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "36px", marginBottom: "40px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
                <span
                  style={{
                    width: "32px",
                    height: "32px",
                    background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                    color: "#fff",
                    borderRadius: "8px",
                    display: "grid",
                    placeItems: "center",
                    fontWeight: 900,
                  }}
                >
                  ✈
                </span>
                <span style={{ fontSize: "1.15rem", fontWeight: 800, color: "var(--ink)", letterSpacing: "-0.02em" }}>PO Preflight</span>
              </div>
              <p style={{ fontSize: "0.8125rem", lineHeight: 1.7, color: "var(--muted)", margin: "0 0 16px" }}>
                Nền tảng kiểm định và tiền phê duyệt đơn hàng B2B tự động hóa. Giải phóng Sales Admin, chặn đứng rủi ro sai giá và quá hạn mức nợ trước khi ghi sổ ERP.
              </p>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "4px 10px", borderRadius: "9999px", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.2)", fontSize: "0.75rem", fontWeight: 700, color: "var(--color-primary)" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10b981" }} />
                <span>Hệ thống trực tuyến • SLA 99.9%</span>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: "0.8125rem", fontWeight: 800, color: "var(--ink)", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.06em" }}>
                GIẢI PHÁP NGHIỆP VỤ
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.3, fontSize: "0.8125rem" }}>
                <li><Link href="/#demo-video" style={{ color: "var(--muted)", textDecoration: "none" }}>Xem Video Thực Tế 60s</Link></li>
                <li><Link href="/#sandbox" style={{ color: "var(--muted)", textDecoration: "none" }}>Trải Nghiệm Khớp SKU 4 Tầng</Link></li>
                <li><Link href="/#roi-calculator" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảng Tính Hoàn Vốn (ROI)</Link></li>
                <li><Link href="/#features" style={{ color: "var(--muted)", textDecoration: "none" }}>4 Trụ Cột Công Nghệ</Link></li>
              </ul>
            </div>

            <div>
              <h4 style={{ fontSize: "0.8125rem", fontWeight: 800, color: "var(--ink)", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.06em" }}>
                HỆ THỐNG &amp; VẬN HÀNH
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.3, fontSize: "0.8125rem" }}>
                <li><Link href="/overview" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảng Điều Khiển Vận Hành</Link></li>
                <li><Link href="/orders" style={{ color: "var(--muted)", textDecoration: "none" }}>Hàng Đợi Phê Duyệt PO</Link></li>
                <li><Link href="/pricing" style={{ color: "var(--muted)", textDecoration: "none" }}>Bảng Giá &amp; Gói Dịch Vụ</Link></li>
                <li><Link href="/security" style={{ color: "var(--muted)", textDecoration: "none" }}>An Ninh Dữ Liệu &amp; Nghị Định 13</Link></li>
              </ul>
            </div>

            <div>
              <h4 style={{ fontSize: "0.8125rem", fontWeight: 800, color: "var(--ink)", textTransform: "uppercase", marginBottom: "14px", letterSpacing: "0.06em" }}>
                HỖ TRỢ &amp; LIÊN HỆ
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "0.8125rem" }}>
                <li>
                  📞 <strong>Hotline:</strong>{" "}
                  <a href="tel:02873006868" style={{ color: "var(--ink)", textDecoration: "none", fontWeight: 700 }}>
                    (028) 7300 6868
                  </a>
                </li>
                <li>
                  ✉️ <strong>Email:</strong>{" "}
                  <a href="mailto:contact@popreflight.vn" style={{ color: "var(--color-primary)", textDecoration: "none", fontWeight: 600 }}>
                    contact@popreflight.vn
                  </a>
                </li>
                <li>
                  🏢 <strong>Phát triển bởi:</strong>{" "}
                  <span>Nhật Minh Technology</span>
                </li>
                <li>
                  📍 <strong>Triển khai:</strong>{" "}
                  <span>Toàn quốc (Cloud SaaS hoặc On-Premise)</span>
                </li>
              </ul>
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--line)", paddingTop: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", fontSize: "0.75rem", color: "var(--faint)" }}>
            <div>© 2026 Nhật Minh Technology. Bản quyền giải pháp PO Preflight đã được đăng ký bảo hộ.</div>
            <div>Mã hóa AES-256 • Chuỗi băm SHA-256 bất biến • Tuân thủ Nghị định 13/2023/NĐ-CP</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
