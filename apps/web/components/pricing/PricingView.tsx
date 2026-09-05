"use client";

import React from "react";
import Link from "next/link";
import { Check, HelpCircle } from "lucide-react";
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
          Đầu tư thông minh cho hệ thống kiểm soát đơn hàng B2B
        </h1>
        <p style={{ fontSize: "var(--text-base)", color: "var(--muted)", maxWidth: "780px", margin: "0 auto", lineHeight: 1.6 }}>
          Mức giá cụ thể được thiết kế dựa trên kết quả phỏng vấn định giá thực địa với 02 Giám đốc Vận hành tại nhà phân phối Dược phẩm &amp; FMCG. Chi phí chỉ bằng 1/10 chi phí nhân sự nhập liệu và hoàn vốn (ROI) ngay tháng đầu tiên.
        </p>
      </div>

      {/* Pricing Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "var(--space-6)",
          marginBottom: "var(--space-8)",
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
              <span className="badge-clean badge-clean-neutral">14 ngày miễn phí</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Dành cho doanh nghiệp muốn đánh giá độ chính xác bóc tách, bộ luật B2B và khả năng kết nối ERP trước khi ký hợp đồng.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--color-primary)" }}>0 đ</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ 14 ngày thử nghiệm</span>
              </div>
              <div style={{ fontSize: "var(--text-xs)", color: "var(--muted)", marginTop: "4px" }}>
                Bao gồm 100 đơn hàng thực tế &amp; hỗ trợ kỹ thuật Onboarding 1-1
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Kiểm tra tối đa 100 đơn hàng thực tế</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Bóc tách PDF hóa đơn, Excel, ảnh scan (Gemini OCR)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Khớp mã SKU 4 tầng (Exact, Fuzzy, FastEmbed Vector)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Duyệt đơn di động qua Telegram Bot &amp; Zalo OA</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Báo cáo phân tích KPI Pilot &amp; xuất file CSV</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#pilot"
            className="secondary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Đăng Ký Pilot 14 Ngày
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
            <span style={{ background: "linear-gradient(135deg, #059669 0%, #047857 100%)", color: "#ffffff", padding: "4px 12px", borderRadius: "9999px", fontSize: "0.75rem", fontWeight: 800, letterSpacing: "0.04em", boxShadow: "0 2px 8px rgba(5, 150, 105, 0.35)" }}>
              PHỔ BIẾN NHẤT
            </span>
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Gói Theo Số Lượng Đơn</h3>
              <span className="badge-clean badge-clean-success">SaaS Cloud</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Phù hợp cho các nhà phân phối B2B xử lý từ 500 đến 1.500 đơn hàng/tháng, kết nối tự động với phần mềm kế toán.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2.3rem", fontWeight: 800, color: "var(--ink)" }}>4.500.000 đ</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ tháng</span>
              </div>
              <div style={{ fontSize: "var(--text-xs)", color: "var(--muted)", marginTop: "4px" }}>
                Bao gồm 1.500 đơn hàng/tháng (~3.000 đ/đơn). Đơn vượt mức: 2.500 đ/đơn.
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Hạn mức 1.500 POs/tháng (Không giới hạn người dùng)</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Toàn bộ quy tắc luật B2B: Giá hợp đồng, Hạn mức nợ, Tồn ATP</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Kết nối 2 chiều ERP Outbox: MISA AMIS, Bravo, Fast, Odoo</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Email Intake Worker tự động quét hộp thư đơn hàng</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Chuỗi băm SHA-256 chứng thực bất biến &amp; SLA 99.5%</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#pilot"
            className="primary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Đăng Ký Gói Tiêu Chuẩn
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
              <span className="badge-clean badge-clean-neutral">On-Premise / Private</span>
            </div>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", minHeight: "44px" }}>
              Triển khai trực tiếp trên hạ tầng máy chủ nội bộ của doanh nghiệp, tuân thủ 100% Nghị định 13 và cách ly dữ liệu.
            </p>

            <div style={{ margin: "var(--space-4) 0", padding: "var(--space-3) 0", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                <span style={{ fontSize: "2.3rem", fontWeight: 800, color: "var(--ink)" }}>12.500.000 đ</span>
                <span style={{ fontSize: "var(--text-sm)", color: "var(--muted)" }}>/ tháng</span>
              </div>
              <div style={{ fontSize: "var(--text-xs)", color: "var(--muted)", marginTop: "4px" }}>
                Hạn mức 10.000 POs/tháng hoặc gói bàn giao vĩnh viễn (On-Premise License)
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 var(--space-6)", display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--text-sm)" }}>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Toàn bộ dữ liệu nằm 100% trong máy chủ của khách hàng</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tuân thủ tuyệt đối Nghị định 13/2023/NĐ-CP về dữ liệu</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tùy biến bộ quy tắc kinh doanh và ma trận duyệt SoD theo yêu cầu</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Tích hợp sâu SAP S/4HANA, SAP Business One, Bravo, ERP riêng</span>
              </li>
              <li style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Check size={16} color="var(--color-primary)" />
                <span>Đội ngũ kỹ sư hỗ trợ On-site, cam kết SLA 99.9% &amp; NDA bảo mật</span>
              </li>
            </ul>
          </div>

          <Link
            href="/#pilot"
            className="secondary-button interactive"
            onClick={createRipple}
            style={{ width: "100%", justifyContent: "center", padding: "12px", textDecoration: "none", fontWeight: 700 }}
          >
            Tư Vấn Gói Doanh Nghiệp
          </Link>
        </div>
      </div>

      {/* Pricing Interview Assumption Footnote */}
      <div
        className="content-card"
        style={{
          background: "var(--surface-container-low, #f8fafc)",
          border: "1px dashed var(--color-outline-variant)",
          borderRadius: "var(--radius-md)",
          padding: "var(--space-4) var(--space-6)",
          marginBottom: "var(--space-8)",
          display: "flex",
          gap: "var(--space-3)",
          alignItems: "flex-start",
        }}
      >
        <HelpCircle size={20} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: "2px" }} />
        <div style={{ fontSize: "var(--text-xs)", color: "var(--muted)", lineHeight: 1.6 }}>
          <strong>Căn cứ xác lập đơn giá &amp; Giả định phỏng vấn thương mại:</strong> Mức phí trên được hiệu chỉnh sau 02 cuộc phỏng vấn sâu với Giám đốc Vận hành tại Nhà phân phối Dược phẩm (Hà Nội, quy mô 1.200 PO/tháng) và Nhà phân phối FMCG (TP.HCM, quy mô 3.500 PO/tháng). Với mức lương trung bình của Sales Admin là 9 - 12 triệu VNĐ/tháng và năng suất xử lý thủ công đạt 25 - 35 PO/ngày, PO Preflight giúp giảm tối thiểu 2 nhân sự nhập liệu rà soát, mang lại tỷ suất ROI vượt 350% ngay từ tháng vận hành đầu tiên.
        </div>
      </div>

      {/* FAQ Section */}
      <div style={{ borderTop: "1px solid var(--line)", paddingTop: "var(--space-8)" }}>
        <h2 style={{ textAlign: "center", fontSize: "1.75rem", fontWeight: 800, marginBottom: "var(--space-6)" }}>
          Câu hỏi thường gặp về chi phí &amp; phương thức thanh toán
        </h2>

        <div style={{ maxWidth: "800px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Chương trình Pilot 14 ngày có phát sinh chi phí ẩn nào không?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Hoàn toàn không. Chúng tôi cung cấp miễn phí môi trường trải nghiệm trong 14 ngày cho tối đa 100 đơn hàng thực tế của doanh nghiệp. Đội ngũ kỹ sư sẽ hỗ trợ nạp dữ liệu Master SKU, cấu hình bot Telegram/Zalo và đồng hành hướng dẫn Sales Admin mà không yêu cầu thẻ tín dụng hay bất kỳ cam kết trả phí nào trước.
            </p>
          </div>

          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Nếu doanh nghiệp vượt quá hạn mức đơn hàng trong tháng thì sao?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Hệ thống không bao giờ gián đoạn hoạt động của bạn. Khi vượt hạn mức, các đơn tiếp theo được tính phí phát sinh ưu đãi là 2.500 đ/đơn đối với gói Tiêu Chuẩn. Báo cáo đối soát chi tiết sẽ được gửi vào cuối kỳ thanh toán.
            </p>
          </div>

          <div className="content-card">
            <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: "0 0 6px", color: "var(--ink)" }}>
              Doanh nghiệp có nhận được hóa đơn giá trị gia tăng (VAT) không?
            </h4>
            <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
              Có. Toàn bộ các gói dịch vụ được xuất hóa đơn điện tử hợp pháp từ Nhật Minh Technology theo đúng quy định pháp luật Việt Nam. Hợp đồng dịch vụ ghi rõ cam kết bảo mật thông tin (NDA) và thỏa thuận mức độ dịch vụ (SLA).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
