"use client";

import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  FileText,
  Package,
  Users,
  UserCheck,
  ShieldCheck,
  RefreshCw,
  Lock,
  History,
  Settings,
  LogOut,
  ChevronDown,
  BarChart3,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { useAppState } from "@/components/app/AppStateProvider";
import { useRipple } from "@/app/lib/useRipple";
import { useState } from "react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

interface NavGroup {
  name: string;
  items: NavItem[];
}

export function Sidebar() {
  const pathname = usePathname();
  const { orders, user, systemModes, healthStatus, logout } = useAppState();
  const { createRipple } = useRipple();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const attentionCount = orders.filter(
    (order) => order.status === "Review required" || order.status === "Blocked",
  ).length;

  const isAdmin = user?.role === "ADMIN" || !user; // Show admin items if admin or dev default

  const navGroups: NavGroup[] = [
    {
      name: "VẬN HÀNH",
      items: [
        { label: "Tổng quan", href: "/overview", icon: LayoutDashboard },
        { label: "Đơn hàng", href: "/orders", icon: FileText },
        { label: "Hồ sơ giải ngân", href: "/banking", icon: ShieldCheck },
        { label: "Báo cáo Pilot", href: "/reports", icon: BarChart3 },
        { label: "Khách hàng", href: "/customers", icon: Users },
        { label: "Danh mục sản phẩm", href: "/catalog", icon: Package },
        { label: "Nhật ký kiểm toán", href: "/audit-log", icon: History },
        { label: "Cài đặt & Kênh", href: "/settings", icon: Settings },
      ],
    },
    ...(isAdmin
      ? [
          {
            name: "QUẢN TRỊ HỆ THỐNG",
            items: [
              { label: "Người dùng & Phân quyền", href: "/users", icon: UserCheck },
              { label: "Luật & Chính sách", href: "/rules", icon: ShieldCheck },
              { label: "Đồng bộ ERP Outbox", href: "/erp-sync", icon: RefreshCw },
              { label: "Giám sát & Sức khỏe", href: "/admin/health", icon: Activity },
              { label: "Công cụ chẩn đoán & RAG", href: "/admin/tools", icon: Wrench },
              { label: "Chứng thư nhật ký (chuỗi băm SHA-256)", href: "/audit-certificate", icon: Lock },
            ],
          },
        ]
      : []),
  ];

  const companyName = systemModes?.company_name || "Công ty Phân phối Nhật Minh";
  const userInitials = user?.user ? user.user.slice(0, 2).toUpperCase() : "AD";
  const userName = user?.user ? user.user.replace("_", " ") : "Administrator";
  const userRole = user?.role ? `Vai trò: ${user.role}` : "Quản trị viên";

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          ✈
        </span>
        <span>PO Preflight</span>
      </div>

      <div className="workspace-switcher interactive" onClick={createRipple} title={companyName}>
        <span className="workspace-avatar">{companyName[0] || "N"}</span>
        <span className="workspace-info">
          <strong>{companyName}</strong>
          <small>Không gian vận hành</small>
        </span>
        <ChevronDown size={14} style={{ opacity: 0.7, flexShrink: 0 }} aria-hidden="true" />
      </div>

      <nav aria-label="Điều hướng chính" style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {navGroups.map((group) => (
          <div key={group.name} style={{ marginBottom: "var(--space-1)" }}>
            <div className="nav-section-label">{group.name}</div>
            {group.items.map((item) => {
              const isActive =
                (item.href === "/overview" && pathname === "/") ||
                pathname === item.href ||
                pathname.startsWith(`${item.href}/`);
              const IconComponent = item.icon;

              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={isActive ? "nav-item active interactive" : "nav-item interactive"}
                  onClick={createRipple}
                >
                  <span className="nav-icon" aria-hidden="true" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <IconComponent size={18} strokeWidth={1.75} />
                  </span>
                  <span>{item.label}</span>
                  {item.href === "/orders" && attentionCount > 0 ? (
                    <span className="nav-count">{attentionCount}</span>
                  ) : null}
                </a>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-spacer" />

      <div className="processing-card">
        <span
          className="live-dot"
          style={{
            backgroundColor: healthStatus === "healthy" ? "var(--color-success)" : "var(--color-error)",
          }}
        />
        <div>
          <strong>{healthStatus === "healthy" ? "Hệ thống ổn định" : "Mất kết nối máy chủ"}</strong>
          <small>{healthStatus === "healthy" ? "Cổng API REST 8001 sẵn sàng" : "Đang kiểm tra kết nối..."}</small>
        </div>
      </div>

      <div style={{ position: "relative" }}>
        <button
          className="profile interactive"
          onClick={(e) => {
            createRipple(e);
            setShowProfileMenu((prev) => !prev);
          }}
          type="button"
          aria-label="Tài khoản người dùng"
        >
          <span className="profile-avatar">{userInitials}</span>
          <span className="profile-info">
            <strong style={{ textTransform: "capitalize" }}>{userName}</strong>
            <small>{userRole}</small>
          </span>
          <ChevronDown size={14} style={{ opacity: 0.7, flexShrink: 0 }} aria-hidden="true" />
        </button>

        {showProfileMenu && (
          <div
            style={{
              position: "absolute",
              bottom: "100%",
              left: 0,
              right: 0,
              marginBottom: "var(--space-2)",
              backgroundColor: "var(--color-surface-container-high)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-outline-variant)",
              boxShadow: "var(--shadow-elevation-2)",
              padding: "var(--space-1)",
              zIndex: 50,
            }}
          >
            <button
              onClick={() => {
                setShowProfileMenu(false);
                void logout();
              }}
              style={{
                width: "100%",
                padding: "var(--space-2) var(--space-3)",
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
                background: "transparent",
                border: "none",
                color: "var(--color-error)",
                fontSize: "0.875rem",
                cursor: "pointer",
                borderRadius: "var(--radius-sm)",
              }}
            >
              <LogOut size={16} />
              <span>Đăng xuất</span>
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
