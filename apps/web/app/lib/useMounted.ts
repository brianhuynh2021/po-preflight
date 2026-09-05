"use client";

import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

/**
 * Hook to safely detect if the component has mounted on the client.
 * Uses useSyncExternalStore to comply with React 19 and avoid SSR hydration mismatches
 * without triggering eslint react-hooks/set-state-in-effect.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}
