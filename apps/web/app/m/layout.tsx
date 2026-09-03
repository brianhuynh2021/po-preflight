import type { ReactNode } from "react";

export const metadata = {
  title: "Phê duyệt đơn hàng di động | PO Preflight",
  description: "Giao diện phê duyệt đơn hàng một chạm tối giản dành cho thiết bị di động",
};

export default function MobileLayout({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "var(--canvas)",
        color: "var(--ink)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div style={{ width: "100%", maxWidth: "480px", minHeight: "100vh", background: "var(--surface)", display: "flex", flexDirection: "column" }}>
        {children}
      </div>
    </div>
  );
}
