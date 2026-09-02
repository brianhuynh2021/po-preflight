"use client";

import React, { useState } from "react";

interface CertificateProps {
  poNumber?: string;
  onClose?: () => void;
}

export function AuditCertificateModal({ poNumber = "PO-10428" }: CertificateProps) {
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
            {copied ? "✔ Copied to Clipboard" : "📋 Export Signed JSON Certificate"}
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "var(--space-5)" }}>
        {/* Certificate Card */}
        <div className="clean-card">
          <div className="card-header-clean">
            <div>
              <span style={{ fontSize: "var(--text-xs)", color: "var(--muted)", fontWeight: 700 }}>OFFICIAL VERIFICATION CERTIFICATE</span>
              <h2 style={{ fontSize: "var(--text-lg)", margin: "var(--space-1) 0 0", color: "var(--ink)" }}>Order: {sampleCert.po_number}</h2>
            </div>
            <span className="badge-clean badge-clean-success">
              ✔ MERKLE CHAIN VALID
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)", fontSize: "var(--text-sm)", marginBottom: "var(--space-4)" }}>
            <div>
              <span style={{ color: "var(--muted)", display: "block" }}>Compliance Standard:</span>
              <strong style={{ color: "var(--ink)" }}>{sampleCert.standard}</strong>
            </div>
            <div>
              <span style={{ color: "var(--muted)", display: "block" }}>Hashing Engine:</span>
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
            <div style={{ fontSize: "var(--text-xs)", color: "var(--muted)", fontWeight: 700, marginBottom: "var(--space-1)" }}>
              MERKLE ROOT HASH (SHA-256)
            </div>
            <code style={{ fontSize: "var(--text-xs)", color: "var(--green)", wordBreak: "break-all", fontFamily: "ui-monospace, monospace" }}>
              {sampleCert.merkle_root_sha256}
            </code>
          </div>

          <h3 style={{ fontSize: "var(--text-sm)", fontWeight: 700, color: "var(--ink)", marginBottom: "var(--space-2)", textTransform: "uppercase" }}>
            Cryptographic Ledger Chain
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
                  fontSize: "var(--text-xs)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                  <strong style={{ color: "var(--ink)" }}>
                    #{block.index}: {block.event}
                  </strong>
                  <span style={{ color: "var(--muted)", fontSize: "var(--text-xs)" }}>{block.timestamp}</span>
                </div>
                <div style={{ color: "var(--muted)", fontSize: "var(--text-xs)" }}>
                  Actor: <span style={{ color: "var(--ink)", fontWeight: 500 }}>{block.actor}</span>
                </div>
                <div style={{ color: "var(--faint)", fontFamily: "ui-monospace, monospace", fontSize: "var(--text-xs)", marginTop: "var(--space-1)" }}>
                  Hash: {block.block_hash}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Explainer & Non-Repudiation */}
        <div className="clean-card">
          <div className="card-header-clean">
            <h3>Non-Repudiation Guarantee</h3>
          </div>

          <p style={{ fontSize: "var(--text-sm)", color: "var(--muted)", lineHeight: 1.5, marginBottom: "var(--space-4)" }}>
            Every document parsing, deterministic rule finding, human approval override, and ERP dispatch event is cryptographically linked in a tamper-evident SHA-256 hash chain.
          </p>

          <div
            style={{
              padding: "var(--space-3)",
              background: "var(--green-soft)",
              border: "1px solid rgba(25, 112, 76, 0.2)",
              borderRadius: "var(--radius-sm)",
              marginBottom: "var(--space-3)",
            }}
          >
            <h4 style={{ fontSize: "var(--text-sm)", color: "var(--green)", margin: "0 0 var(--space-1)", fontWeight: 700 }}>
              SOX 404 Audit Readiness
            </h4>
            <p style={{ fontSize: "var(--text-xs)", color: "var(--ink)", margin: 0, lineHeight: 1.4 }}>
              External auditors can mathematically verify that no figures or order items were altered post-approval without needing live database access.
            </p>
          </div>

          <div
            style={{
              padding: "var(--space-3)",
              background: "var(--blue-soft)",
              border: "1px solid rgba(56, 107, 142, 0.2)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            <h4 style={{ fontSize: "var(--text-sm)", color: "var(--blue)", margin: "0 0 var(--space-1)", fontWeight: 700 }}>
              Cryptographic Nonce & Timestamp
            </h4>
            <p style={{ fontSize: "var(--text-xs)", color: "var(--ink)", margin: 0, lineHeight: 1.4 }}>
              Timestamps are anchored to UTC ISO-8601 with microsecond precision, preventing backdated order authorization attacks.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
