"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { money } from "@/app/lib/derive";
import { useRipple } from "@/app/lib/useRipple";

export function LandingPageView() {
  const { createRipple } = useRipple();

  // Video Demo Player State
  const [videoLang, setVideoLang] = useState<"vi" | "en">("vi");
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Chapters data corresponding to actual 60s demo video storyboard
  const chapters = [
    {
      id: 0,
      time: 0,
      timeLabel: "00:00 - 00:09",
      titleVi: "1. Nỗi đau đối soát thủ công",
      titleEn: "1. Manual Intake Bottleneck",
      descVi: "Xử lý file Excel lệch cột, ảnh scan mờ và rà soát thủ công 25 phút/đơn.",
      descEn: "Tackling misaligned spreadsheets, blurry scans, and 25-min manual checks.",
    },
    {
      id: 1,
      time: 9.5,
      timeLabel: "00:09 - 00:22",
      titleVi: "2. Bóc tách & Kiểm toán số học",
      titleEn: "2. Ingestion & Deterministic Math Audit",
      descVi: "Bóc tách đa định dạng chỉ trong 2 giây, tự tính lại tổng tiền dòng chống sai lệch.",
      descEn: "Instant multi-format parsing with zero-hallucination arithmetic re-audit.",
    },
    {
      id: 2,
      time: 22.5,
      timeLabel: "00:22 - 00:36",
      titleVi: "3. Khớp SKU 4 tầng & Luật 3 chiều",
      titleEn: "3. 4-Tier SKU Match & 3-Way Policy",
      descVi: "Hiểu tiếng lóng hàng hóa, đối chiếu giá hợp đồng, tồn kho thực và hạn mức nợ.",
      descEn: "Resolves local slang, validates contract prices, live stock, and credit limits.",
    },
    {
      id: 3,
      time: 35.6,
      timeLabel: "00:36 - 00:48",
      titleVi: "4. Duyệt di động 1 chạm & ERP Outbox",
      titleEn: "4. 1-Tap Mobile Approval & ERP Outbox",
      descVi: "Cấp quản lý duyệt ngoại lệ tức thì qua Telegram/Zalo, đồng bộ chuẩn xác vào ERP.",
      descEn: "Instant mobile exception approvals via Telegram/Zalo, Exactly-Once sync to ERP.",
    },
    {
      id: 4,
      time: 46.6,
      timeLabel: "00:48 - 01:00",
      titleVi: "5. Báo cáo đo lường Pilot & KPI",
      titleEn: "5. Pilot ROI Analytics & Audit Trails",
      descVi: "Đo lường thời gian tiết kiệm 90%, kiểm soát dòng tiền và xuất chứng chỉ kiểm toán.",
      descEn: "Track 90% time savings, safeguard cash flow, and export audit-ready reports.",
    },
  ];

  // Determine current active chapter index
  const activeChapterIndex = chapters.reduce((acc, c, idx) => {
    if (currentTime >= c.time) return idx;
    return acc;
  }, 0);

  const handleSeekChapter = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleLanguageChange = (lang: "vi" | "en") => {
    const prevTime = videoRef.current?.currentTime || 0;
    const wasPlaying = isPlaying;
    setVideoLang(lang);
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.currentTime = prevTime;
        if (wasPlaying) {
          videoRef.current.play().catch(() => {});
        }
      }
    }, 50);
  };

  // Interactive Sandbox State
  const [testQuery, setTestQuery] = useState("dây mạng 3m bấm sẵn");
  const [matchedSku, setMatchedSku] = useState("CAB-CAT6-3M");
  const [confidence, setConfidence] = useState(0.88);
  const [latency, setLatency] = useState(8.4);
  const [tierUsed, setTierUsed] = useState("TIER_3_SEMANTIC_VECTOR");

  // ROI Calculator State
  const [dailyPOs, setDailyPOs] = useState(60);
  const [adminHourlyWage, setAdminHourlyWage] = useState(45000); // 45k VND/hr (~8-10tr/month)

  // Lead Form State
  const [leadName, setLeadName] = useState("");
  const [leadEmail, setLeadEmail] = useState("");
  const [leadCompany, setLeadCompany] = useState("");
  const [leadPhone, setLeadPhone] = useState("");
  const [leadERP, setLeadERP] = useState("MISA AMIS");
  const [leadVolume, setLeadVolume] = useState("50-200 đơn/ngày");
  const [leadNote, setLeadNote] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  // Quick preset queries for sandbox
  const presets = [
    { label: "Tên Lóng Việt Nam", query: "dây mạng 3m bấm sẵn", sku: "CAB-CAT6-3M", tier: "TIER_3_SEMANTIC_VECTOR", conf: 0.88 },
    { label: "Mã SKU Chuẩn", query: "LAPTOP-A14", sku: "LAPTOP-A14", tier: "TIER_1_EXACT", conf: 1.0 },
    { label: "Gõ Sai Chính Tả", query: "laptop-a14-biz-pro", sku: "LAPTOP-A14", tier: "TIER_2_FUZZY", conf: 0.83 },
    { label: "Từ Khóa Kỹ Thuật", query: "cục chuyển đổi type c đa năng", sku: "DOCK-USBC", tier: "TIER_3_SEMANTIC_VECTOR", conf: 0.81 },
  ];

  const handleTestQuery = (q: string) => {
    setTestQuery(q);
    const qLower = q.toLowerCase();
    if (qLower.includes("laptop") || qLower.includes("a14")) {
      setMatchedSku("LAPTOP-A14");
      setConfidence(0.95);
      setLatency(3.2);
      setTierUsed(qLower === "laptop-a14" ? "TIER_1_EXACT" : "TIER_2_FUZZY");
    } else if (qLower.includes("mạng") || qLower.includes("cat6") || qLower.includes("dây")) {
      setMatchedSku("CAB-CAT6-3M");
      setConfidence(0.88);
      setLatency(8.4);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    } else if (qLower.includes("dock") || qLower.includes("chuyển") || qLower.includes("type c")) {
      setMatchedSku("DOCK-USBC");
      setConfidence(0.82);
      setLatency(7.9);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    } else {
      setMatchedSku("MONITOR-27");
      setConfidence(0.78);
      setLatency(11.2);
      setTierUsed("TIER_3_SEMANTIC_VECTOR");
    }
  };

  // ROI Calculations with transparent formula
  const monthlyPOs = dailyPOs * 24; // 24 working days
  const manualMinutesPerPO = 20; // 20 mins per PO manually
  const preflightMinutesPerPO = 0.5; // 30 seconds with PO Preflight
  const manualHoursMonthly = monthlyPOs * (manualMinutesPerPO / 60);
  const preflightHoursMonthly = monthlyPOs * (preflightMinutesPerPO / 60);
  const hoursSavedMonthly = Math.round(manualHoursMonthly - preflightHoursMonthly);
  const laborCostSaved = hoursSavedMonthly * adminHourlyWage;
  const pricingRiskSaved = Math.round(monthlyPOs * 0.02 * 350000); // 2% pricing error risk * 350k VND avg loss
  const totalMonthlySavings = laborCostSaved + pricingRiskSaved;

  const handleLeadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEmail || !leadName || !leadPhone) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const res = await fetch("/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: leadName,
          company: leadCompany || "Doanh nghiệp phân phối",
          phone: leadPhone,
          email: leadEmail,
          erp: leadERP,
          volume: leadVolume,
          note: leadNote,
          website: honeypot, // Honeypot bot protection
        }),
      });

      if (res.status === 429) {
        setSubmitError("Bạn đã gửi quá 5 yêu cầu trong 1 phút. Vui lòng thử lại sau.");
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setSubmitError(data.detail || "Không thể gửi đăng ký. Vui lòng liên hệ hotline.");
        return;
      }

      setSubmitted(true);
    } catch {
      setSubmitError("Lỗi kết nối máy chủ. Vui lòng liên hệ hotline (028) 7300 6868.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="landing-root" style={{ background: "var(--canvas)", minHeight: "100vh", color: "var(--ink)" }}>
      {/* 1. Hero Section with Ambient Glow */}
      <section
        className="hero-ambient-glow"
        style={{
          borderBottom: "1px solid var(--line)",
          padding: "var(--space-12) var(--space-4) var(--space-10)",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: "1160px", margin: "0 auto" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(16,185,129,0.08)",
              border: "1px solid rgba(16,185,129,0.25)",
              borderRadius: "9999px",
              padding: "6px 16px",
              marginBottom: "var(--space-4)",
            }}
          >
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 10px #10b981" }} />
            <span style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--color-primary)", letterSpacing: "0.03em" }}>
              HỆ THỐNG TIỀN KIỂM ĐƠN HÀNG B2B TỰ ĐỘNG HÓA
            </span>
          </div>

          <h1
            style={{
              fontSize: "clamp(2.2rem, 5.5vw, 3.5rem)",
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: "-0.035em",
              color: "var(--ink)",
              maxWidth: "960px",
              margin: "0 auto var(--space-4)",
            }}
          >
            Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B
          </h1>

          <p
            style={{
              fontSize: "1.125rem",
              lineHeight: 1.65,
              color: "var(--muted)",
              maxWidth: "800px",
              margin: "0 auto var(--space-6)",
            }}
          >
            Giải phóng hoàn toàn đội ngũ Sales Admin khỏi 25 phút đối soát thủ công mỗi đơn. Tự động bóc tách đơn hàng đa kênh (PDF scan, Excel, Zalo, Email); đối soát 3 chiều bảng giá hợp đồng, tồn kho thực tế và hạn mức công nợ; phê duyệt ngoại lệ 1 chạm di động trước khi đồng bộ an toàn vào ERP.
          </p>

          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap", marginBottom: "var(--space-8)" }}>
            <a
              href="#pilot"
              className="primary-button interactive"
              onClick={createRipple}
              style={{
                fontSize: "1rem",
                padding: "13px 26px",
                textDecoration: "none",
                fontWeight: 700,
                background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                boxShadow: "0 4px 14px rgba(16,185,129,0.35)",
              }}
            >
              Đăng Ký Trải Nghiệm Pilot 14 Ngày →
            </a>
            <a
              href="#demo-video"
              className="secondary-button interactive"
              onClick={createRipple}
              style={{
                fontSize: "1rem",
                padding: "13px 24px",
                textDecoration: "none",
                fontWeight: 700,
                background: "var(--paper)",
                borderColor: "var(--line-strong)",
                color: "var(--ink)",
              }}
            >
              🎬 Xem Video Demo (60s)
            </a>
            <Link
              href="/pricing"
              className="secondary-button interactive"
              onClick={createRipple}
              style={{ fontSize: "1rem", padding: "13px 22px", textDecoration: "none", fontWeight: 700 }}
            >
              Xem Bảng Giá &amp; Gói Dịch Vụ
            </Link>
          </div>

          {/* 4 Feature Grid Chips */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "12px",
              maxWidth: "1080px",
              margin: "0 auto",
            }}
          >
            <div className="feature-grid-chip">
              <span style={{ fontSize: "1.25rem" }}>🛡️</span>
              <div style={{ textAlign: "left", fontSize: "0.8125rem", lineHeight: 1.4 }}>
                <strong style={{ color: "var(--ink)", display: "block" }}>Đối soát 3 chiều 100%</strong>
                <span style={{ color: "var(--muted)" }}>Bảng giá hợp đồng, tồn kho ATP &amp; hạn mức nợ</span>
              </div>
            </div>
            <div className="feature-grid-chip">
              <span style={{ fontSize: "1.25rem" }}>⚡</span>
              <div style={{ textAlign: "left", fontSize: "0.8125rem", lineHeight: 1.4 }}>
                <strong style={{ color: "var(--ink)", display: "block" }}>Bóc tách AI trong 2s</strong>
                <span style={{ color: "var(--muted)" }}>Đọc PDF scan, Excel, ảnh chụp và văn bản thô</span>
              </div>
            </div>
            <div className="feature-grid-chip">
              <span style={{ fontSize: "1.25rem" }}>📱</span>
              <div style={{ textAlign: "left", fontSize: "0.8125rem", lineHeight: 1.4 }}>
                <strong style={{ color: "var(--ink)", display: "block" }}>Duyệt di động 1 chạm</strong>
                <span style={{ color: "var(--muted)" }}>Cảnh báo vi phạm tức thì qua Telegram &amp; Zalo OA</span>
              </div>
            </div>
            <div className="feature-grid-chip">
              <span style={{ fontSize: "1.25rem" }}>🔐</span>
              <div style={{ textAlign: "left", fontSize: "0.8125rem", lineHeight: 1.4 }}>
                <strong style={{ color: "var(--ink)", display: "block" }}>Chuỗi băm SHA-256</strong>
                <span style={{ color: "var(--muted)" }}>Niêm phong kiểm toán &amp; đồng bộ Exactly-Once ERP</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. ERP Compatibility Strip */}
      <section style={{ borderBottom: "1px solid var(--line)", background: "var(--paper)", padding: "var(--space-6) var(--space-4)", textAlign: "center" }}>
        <p style={{ fontSize: "0.75rem", fontWeight: 800, letterSpacing: "0.1em", color: "var(--muted)", textTransform: "uppercase", margin: "0 0 16px" }}>
          TƯƠNG THÍCH VÀ ĐỒNG BỘ 2 CHIỀU VỚI CÁC NỀN TẢNG ERP PHỔ BIẾN TẠI VIỆT NAM
        </p>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "12px", flexWrap: "wrap", maxWidth: "1100px", margin: "0 auto" }}>
          <div className="erp-partner-chip">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
            <span>MISA AMIS ERP</span>
          </div>
          <div className="erp-partner-chip">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
            <span>Bravo Software</span>
          </div>
          <div className="erp-partner-chip">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
            <span>Fast Business Online</span>
          </div>
          <div className="erp-partner-chip">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }} />
            <span>Odoo Enterprise</span>
          </div>
          <div className="erp-partner-chip" style={{ opacity: 0.85, borderStyle: "dashed" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#f59e0b" }} />
            <span style={{ color: "var(--muted)" }}>SAP Business One (Đang tích hợp)</span>
          </div>
        </div>
      </section>

      {/* 3. DUAL-LANGUAGE 60-SECOND DEMO VIDEO SHOWCASE */}
      <section id="demo-video" style={{ maxWidth: "1160px", margin: "0 auto", padding: "var(--space-10) var(--space-4)" }}>
        <div style={{ textAlign: "center", marginBottom: "var(--space-6)" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: "20px", padding: "3px 12px", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.85rem" }}>🎬</span>
            <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "var(--color-primary)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              TRẢI NGHIỆM TRỰC QUAN TRÊN DỮ LIỆU THẬT (60 GIÂY)
            </span>
          </div>
          <h2 style={{ fontSize: "2.1rem", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0 10px", color: "var(--ink)" }}>
            Xem Video Demo: Quy Trình Tiền Kiểm &amp; Phê Duyệt Tự Động Hóa
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "760px", margin: "0 auto 20px", fontSize: "0.95rem", lineHeight: 1.6 }}>
            Khám phá trọn vẹn luồng nghiệp vụ thực tế: Tiếp nhận tệp Excel/PDF, tự động bóc tách &amp; kiểm toán số học, khớp mã SKU 4 tầng, cảnh báo luật 3 chiều và duyệt di động tức thì trước khi ghi sổ ERP.
          </p>

          {/* Locked Bulletproof Segmented Control */}
          <div className="segmented-control-container">
            <button
              onClick={() => handleLanguageChange("vi")}
              type="button"
              className={`segmented-control-btn ${videoLang === "vi" ? "active vi" : ""}`}
            >
              <span style={{ fontSize: "1rem" }}>🇻🇳</span>
              <span>Bản Tiếng Việt (Thuyết minh &amp; Phụ đề)</span>
            </button>
            <button
              onClick={() => handleLanguageChange("en")}
              type="button"
              className={`segmented-control-btn ${videoLang === "en" ? "active en" : ""}`}
            >
              <span style={{ fontSize: "1rem" }}>🇺🇸</span>
              <span>English Edition (Voiceover &amp; Subtitles)</span>
            </button>
          </div>
        </div>

        {/* Video Player Card */}
        <div
          className="content-card"
          style={{
            padding: "0",
            background: "#090d16",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            boxShadow: "0 20px 40px -15px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.08)",
          }}
        >
          {/* Top Frame Control Bar */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 20px",
              background: "rgba(15,23,42,0.85)",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              fontSize: "0.8125rem",
              color: "#94a3b8",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", background: "#ef4444" }} />
              <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", background: "#f59e0b" }} />
              <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", background: "#10b981" }} />
              <span style={{ marginLeft: "6px", fontWeight: 600, color: "#cbd5e1" }}>
                PO Preflight Studio — 60s Live Product Walkthrough ({videoLang === "vi" ? "Tiếng Việt" : "English"})
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ background: "rgba(16,185,129,0.2)", color: "#34d399", padding: "2px 8px", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 700 }}>
                HD 1080p • 60 FPS
              </span>
              <span style={{ color: "#e2e8f0", fontWeight: 700 }}>
                {Math.floor(currentTime / 60).toString().padStart(2, "0")}:{Math.floor(currentTime % 60).toString().padStart(2, "0")} / 01:00
              </span>
            </div>
          </div>

          {/* Responsive HTML5 Video Element */}
          <div style={{ position: "relative", width: "100%", paddingTop: "56.25%", background: "#000" }}>
            <video
              ref={videoRef}
              key={videoLang}
              src={videoLang === "vi" ? "/demo/po_preflight_demo_60s_vi.mp4" : "/demo/po_preflight_demo_60s_en.mp4"}
              poster="/demo/po_preflight_demo_60s.webp"
              controls
              playsInline
              onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "contain",
                outline: "none",
              }}
            >
              {videoLang === "vi" ? (
                <track default kind="subtitles" src="/demo/subtitles_vi.vtt" srcLang="vi" label="Tiếng Việt" />
              ) : (
                <track default kind="subtitles" src="/demo/subtitles_en.vtt" srcLang="en" label="English" />
              )}
              Trình duyệt của bạn không hỗ trợ phát thẻ video HTML5.
            </video>
          </div>

          {/* Interactive Chapter Timeline Below Video */}
          <div
            style={{
              padding: "20px 24px",
              background: "#0f172a",
              borderTop: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 800, color: "#94a3b8", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                PHÂN CẢNH VIDEO (BẤM ĐỂ CHUYỂN NHANH ĐẾN MỤC QUAN TÂM):
              </span>
              <span style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: 600 }}>
                💡 Nhấp vào từng chặng để xem cận cảnh tính năng
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "10px" }}>
              {chapters.map((chap, idx) => {
                const isActive = idx === activeChapterIndex;
                return (
                  <button
                    key={chap.id}
                    onClick={() => handleSeekChapter(chap.time)}
                    style={{
                      textAlign: "left",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: isActive ? "1px solid #10b981" : "1px solid rgba(255,255,255,0.08)",
                      background: isActive ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.03)",
                      color: "#ffffff",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontSize: "0.7rem", fontWeight: 800, color: isActive ? "#34d399" : "#64748b" }}>
                        {chap.timeLabel}
                      </span>
                      {isActive && (
                        <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10b981" }} />
                      )}
                    </div>
                    <div style={{ fontSize: "0.8125rem", fontWeight: 700, color: isActive ? "#ffffff" : "#cbd5e1", marginBottom: "3px" }}>
                      {videoLang === "vi" ? chap.titleVi : chap.titleEn}
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "#94a3b8", lineHeight: 1.4 }}>
                      {videoLang === "vi" ? chap.descVi : chap.descEn}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 4 Bottom Value KPI Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-4)", marginTop: "var(--space-6)" }}>
          <div className="content-card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ fontSize: "2rem" }}>⚡</span>
            <div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-primary)" }}>&lt; 2 Giây / Đơn</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)" }}>Bóc tách đa kênh &amp; tự kiểm toán số học</div>
            </div>
          </div>
          <div className="content-card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ fontSize: "2rem" }}>📉</span>
            <div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-primary)" }}>Giảm 90% Thời Gian</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)" }}>Giải phóng Sales Admin khỏi rà soát thủ công</div>
            </div>
          </div>
          <div className="content-card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ fontSize: "2rem" }}>🛡️</span>
            <div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-primary)" }}>100% Đối Soát 3 Chiều</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)" }}>Chặn đứng đơn sai giá, thiếu kho, quá hạn nợ</div>
            </div>
          </div>
          <div className="content-card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ fontSize: "2rem" }}>🔒</span>
            <div>
              <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--color-primary)" }}>SHA-256 Bất Biến</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)" }}>Niêm phong kiểm toán &amp; đồng bộ Exactly-Once</div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. 4 Core Technological Pillars */}
      <section id="features" style={{ maxWidth: "1160px", margin: "0 auto", padding: "var(--space-8) var(--space-4) var(--space-10)" }}>
        <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
          <p className="eyebrow">4 TRỤ CỘT CÔNG NGHỆ CỐT LÕI</p>
          <h2 style={{ fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.02em", margin: "6px 0 12px" }}>
            Quy trình khép kín từ tiếp nhận đến ghi sổ ERP
          </h2>
          <p style={{ color: "var(--muted)", maxWidth: "700px", margin: "0 auto" }}>
            Giải phóng Sales Admin khỏi việc nhập liệu thủ công và ngăn chặn 100% các đơn hàng sai giá, thiếu tồn kho hoặc quá hạn mức nợ.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "var(--space-4)" }}>
          <div className="content-card" style={{ padding: "var(--space-6)", borderRadius: "var(--radius-lg)", border: "1px solid var(--line)" }}>
            <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)", display: "grid", placeItems: "center", fontSize: "1.4rem", marginBottom: "var(--space-3)" }}>
              🔍
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px", color: "var(--ink)" }}>Tự Động Bóc Tách &amp; Đối Soát Số Học</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Đọc tệp PDF, ảnh chụp hoặc Excel. Tự kiểm tra tổng tiền dòng so với tổng đơn; sai lệch bị chặn để người kiểm tra trước khi chuyển bước tiếp theo.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-6)", borderRadius: "var(--radius-lg)", border: "1px solid var(--line)" }}>
            <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", display: "grid", placeItems: "center", fontSize: "1.4rem", marginBottom: "var(--space-3)" }}>
              🧠
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px", color: "var(--ink)" }}>Khớp Mã Kho &amp; Đơn Vị Tính</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Cơ chế 4 tầng (Khớp chính xác → Fuzzy → Vector → LLM). Tự động nhận diện tên lóng tiếng Việt và quy đổi thùng/hộp/cây sang đơn vị chuẩn.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-6)", borderRadius: "var(--radius-lg)", border: "1px solid var(--line)" }}>
            <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)", display: "grid", placeItems: "center", fontSize: "1.4rem", marginBottom: "var(--space-3)" }}>
              📱
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px", color: "var(--ink)" }}>Phê Duyệt 1 Chạm Telegram &amp; Zalo</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Khi phát hiện đơn hàng vi phạm chính sách giá hoặc tồn kho, hệ thống gửi thẻ cảnh báo chi tiết về điện thoại quản lý để duyệt hoặc từ chối tức thì.
            </p>
          </div>

          <div className="content-card" style={{ padding: "var(--space-6)", borderRadius: "var(--radius-lg)", border: "1px solid var(--line)" }}>
            <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "rgba(139,92,246,0.1)", border: "1px solid rgba(139,92,246,0.2)", display: "grid", placeItems: "center", fontSize: "1.4rem", marginBottom: "var(--space-3)" }}>
              🔒
            </div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 8px", color: "var(--ink)" }}>Nhật Ký Bất Biến SHA-256 &amp; Outbox</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", lineHeight: 1.6, margin: 0 }}>
              Nhật ký bất biến có chuỗi băm SHA-256, xuất được để đối soát. Hàng đợi Transactional Outbox đảm bảo đồng bộ vào ERP đúng duy nhất 1 lần (Exactly-Once).
            </p>
          </div>
        </div>
      </section>

      {/* 5. Interactive SKU Sandbox Widget */}
      <section id="sandbox" style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div className="content-card" style={{ padding: "var(--space-6)", background: "var(--surface)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-5)" }}>
            <span className="badge-clean badge-clean-neutral" style={{ marginBottom: "var(--space-2)" }}>TRẢI NGHIỆM TRÍ TUỆ KHỚP MÃ KHO</span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 8px" }}>
              Tự Động Hiểu &quot;Tên Lóng&quot; &amp; Biệt Danh Hàng Hóa Của Khách
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "600px", margin: "0 auto" }}>
              Khách hàng ghi theo cách của họ (viết tắt, gõ sai, tiếng lóng) — Hệ thống tự động ánh xạ về mã SKU kho chuẩn.
            </p>
          </div>

          <div style={{ marginBottom: "var(--space-4)" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>THỬ CÁC TÌNH HUỐNG MẪU:</span>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "6px" }}>
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  className="secondary-button interactive"
                  onClick={() => handleTestQuery(p.query)}
                  style={{ fontSize: "0.75rem", padding: "4px 10px" }}
                >
                  {p.label}: <strong>&quot;{p.query}&quot;</strong>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 700, marginBottom: "4px" }}>
                Nhập Tên Hàng / Tên Viết Tắt:
              </label>
              <input
                type="text"
                value={testQuery}
                onChange={(e) => handleTestQuery(e.target.value)}
                placeholder="Gõ thử: dây mạng 3m, laptop a14, dock chuyển đổi..."
                style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
              />
            </div>

            <div style={{ background: "rgba(16,185,129,0.06)", border: "1px solid var(--color-primary)", borderRadius: "var(--radius-sm)", padding: "12px 16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-primary)" }}>KẾT QUẢ ÁNH XẠ:</span>
                <span className="badge-clean badge-clean-success" style={{ fontSize: "0.7rem" }}>{tierUsed}</span>
              </div>
              <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--ink)" }}>Mã SKU: {matchedSku}</div>
              <div style={{ fontSize: "0.8125rem", color: "var(--muted)", marginTop: "4px" }}>
                Độ tin cậy: {(confidence * 100).toFixed(0)}% • Thời gian xử lý: {latency}ms
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Transparent ROI Calculator */}
      <section id="roi-calculator" style={{ maxWidth: "1000px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div className="content-card" style={{ padding: "var(--space-6)", border: "1px solid var(--color-primary)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-5)" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "var(--space-2)" }}>BẢNG TÍNH HIỆU QUẢ HOÀN VỐN</span>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 8px" }}>
              Ước tính hiệu quả kinh tế cho doanh nghiệp của bạn
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "650px", margin: "0 auto" }}>
              Công thức dựa trên giả định thực tế: Giảm thời gian xử lý từ 20 phút xuống 30 giây/đơn và phòng ngừa 2% rủi ro sai sót đơn giá.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-6)", alignItems: "center" }}>
            <div>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Số đơn hàng trung bình mỗi ngày:</span>
                  <span style={{ color: "var(--color-primary)" }}>{dailyPOs} đơn/ngày</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={500}
                  step={5}
                  value={dailyPOs}
                  onChange={(e) => setDailyPOs(Number(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "var(--space-4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Chi phí lương nhân viên nhập liệu:</span>
                  <span style={{ color: "var(--color-primary)" }}>{money(adminHourlyWage, "VND")}/giờ</span>
                </div>
                <input
                  type="range"
                  min={30000}
                  max={100000}
                  step={5000}
                  value={adminHourlyWage}
                  onChange={(e) => setAdminHourlyWage(Number(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ fontSize: "0.8125rem", color: "var(--muted)", lineHeight: 1.5, background: "var(--canvas)", padding: "10px", borderRadius: "var(--radius-sm)" }}>
                <strong>Công thức ước tính:</strong><br />
                • Tiết kiệm giờ làm: {dailyPOs} đơn × 24 ngày × 19.5 phút = {hoursSavedMonthly} giờ/tháng.<br />
                • Ngăn ngừa rủi ro giá: {dailyPOs} × 24 × 2% × 350.000 đ = {money(pricingRiskSaved, "VND")}/tháng.
              </div>
            </div>

            <div style={{ textAlign: "center", background: "linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(30,58,138,0.1) 100%)", padding: "var(--space-6)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-primary)" }}>
              <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>TỔNG GIÁ TRỊ TIẾT KIỆM HÀNG THÁNG:</div>
              <div style={{ fontSize: "2.25rem", fontWeight: 900, color: "var(--color-primary)", margin: "8px 0" }}>
                {money(totalMonthlySavings, "VND")}
              </div>
              <div style={{ fontSize: "0.875rem", color: "var(--muted)" }}>
                Tiết kiệm tương đương <strong>{hoursSavedMonthly} giờ làm việc</strong> và phòng ngừa rủi ro sai giá.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Lead Capture Form Section */}
      <section id="pilot" style={{ maxWidth: "800px", margin: "0 auto", padding: "0 var(--space-4) var(--space-10)" }}>
        <div id="contact" style={{ position: "relative", top: "-40px", visibility: "hidden" }} />
        <div className="content-card" style={{ padding: "var(--space-8)", background: "var(--surface)", border: "2px solid var(--color-primary)" }}>
          <div style={{ textAlign: "center", marginBottom: "var(--space-6)" }}>
            <span className="badge-clean badge-clean-success" style={{ marginBottom: "var(--space-2)" }}>CHƯƠNG TRÌNH PILOT 14 NGÀY</span>
            <h2 style={{ fontSize: "1.75rem", fontWeight: 800, margin: "6px 0 8px" }}>
              Đăng Ký Trải Nghiệm Pilot 14 Ngày Miễn Phí
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", maxWidth: "560px", margin: "0 auto" }}>
              Miễn phí 14 ngày (tối đa 300 đơn hàng thực tế). Ký thỏa thuận bảo mật bảng giá NDA trước khi khảo sát và thiết lập môi trường thử nghiệm riêng.
            </p>
          </div>

          {submitted ? (
            <div style={{ padding: "24px", background: "rgba(16,185,129,0.1)", borderRadius: "var(--radius-md)", textAlign: "center", border: "1px solid var(--color-primary)" }}>
              <div style={{ fontSize: "2rem", marginBottom: "8px" }}>🎉</div>
              <h3 style={{ color: "var(--color-primary)", margin: "0 0 8px", fontSize: "1.25rem" }}>Đã Nhận Thông Tin Đăng Ký!</h3>
              <p style={{ fontSize: "0.95rem", color: "var(--ink)", margin: 0, lineHeight: 1.6 }}>
                Chúng tôi sẽ liên hệ trong vòng 1 ngày làm việc qua số điện thoại <strong>{leadPhone}</strong> và email <strong>{leadEmail}</strong> để trao đổi chi tiết.
              </p>
            </div>
          ) : (
            <form onSubmit={handleLeadSubmit} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
              {/* Anti-bot honeypot */}
              <input
                type="text"
                name="website"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
                style={{ display: "none" }}
                tabIndex={-1}
                autoComplete="off"
              />

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Họ và Tên Người Phụ Trách *
                </label>
                <input
                  type="text"
                  required
                  value={leadName}
                  onChange={(e) => setLeadName(e.target.value)}
                  placeholder="Nguyễn Văn A"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Tên Doanh Nghiệp / Đơn Vị *
                </label>
                <input
                  type="text"
                  required
                  value={leadCompany}
                  onChange={(e) => setLeadCompany(e.target.value)}
                  placeholder="Công ty CP / TNHH..."
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Email Doanh Nghiệp (Work Email) *
                </label>
                <input
                  type="email"
                  required
                  value={leadEmail}
                  onChange={(e) => setLeadEmail(e.target.value)}
                  placeholder="ten@congty.vn"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Số Điện Thoại / Zalo *
                </label>
                <input
                  type="tel"
                  required
                  value={leadPhone}
                  onChange={(e) => setLeadPhone(e.target.value)}
                  placeholder="0912 345 678"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Hệ Thống ERP Đang Dùng
                </label>
                <select
                  value={leadERP}
                  onChange={(e) => setLeadERP(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                >
                  <option value="MISA AMIS">MISA AMIS</option>
                  <option value="Bravo">Bravo Software</option>
                  <option value="Fast">Fast Business</option>
                  <option value="Odoo">Odoo</option>
                  <option value="SAP B1">SAP Business One</option>
                  <option value="Excel">Đang quản lý bằng Excel</option>
                  <option value="Khác">Khác / Tùy chỉnh</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Số Lượng Đơn/Ngày
                </label>
                <select
                  value={leadVolume}
                  onChange={(e) => setLeadVolume(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)" }}
                >
                  <option value="Dưới 30 đơn/ngày">Dưới 30 đơn/ngày</option>
                  <option value="30-100 đơn/ngày">30-100 đơn/ngày</option>
                  <option value="100-300 đơn/ngày">100-300 đơn/ngày</option>
                  <option value="Trên 300 đơn/ngày">Trên 300 đơn/ngày</option>
                </select>
              </div>

              <div style={{ gridColumn: "1 / -1" }}>
                <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 700, marginBottom: "4px" }}>
                  Ghi Chú Hoặc Nhu Cầu Cụ Thể (Tùy chọn)
                </label>
                <textarea
                  rows={2}
                  value={leadNote}
                  onChange={(e) => setLeadNote(e.target.value)}
                  placeholder="Ví dụ: Cần kiểm tra công nợ và đồng bộ vào MISA AMIS..."
                  style={{ width: "100%", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--color-outline-variant)", resize: "vertical" }}
                />
              </div>

              {submitError && (
                <div style={{ gridColumn: "1 / -1", color: "var(--color-error)", fontSize: "0.875rem" }}>
                  ⚠️ {submitError}
                </div>
              )}

              <div style={{ gridColumn: "1 / -1", marginTop: "8px" }}>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="primary-button interactive"
                  onClick={createRipple}
                  style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: "1rem", fontWeight: 700 }}
                >
                  {isSubmitting ? "Đang gửi thông tin..." : "🚀 Kích Hoạt 14 Ngày Trải Nghiệm Pilot Miễn Phí"}
                </button>
                <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--muted)", marginTop: "8px" }}>
                  🔒 Cam kết bảo mật thông tin 100%. Ký thỏa thuận NDA trước khi tiến hành thử nghiệm.
                </p>
              </div>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
