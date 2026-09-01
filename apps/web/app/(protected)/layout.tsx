import type { ReactNode } from "react";

import { AppStateProvider } from "@/components/app/AppStateProvider";
import { ProtectedLayout } from "@/components/layout/ProtectedLayout";

export default function ProtectedLayoutWrapper({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AppStateProvider>
      <ProtectedLayout>{children}</ProtectedLayout>
    </AppStateProvider>
  );
}
