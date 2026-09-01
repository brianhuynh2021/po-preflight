"use client";

import { useTheme } from "@/app/lib/useTheme";

export function Topbar() {
  const { theme, toggleTheme } = useTheme();
  const resolved = theme !== null;
  const isDark = theme === "dark";

  return (
    <header className="topbar">
      <div className="mobile-brand">
        <span className="brand-mark">O</span>
        <strong>Preflight</strong>
      </div>
      <div className="topbar-actions">
        <button
          className="icon-button"
          aria-label="Toggle theme"
          title={
            resolved
              ? isDark
                ? "Switch to light theme"
                : "Switch to dark theme"
              : "Toggle theme"
          }
          onClick={toggleTheme}
          type="button"
        >
          {resolved ? (isDark ? "☀" : "☾") : "◐"}
        </button>
        <button className="icon-button" aria-label="Help">
          ?
        </button>
        <button
          className="icon-button notification-button"
          aria-label="Notifications"
        >
          ♢<span />
        </button>
      </div>
    </header>
  );
}