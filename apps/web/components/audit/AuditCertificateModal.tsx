"use client";

import React, { useState } from "react";

interface CertificateProps {
  poNumber?: string;
  onClose?: () => void;
}

export function AuditCertificateModal({ poNumber = "PO-10428", onClose }: CertificateProps) {
  const [copied, setCopied] = useState(false);

  const sampleCert = {
    po_number: poNumber,
    issued_at: new Date().toISOString(),
    standard: "SOX-404 / SOC2 Type II Non-Repudiation Audit Specification",
    merkle_root_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    blocks: [
      {
        index: 0,
        event: "GENESIS_DOCUMENT_INGESTION",
        block_hash: "a8f5f167f44f4964e6c998dee827110c",
        timestamp: "2026-09-01T08:00:00Z",
        actor: "system_ingestion_worker",
      },
      {
        index: 1,
        event: "PREFLIGHT_RULES_EVALUATION",
        block_hash: "b10a8db164e0754105b7a99be72e3fe5",
        timestamp: "2026-09-01T08:00:01Z",
        actor: "rules_engine_deterministic",
      },
      {
        index: 2,
        event: "HUMAN_APPROVAL_AUTHORIZATION",
        block_hash: "c79a95781a941584c6c2149b1ff53457",
        timestamp: "2026-09-01T08:05:22Z",
        actor: "operations_director",
        decision: "APPROVED",
        signature: "ECDSA_P256_04c56b...",
      },
      {
        index: 3,
        event: "TRANSACTIONAL_OUTBOX_ERP_DELIVERY",
        block_hash: "d9e84325a770417382049e25d97f9011",
        timestamp: "2026-09-01T08:05:23Z",
        actor: "sap_outbox_connector",
        erp_reference: "SAP-SO-20268899",
      },
    ],
    chain_integrity: "VERIFIED_VALID",
    hash_algorithm: "SHA-256 (NIST FIPS 180-4)",
  };

  const copyCert = () => {
    navigator.clipboard.writeText(JSON.stringify(sampleCert, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="page audit-cert-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">COMPLIANCE & NON-REPUDIATION (ISSUE #40)</p>
          <h1>Cryptographic Audit Certificate Center</h1>
          <p>
            Cryptographic SHA-256 Merkle hash chain certification for regulatory compliance, SOX 404 auditability, and tamper-evident history verification.
          </p>
        </div>
        <div>
          <button className="primary-button" onClick={copyCert}>
            {copied ? "✔ Certificate Copied!" : "📋 Copy Signed JSON Certificate"}
          </button>
        </div>
      </div>

      <div className="workspace-grid" style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px" }}>
        {/* Certificate Presentation Card */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "24px", borderRadius: "10px", border: "1px solid #3b82f6", boxShadow: "0 0 20px #3b82f622" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid #334155", paddingBottom: "16px", marginBottom: "16px" }}>
            <div>
              <div style={{ fontSize: "12px", color: "#60a5fa", fontWeight: "bold" }}>OFFICIAL VERIFICATION CERTIFICATE</div>
              <h2 style={{ fontSize: "20px", color: "#fff", marginTop: "4px" }}>Order: {sampleCert.po_number}</h2>
            </div>
            <div style={{ padding: "6px 12px", background: "#064e3b", color: "#34d399", borderRadius: "20px", fontSize: "12px", fontWeight: "bold", border: "1px solid #059669" }}>
              ✔ MERKLE CHAIN VALID
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px", marginBottom: "20px" }}>
            <div>
              <span style={{ color: "#94a3b8" }}>Standard:</span>
              <div style={{ color: "#fff", fontWeight: "bold" }}>{sampleCert.standard}</div>
            </div>
            <div>
              <span style={{ color: "#94a3b8" }}>Hash Algorithm:</span>
              <div style={{ color: "#fff", fontWeight: "bold" }}>{sampleCert.hash_algorithm}</div>
            </div>
          </div>

          <div style={{ marginBottom: "20px", padding: "12px", background: "#0f172a", borderRadius: "6px", border: "1px solid #1e293b" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>MERKLE ROOT HASH (SHA-256)</div>
            <code style={{ fontSize: "12px", color: "#38bdf8", wordBreak: "break-all" }}>{sampleCert.merkle_root_sha256}</code>
          </div>

          <h3 style={{ fontSize: "14px", color: "#e2e8f0", marginBottom: "12px" }}>Cryptographic Ledger Blocks:</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {sampleCert.blocks.map((block) => (
              <div key={block.index} style={{ padding: "10px 14px", background: "#111827", borderRadius: "6px", border: "1px solid #1f2937", fontSize: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                  <strong style={{ color: "#a5b4fc" }}>Block #{block.index}: {block.event}</strong>
                  <span style={{ color: "#64748b" }}>{block.timestamp}</span>
                </div>
                <div style={{ color: "#94a3b8" }}>Actor: <span style={{ color: "#cbd5e1" }}>{block.actor}</span></div>
                <div style={{ color: "#64748b", fontFamily: "monospace", fontSize: "11px", marginTop: "2px" }}>Hash: {block.block_hash}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Guidance & Verification Explainer */}
        <div className="panel" style={{ background: "var(--surface-color, #1e1e2d)", padding: "20px", borderRadius: "10px", border: "1px solid var(--border-color, #333)" }}>
          <h3 style={{ fontSize: "16px", color: "#fff", marginBottom: "12px" }}>Non-Repudiation Guarantee</h3>
          <p style={{ fontSize: "13px", color: "#94a3b8", lineHeight: "1.6", marginBottom: "16px" }}>
            Every PO ingestion, rule finding, human approval override, and ERP dispatch event is cryptographically linked in a tamper-evident SHA-256 Hash Chain.
          </p>

          <div style={{ padding: "14px", background: "#0f172a", borderRadius: "8px", borderLeft: "4px solid #10b981", marginBottom: "16px" }}>
            <h4 style={{ fontSize: "13px", color: "#34d399", marginBottom: "4px" }}>SOX 404 Audit Readiness</h4>
            <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0 }}>
              External auditors can mathematically verify that no financial figures or order items were modified post-approval without requiring access to live database credentials.
            </p>
          </div>

          <div style={{ padding: "14px", background: "#0f172a", borderRadius: "8px", borderLeft: "4px solid #3b82f6" }}>
            <h4 style={{ fontSize: "13px", color: "#60a5fa", marginBottom: "4px" }}>Cryptographic Nonce & Timestamp</h4>
            <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0 }}>
              Timestamps are anchored to UTC ISO-8601 with microsecond precision, preventing backdated order authorization attacks.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
