"use client";

import React from "react";
import Link from "next/link";
import { Lock, Database, Key, FileCode, Server, Trash2 } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

export function SecurityView() {
  const { createRipple } = useRipple();

  return (
    <div className="security-page" style={{ maxWidth: "1100px", margin: "0 auto", padding: "var(--space-8) var(--space-4)" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
        <span
          className="badge-clean badge-clean-success"
          style={{ padding: "4px 12px", fontSize: "var(--text-xs)", fontWeight: 700, marginBottom: "var(--space-2)", display: "inline-block" }}
        >
          AN NINH DỮ LIỆU &amp; TUÂN THỦ PHÁP LÝ
        </span>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 800, color: "var(--ink)", margin: "8px 0 16px", letterSpacing: "-0.02em" }}>
          Cam kết bảo vệ dữ liệu thương mại của doanh nghiệp
        </h1>
        <p style={{ fontSize: "var(--text-base)", color: "var(--muted)", maxWidth: "720px", margin: "0 auto" }}>
          Chúng tôi hiểu rằng bảng giá, danh mục khách hàng và số liệu đơn hàng là tài sản chiến lược quan trọng nhất của doanh nghiệp phân phối.
        </p>
      </div>

      {/* Security Pillars */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "var(--space-4)", marginBottom: "var(--space-8)" }}>
        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <Database size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Chủ Quyền &amp; Lưu Trữ Dữ Liệu</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Toàn bộ cơ sở dữ liệu và tệp đơn hàng được lưu trữ trên hạ tầng trung tâm dữ liệu tại Việt Nam (Viettel IDC / VNPT Data Center) hoặc máy chủ Private Cloud của doanh nghiệp. Đáp ứng 100% quy định của <strong>Nghị định 13/2023/NĐ-CP</strong> về bảo vệ dữ liệu cá nhân.
          </p>
        </div>

        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <Lock size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Mã Hóa Đa Tầng Tiêu Chuẩn</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Dữ liệu truyền tải được mã hóa toàn trình qua giao thức <strong>TLS 1.3</strong>. Dữ liệu lưu trữ tĩnh (Data-at-Rest) được mã hóa bằng thuật toán <strong>AES-256</strong> với khóa mã hóa quản lý độc lập cho từng doanh nghiệp khách hàng.
          </p>
        </div>

        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <Key size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Phân Quyền Vai Trò (RBAC)</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Cơ chế xác thực phân cấp chặt chẽ: Admin, Manager, Operator, Viewer, Auditor. Nhân viên chỉ xem được các đơn hàng trong phạm vi phụ trách; chỉ cấp Quản lý có thẩm quyền mới được duyệt các đơn hàng vi phạm cảnh báo giá hoặc tồn kho.
          </p>
        </div>

        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <FileCode size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Nhật Ký Bất Biến SHA-256</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Mọi hành động tải tệp, phát hiện vi phạm quy tắc và quyết định duyệt đơn được liên kết vào chuỗi băm <strong>SHA-256 Merkle Audit Chain</strong>. Bất kỳ hành vi sửa đổi lén nào sau khi duyệt đều lập tức làm gãy chuỗi băm và bị phát hiện ngay lập tức.
          </p>
        </div>

        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <Server size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Tùy Chọn Triển Khai On-Premise</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Dành cho các đơn vị có yêu cầu bảo mật đặc biệt khắt khe: Hệ thống có thể đóng gói Docker Container chạy hoàn toàn độc lập trong mạng LAN nội bộ của doanh nghiệp mà không cần gửi dữ liệu ra bên ngoài internet.
          </p>
        </div>

        <div className="content-card" style={{ padding: "var(--space-5)" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", display: "grid", placeItems: "center", marginBottom: "var(--space-3)" }}>
            <Trash2 size={22} color="var(--color-primary)" />
          </div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px" }}>Quy Trình Xóa &amp; Bàn Giao Dữ Liệu</h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
            Khi kết thúc thỏa thuận Pilot hoặc hợp đồng dịch vụ, toàn bộ dữ liệu đơn hàng, tệp tải lên và danh mục SKU sẽ được xuất bàn giao đầy đủ cho khách hàng và được xóa vĩnh viễn khỏi toàn bộ hệ thống sao lưu trong vòng 30 ngày.
          </p>
        </div>
      </div>

      {/* SLA & Legal Commitment Card */}
      <div
        className="content-card"
        style={{
          background: "linear-gradient(135deg, rgba(6,78,59,0.06) 0%, rgba(30,58,138,0.06) 100%)",
          border: "1px solid var(--color-primary)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-6)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-4)",
        }}
      >
        <div style={{ maxWidth: "680px" }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 800, margin: "0 0 8px", color: "var(--ink)" }}>
            Thỏa thuận bảo mật thông tin (NDA) tiêu chuẩn doanh nghiệp
          </h3>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", margin: 0, lineHeight: 1.6 }}>
            Trước khi tiến hành khảo sát và nhập danh mục mẫu, Nhật Minh Tech cung cấp thỏa thuận NDA ký điện tử hoặc văn bản trực tiếp để bảo vệ 100% quyền lợi và bí mật kinh doanh của Quý doanh nghiệp.
          </p>
        </div>

        <Link
          href="/#contact"
          className="primary-button interactive"
          onClick={createRipple}
          style={{ padding: "12px 24px", textDecoration: "none", fontWeight: 700 }}
        >
          Yêu Cầu Thỏa Thuận NDA
        </Link>
      </div>
    </div>
  );
}
