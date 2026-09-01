"use client";

import { useCallback, type MouseEvent } from "react";

/**
 * Google Material 3 Ripple effect hook.
 * Spawns a radial ripple originating precisely from the click/tap coordinate.
 * Respects prefers-reduced-motion accessibility preference.
 */
export function useRipple() {
  const createRipple = useCallback((event: MouseEvent<HTMLElement>) => {
    // Disable ripple if user prefers reduced motion
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    const currentTarget = event.currentTarget;
    if (!currentTarget) return;

    const rect = currentTarget.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 2;
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.width = `${size}px`;
    ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;

    currentTarget.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 550);
  }, []);

  return { createRipple };
}
