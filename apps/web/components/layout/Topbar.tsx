"use client";

import { Sun, Moon, HelpCircle, Bell } from "lucide-react";
import { useTheme } from "@/app/lib/useTheme";
import { useRipple } from "@/app/lib/useRipple";

export function Topbar() {
  const { theme, toggleTheme } = useTheme();
  const { createRipple } = useRipple();
  const resolved = theme !== null;
  const isDark = theme === "dark";

  return (
    <header className="topbar">
      <div className="mobile-brand">
        <span className="brand-mark">✈</span>
        <strong>Preflight</strong>
      </div>
      <div className="topbar-actions">
        <button
          className="icon-button interactive"
          aria-label="Toggle theme"
          title={
            resolved
              ? isDark
                ? "Switch to light theme"
                : "Switch to dark theme"
              : "Toggle theme"
          }
          onClick={(e) => {
            createRipple(e);
            toggleTheme();
          }}
          type="button"
          style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          {resolved ? (
            isDark ? (
              <Sun size={17} strokeWidth={1.8} />
            ) : (
              <Moon size={17} strokeWidth={1.8} />
            )
          ) : (
            <Sun size={17} strokeWidth={1.8} />
          )}
        </button>

        <button
          className="icon-button interactive"
          aria-label="Help"
          onClick={createRipple}
          type="button"
          style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <HelpCircle size={17} strokeWidth={1.8} />
        </button>

        <button
          className="icon-button notification-button interactive"
          aria-label="Notifications"
          onClick={createRipple}
          type="button"
          style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <Bell size={17} strokeWidth={1.8} />
          <span />
        </button>
      </div>
    </header>
  );
}