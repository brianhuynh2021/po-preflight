import type { ReactNode } from "react";
import Link from "next/link";

export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="marketing-layout" style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--canvas)" }}>
      {/* 0. Top Hotline Banner */}
      <div
        style={{
          background: "linear-gradient(90deg, #064e3b 0%, #1e3a8a 100%)",
          color: "#ffffff",
          padding: "8px 24px",
          fontSize: "0.8125rem",
          fontWeight: 600,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
          borderBottom: "1px solid rgba(255,255,255,0.12)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ background: "#10b981", color: "#fff", padding: "1px 6px", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 800 }}>
            NHẬT MINH TECH
          </span>
          <span>Cổng Kiểm Soát Đơn Hàng B2B Tự Động Hóa Dành Cho Doanh Nghiệp Phân Phối.</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "0.75rem" }}>
          <a href="tel:02873006868" style={{ color: "#fef08a", textDecoration: "none", fontWeight: 700 }}>
            📞 Hotline: (028) 7300 6868
          </a>
          <a href="mailto:contact@popreflight.vn" style={{ color: "#93c5fd", textDecoration: "none", fontWeight: 700 }}>
            ✉️ contact@popreflight.vn
          </a>
        </div>
      </div>

      {/* 1. Header Navigation Bar */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          background: "rgba(255, 255, 255, 0.96)",
          backdropFilter: "blur(12px)",
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
                width: "36px",
                height: "36px",
                background: "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                color: "#fff",
                borderRadius: "8px",
                display: "grid",
                placeItems: "center",
                fontWeight: 900,
                fontSize: "1.1rem",
                boxShadow: "0 4px 12px rgba(16,185,129,0.3)",
              }}
            >
              P
            </span>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "nowrap" }}>
                <span style={{ fontSize: "1.15rem", fontWeight: 800, letterSpacing: "-0.02em", color: "var(--ink)", whiteSpace: "nowrap" }}>
                  PO Preflight
                </span>
                <span className="badge-clean badge-clean-success" style={{ fontSize: "0.7rem", padding: "1px 6px", whiteSpace: "nowrap" }}>
                  Nhật Minh Tech
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 500 }}>
                Cổng Tiền Phê Duyệt Đơn Hàng B2B
              </div>
            </div>
          </Link>
        </div>

        <nav className="marketing-nav-links" style={{ display: "flex", alignItems: "center", gap: "24px", fontSize: "0.875rem", fontWeight: 600 }}>
          <Link href="/" style={{ color: "var(--ink)", textDecoration: "none" }}>
            Trang Chủ
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
            style={{ fontSize: "0.875rem", padding: "8px 16px", textDecoration: "none", fontWeight: 700 }}
          >
            Vào Ứng Dụng (App) →
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>{children}</main>

      {/* Footer */}
      <footer id="contact" style={{ borderTop: "2px solid var(--line)", background: "#0b1320", color: "#cbd5e1", padding: "48px 32px 24px", fontSize: "0.875rem" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "32px", marginBottom: "32px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ width: "28px", height: "28px", background: "#10b981", color: "#fff", borderRadius: "6px", display: "grid", placeItems: "center", fontWeight: 900 }}>
                  N
                </span>
                <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#fff" }}>Công Ty Công Nghệ Nhật Minh</span>
              </div>
              <p style={{ fontSize: "0.8125rem", lineHeight: 1.7, color: "#94a3b8", margin: "0 0 16px" }}>
                Đơn vị phát triển nền tảng <strong>PO Preflight</strong> — Cổng Tiền Phê Duyệt &amp; Kiểm Soát Đơn Hàng B2B Tự Động Hóa Hàng Đầu Cho Doanh Nghiệp Phân Phối.
              </p>
              <div style={{ fontSize: "0.8125rem", lineHeight: 1.8, color: "#cbd5e1" }}>
                <div>🌐 <strong>Tên miền chính thức:</strong> popreflight.vn</div>
                <div>📍 <strong>Hỗ trợ kỹ thuật:</strong> Toàn quốc (Remote &amp; On-site)</div>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: "0.875rem", fontWeight: 800, color: "#fff", textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.05em" }}>
                THÔNG TIN LIÊN HỆ
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "0.8125rem" }}>
                <li>
                  📞 <strong>Hotline:</strong>{" "}
                  <a href="tel:02873006868" style={{ color: "#fef08a", textDecoration: "none", fontWeight: 700 }}>
                    (028) 7300 6868
                  </a>
                </li>
                <li>
                  ✉️ <strong>Email:</strong>{" "}
                  <a href="mailto:contact@popreflight.vn" style={{ color: "#67e8f9", textDecoration: "none" }}>
                    contact@popreflight.vn
                  </a>
                </li>
                <li>
                  ✈️ <strong>Telegram:</strong>{" "}
                  <span style={{ color: "#cbd5e1" }}>@popreflight_support_bot</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 style={{ fontSize: "0.875rem", fontWeight: 800, color: "#fff", textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.05em" }}>
                GIẢI PHÁP &amp; ỨNG DỤNG
              </h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 2.2, fontSize: "0.8125rem" }}>
                <li><Link href="/overview" style={{ color: "#94a3b8", textDecoration: "none" }}>Bảng Điều Khiển Tổng Quan</Link></li>
                <li><Link href="/orders" style={{ color: "#94a3b8", textDecoration: "none" }}>Quản Lý Đơn Hàng (Orders)</Link></li>
                <li><Link href="/pricing" style={{ color: "#94a3b8", textDecoration: "none" }}>Bảng Giá &amp; Gói Pilot</Link></li>
                <li><Link href="/security" style={{ color: "#94a3b8", textDecoration: "none" }}>Bảo Mật &amp; Tuân Thủ Pháp Lý</Link></li>
              </ul>
            </div>
          </div>

          <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", fontSize: "0.75rem", color: "#64748b" }}>
            <div>© 2026 Nhật Minh Technology. Bản quyền đã được đăng ký bảo hộ.</div>
            <div>Mã hóa AES-256 • Chuỗi băm SHA-256 bất biến • Tuân thủ Nghị định 13/2023/NĐ-CP</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
