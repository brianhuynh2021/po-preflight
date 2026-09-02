"use client";

import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import { useRipple } from "@/app/lib/useRipple";

interface CertificateProps {
  poNumber?: string;
  onClose?: () => void;
}

export function AuditCertificateModal({ poNumber = "PO-10428" }: CertificateProps) {
  const { createRipple } = useRipple();
  const [copied, setCopied] = useState(false);

  const sampleCert = {
    po_number: poNumber,
    issued_at: new Date().toISOString(),
    standard: "Chuỗi băm bất biến SHA-256 Merkle Audit Chain",
    merkle_root_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    blocks: [
      {
        index: 0,
        event: "GENESIS_DOCUMENT_INGESTION",
        description: "Tiếp nhận & bóc tách tệp đơn hàng gốc",
        block_hash: "a8f5f167f44f4964e6c998dee827110c",
        timestamp: "2026-09-01T08:00:00Z",
        actor: "system_ingestion_worker",
      },
      {
        index: 1,
        event: "PREFLIGHT_RULES_EVALUATION",
        description: "Kiểm tra quy tắc giá, tồn kho và công nợ",
        block_hash: "b10a8db164e0754105b7a99be72e3fe5",
        timestamp: "2026-09-01T08:00:01Z",
        actor: "rules_engine_deterministic",
      },
      {
        index: 2,
        event: "HUMAN_APPROVAL_AUTHORIZATION",
        description: "Phê duyệt có chữ ký điện tử từ Quản lý",
        block_hash: "c79a95781a941584c6c2149b1ff53457",
        timestamp: "2026-09-01T08:05:22Z",
        actor: "operations_manager",
        decision: "APPROVED",
        signature: "ECDSA_P256_04c56b...",
      },
      {
        index: 3,
        event: "TRANSACTIONAL_OUTBOX_ERP_DELIVERY",
        description: "Đồng bộ an toàn qua Transactional Outbox vào ERP",
        block_hash: "d9e84325a770417382049e25d97f9011",
        timestamp: "2026-09-01T08:05:23Z",
        actor: "erp_outbox_connector",
        erp_reference: "MISA-SO-20268899",
      },
    ],
    chain_integrity: "VERIFIED_VALID",
    hash_algorithm: "SHA-256 (NIST FIPS 180-4)",
  };

  const copyCert = (e: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    navigator.clipboard.writeText(JSON.stringify(sampleCert, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="page audit-cert-page page-enter">
      <div className="page-heading">
        <div>
          <p className="eyebrow">BẢO MẬT &amp; CHỐNG CHỐI BỎ THÔNG TIN</p>
          <h1>Trung tâm Chứng thư Kiểm toán Mật mã</h1>
          <p>
            Chứng thư chuỗi băm SHA-256 Merkle bất biến phục vụ đối soát kế toán và xác thực lịch sử đơn hàng chống sửa đổi lén.
          </p>
        </div>
        <div>
          <button className="primary-button interactive" onClick={copyCert} style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-1)" }}>
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? "Đã sao chép vào bộ nhớ" : "Xuất chứng thư JSON có chữ ký"}</span>
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "var(--space-5)" }}>
        {/* Certificate Card */}
        <div className="content-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <div>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 700, textTransform: "uppercase" }}>CHỨNG NHẬN XÁC THỰC CHÍNH THỨC</span>
              <h2 style={{ fontSize: "1.15rem", margin: "4px 0 0", color: "var(--ink)" }}>Đơn hàng: {sampleCert.po_number}</h2>
            </div>
            <span className="badge-clean badge-clean-success">
              ✔ CHUỖI MERKLE HỢP LỆ
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)", fontSize: "0.875rem", marginBottom: "var(--space-4)" }}>
            <div>
              <span style={{ color: "var(--muted)", display: "block", fontSize: "0.75rem" }}>Tiêu chuẩn kiểm toán:</span>
              <strong style={{ color: "var(--ink)" }}>{sampleCert.standard}</strong>
            </div>
            <div>
              <span style={{ color: "var(--muted)", display: "block", fontSize: "0.75rem" }}>Thuật toán băm:</span>
              <strong style={{ color: "var(--ink)" }}>{sampleCert.hash_algorithm}</strong>
            </div>
          </div>

          <div
            style={{
              background: "var(--canvas)",
              padding: "var(--space-3)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--line)",
              marginBottom: "var(--space-4)",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 700, marginBottom: "4px" }}>
              MÃ BĂM GỐC MERKLE ROOT (SHA-256)
            </div>
            <code style={{ fontSize: "0.75rem", color: "var(--color-primary)", wordBreak: "break-all", fontFamily: "ui-monospace, monospace" }}>
              {sampleCert.merkle_root_sha256}
            </code>
          </div>

          <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--ink)", marginBottom: "var(--space-2)", textTransform: "uppercase" }}>
            Danh sách các khối trong chuỗi nhật ký (Ledger Chain)
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {sampleCert.blocks.map((block) => (
              <div
                key={block.index}
                style={{
                  padding: "var(--space-2) var(--space-3)",
                  background: "var(--canvas)",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--line)",
                  fontSize: "0.75rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                  <strong style={{ color: "var(--ink)" }}>
                    #{block.index}: {block.description}
                  </strong>
                  <span style={{ color: "var(--muted)", fontSize: "0.7rem" }}>{block.timestamp}</span>
                </div>
                <div style={{ color: "var(--muted)", fontSize: "0.75rem" }}>
                  Tác nhân: <span style={{ color: "var(--ink)", fontWeight: 500 }}>{block.actor}</span>
                </div>
                <div style={{ color: "var(--muted)", fontFamily: "ui-monospace, monospace", fontSize: "0.7rem", marginTop: "2px" }}>
                  Mã băm khối: {block.block_hash}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Explainer & Non-Repudiation */}
        <div className="content-card">
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 12px" }}>Cam kết chống chối bỏ &amp; Kiểm toán độc lập</h3>

          <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, marginBottom: "var(--space-4)" }}>
            Mọi sự kiện từ bóc tách văn bản, kết quả kiểm tra quy tắc, quyết định phê duyệt có ngoại lệ cho đến gói tin đồng bộ ERP đều được liên kết bằng chuỗi băm SHA-256 Merkle bất biến.
          </p>

          <div
            style={{
              padding: "var(--space-3)",
              background: "rgba(16,185,129,0.08)",
              border: "1px solid var(--color-primary)",
              borderRadius: "var(--radius-sm)",
              marginBottom: "var(--space-3)",
            }}
          >
            <h4 style={{ fontSize: "0.875rem", color: "var(--color-primary)", margin: "0 0 4px", fontWeight: 700 }}>
              Sẵn sàng cho kiểm toán độc lập
            </h4>
            <p style={{ fontSize: "0.75rem", color: "var(--ink)", margin: 0, lineHeight: 1.5 }}>
              Kiểm toán viên nội bộ hoặc đơn vị kiểm toán độc lập có thể kiểm tra toán học chuỗi băm để xác nhận không có bất kỳ số liệu đơn hàng nào bị thay đổi lén sau khi duyệt.
            </p>
          </div>

          <div
            style={{
              padding: "var(--space-3)",
              background: "rgba(59,130,246,0.08)",
              border: "1px solid rgba(59,130,246,0.3)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <h4 style={{ fontSize: "0.875rem", color: "#2563eb", margin: "0 0 4px", fontWeight: 700 }}>
              Dấu thời gian UTC chuẩn xác
            </h4>
            <p style={{ fontSize: "0.75rem", color: "var(--ink)", margin: 0, lineHeight: 1.5 }}>
              Mỗi khối nhật ký được gắn dấu thời gian ISO-8601 theo giờ chuẩn UTC, ngăn chặn việc tạo lùi ngày duyệt hoặc can thiệp thời gian phê duyệt.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
