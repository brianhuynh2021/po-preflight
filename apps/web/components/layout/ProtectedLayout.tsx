"use client";

import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useAppState } from "@/components/app/AppStateProvider";

export function ProtectedLayout({ children }: { children: ReactNode }) {
  const { systemModes } = useAppState();

  const mockNotices: string[] = [];
  if (systemModes) {
    if (systemModes.ocr === "unavailable") mockNotices.push("OCR Gemini chưa cấu hình");
    if (systemModes.telegram === "dry_run" || systemModes.telegram === "unconfigured") {
      mockNotices.push("Telegram bot ở chế độ dry-run/chưa cấu hình");
    }
    if (systemModes.zalo === "dry_run" || systemModes.zalo === "unconfigured") {
      mockNotices.push("Zalo OA ở chế độ dry-run/chưa cấu hình");
    }
    if (systemModes.erp?.mode === "mock") {
      mockNotices.push(`ERP Adapter ${systemModes.erp.adapter} chạy giả lập (Mock)`);
    }
  }

  const showBanner = mockNotices.length > 0;

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main">
        {showBanner && (
          <div
            style={{
              padding: "var(--space-2) var(--space-4)",
              backgroundColor: "rgba(245, 158, 11, 0.12)",
              borderBottom: "1px solid rgba(245, 158, 11, 0.3)",
              color: "#b45309",
              fontSize: "0.8125rem",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              fontWeight: 500,
            }}
          >
            <AlertTriangle size={15} color="#d97706" />
            <span>
              <strong>Chế độ thử nghiệm:</strong> {mockNotices.join(" • ")}
            </span>
          </div>
        )}
        <Topbar />
        {children}
      </main>
    </div>
  );
}
