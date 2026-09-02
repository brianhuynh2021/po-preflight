"use client";

import React from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

export function PricingView() {
  const { createRipple } = useRipple();

  return (
    <div className="pricing-page" style={{ maxWidth: "1200px", margin: "0 auto", padding: "var(--space-8) var(--space-4)" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
        <span
          className="badge-clean badge-clean-success"
          style={{ padding: "4px 12px", fontSize: "var(--text-xs)", fontWeight: 700, marginBottom: "var(--space-2)", display: "inline-block" }}
        >
          BẢNG GIÁ &amp; GÓI DỊCH VỤ LINH HOẠT
        </span>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--ink)", margin: "8px 0 16px", letterSpacing: "-0.02em" }}>
          Đầu tư hiệu quả cho hệ thống kiểm soát đơn hàng B2B
        </h1>
        <p style={{ fontSize: "var(--text-base)", color: "var(--muted)", maxWidth: "700px", margin: "0 auto" }}>
          Lựa chọn gói triển khai phù hợp với quy mô doanh nghiệp phân phối. Khởi đầu với chương trình Pilot trải nghiệm 30 ngày hoàn toàn miễn phí.
        </p>
      </div>

      {/* Pricing Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "var(--space-6)",
          marginBottom: "var(--space-10)",
        }}
      >
        {/* Tier 1: Pilot 30 Days Free */}
        <div
          className="content-card"
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            border: "1px solid var(--color-outline-variant)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            background: "var(--surface)",
            position: "relative",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Gói Pilot Trải Nghiệm</h3>
              <span className="badge-clean badge-clean-neutral">30 ngày miễn phí</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Dành cho doanh nghiệp muốn đánh giá độ chính xác và khả năng tương thích trước khi ký hợp đồng chính thức.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--color-primary)" }}>0 đ</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ 30 ngày thử nghiệm</span>
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Kiểm tra tối đa 100 đơn hàng thật</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Bóc tách PDF / Ảnh chụp hóa đơn</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Khớp mã SKU 4 tầng (Chính xác &amp; Từ lóng)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Duyệt đơn 1 chạm qua Telegram Bot</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Hỗ trợ kỹ thuật trực tiếp 1-1</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#contact"
            className="secondary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Đăng ký Pilot 30 Ngày
          </Link>
        </div>

        {/* Tier 2: Volume-based Standard */}
        <div
          className="content-card"
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            border: "2px solid var(--color-primary)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            background: "var(--surface)",
            position: "relative",
            boxShadow: "0 12px 30px rgba(16,185,129,0.12)",
          }}
        >
          <div style={{ position: "absolute", top: "-12px", right: "24px" }}>
            <span style={{ background: "var(--color-primary)", color: "#fff", padding: "3px 10px", borderRadius: "var(--radius-sm)", fontSize: "0.75rem", fontWeight: 800 }}>
              PHỔ BIẾN NHẤT
            </span>
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Gói Theo Số Lượng Đơn</h3>
              <span className="badge-clean badge-clean-success">SaaS Cloud</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Tối ưu chi phí theo hạn mức đơn thực tế hàng tháng, không giới hạn người dùng và tài khoản quản lý.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ink)" }}>Liên hệ</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ Báo giá theo hạn mức</span>
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Toàn bộ tính năng kiểm tra tự động</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Không giới hạn số lượng tài khoản phân quyền</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Đồng bộ 2 chiều qua Transactional Outbox (MISA, Bravo, Fast, Odoo)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Nhật ký bất biến có chuỗi băm SHA-256 xuất đối soát</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Cam kết dịch vụ SLA 99.9%</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#contact"
            className="primary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Nhận Báo Giá Chi Tiết
          </Link>
        </div>

        {/* Tier 3: Enterprise & On-Premise */}
        <div
          className="content-card"
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            border: "1px solid var(--color-outline-variant)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            background: "var(--surface)",
            position: "relative",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Gói Doanh Nghiệp On-Premise</h3>
              <span className="badge-clean badge-clean-neutral">Private Server</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Cài đặt trực tiếp trên hạ tầng máy chủ nội bộ hoặc Private Cloud của doanh nghiệp, cách ly dữ liệu 100%.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2rem", fontWeight: 800, color: "var(--ink)" }}>Tùy Chỉnh</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ Hợp đồng triển khai</span>
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Toàn bộ dữ liệu nằm trong máy chủ của khách hàng</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tuân thủ 100% Nghị định 13/2023/NĐ-CP về dữ liệu</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tùy biến bộ quy tắc nghiệp vụ theo yêu cầu riêng</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tích hợp sâu ERP (SAP S/4HANA, Oracle NetSuite, Bravo)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Đội ngũ kỹ thuật hỗ trợ On-site chuyên trách</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#contact"
            className="secondary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Tư Vấn Gói Doanh Nghiệp
          </Link>
        </div>
      </div>

      {/* FAQ Section */}
      <div style={{ borderTop: "1px solid var(--line)", paddingTop: "var(--space-8)" }}>
        <h2 style={{ textAlign: "center", fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-6)" }}>
          Câu hỏi thường gặp về chương trình Pilot &amp; Triển khai
        </h2>

        <div style={{ maxWidth: "800px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Chương trình Pilot 30 ngày hoạt động như thế nào?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Chúng tôi sẽ thiết lập môi trường riêng cho doanh nghiệp trong vòng 24 giờ. Đội ngũ kỹ thuật sẽ hỗ trợ nạp danh mục sản phẩm mẫu, thiết lập bot Telegram/Zalo và đồng hành cùng đội ngũ vận hành kiểm thử trên tối đa 100 đơn hàng thực tế mà không thu bất kỳ khoản phí nào.
            </p>
          </div>

          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Hệ thống có cần can thiệp trực tiếp vào mã nguồn ERP hiện tại không?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Không. PO Preflight hoạt động như một lớp kiểm soát độc lập đứng trước ERP. Dữ liệu chỉ được ghi vào ERP qua API tiêu chuẩn hoặc tệp trung gian khi đã có quyết định phê duyệt hợp lệ.
            </p>
          </div>

          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Dữ liệu của chúng tôi được bảo vệ như thế nào?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Dữ liệu đơn hàng và danh mục được mã hóa AES-256 khi lưu trữ và truyền qua TLS 1.3. Với gói Doanh nghiệp On-Premise, hệ thống chạy hoàn toàn trên máy chủ của bạn và không truyền dữ liệu ra ngoài Internet.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
