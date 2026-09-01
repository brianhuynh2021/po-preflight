"use client";

import { useEffect, useState } from "react";

import { formatSubmitted } from "@/app/lib/derive";

/**
 * Renders a submitted timestamp only after hydration.
 *
 * formatSubmitted() depends on the current time and locale, so it produces
 * different strings on the server vs the client and would fail React
 * hydration. Rendering nothing until mounted keeps server/client HTML
 * identical; the real value appears after hydration.
 */
export function SubmittedAt({ iso }: { iso: string }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Hydration marker: the flag is flipped once, right after the client
    // mounts, so the time/locale-dependent render never reaches the server.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  if (!mounted) return null;
  return <>{formatSubmitted(iso)}</>;
}
