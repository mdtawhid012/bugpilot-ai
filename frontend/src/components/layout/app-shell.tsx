import type { ReactNode } from "react";
import { AppSidebar } from "./app-sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <AppSidebar />
      <main className="main-content">{children}</main>
    </div>
  );
}
