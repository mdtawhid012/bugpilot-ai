import { StatusBadge } from "@/components/shared/status-badge";
import { Card } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { InvestigationDetail } from "@/types/api.types";

export function InvestigationOverview({ investigation }: { investigation: InvestigationDetail }) {
  return (
    <div className="detail-grid">
      <div className="detail-column">
        <Card className="detail-card">
          <h2>Original report</h2>
          <pre>{investigation.report}</pre>
        </Card>
        <Card className="detail-card">
          <h2>Fixture</h2>
          <div className="meta-grid">
            <div className="meta-item"><span>Name</span><strong>{investigation.fixture.title}</strong></div>
            <div className="meta-item"><span>Revision</span><strong>{investigation.fixture.revision}</strong></div>
          </div>
        </Card>
      </div>
      <aside className="detail-column">
        <Card className="detail-card">
          <h2>Lifecycle</h2>
          <div className="meta-grid">
            <div className="meta-item"><span>Status</span><StatusBadge status={investigation.status} /></div>
            <div className="meta-item"><span>Execution</span><strong>{investigation.execution_status}</strong></div>
            <div className="meta-item"><span>Verification</span><strong>{investigation.verification_outcome}</strong></div>
            <div className="meta-item"><span>Created</span><strong>{formatDate(investigation.created_at)}</strong></div>
            <div className="meta-item"><span>Updated</span><strong>{formatDate(investigation.updated_at)}</strong></div>
          </div>
        </Card>
      </aside>
    </div>
  );
}
