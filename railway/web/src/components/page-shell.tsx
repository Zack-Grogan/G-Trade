import type { ReactNode } from "react";

import { AppShell, LoginScreen } from "@/components/app-shell";

export function PageShell({
  authenticated,
  children,
}: {
  authenticated: boolean;
  children?: ReactNode;
}) {
  if (!authenticated) {
    return <LoginScreen />;
  }

  return <AppShell>{children}</AppShell>;
}
