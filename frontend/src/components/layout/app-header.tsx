import type { ReactNode } from "react";

export function AppHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">BugPilot workspace</p>
        <h1>{title}</h1>
      </div>
      {actions ? <div className="header-actions">{actions}</div> : null}
    </header>
  );
}
