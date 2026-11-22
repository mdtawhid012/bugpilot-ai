import type { ReactNode } from "react";

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="empty-state" role="status">
      <div className="empty-mark" aria-hidden="true">BP</div>
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </div>
  );
}
