import Link from "next/link";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";

export default function OverviewPage() {
  return (
    <>
      <AppHeader title="Overview" actions={<Link className="button" href="/investigations/new">New investigation</Link>} />
      <PageContainer>
        <div className="metric-grid">
          {["Total investigations", "Queued", "Analyzing", "Reviewable"].map((label) => (
            <Card className="metric-card" key={label}><span>{label}</span><strong>—</strong></Card>
          ))}
        </div>
        <section className="section">
          <div className="section-header"><div><h2>Recent investigations</h2><p>Available backend data only</p></div></div>
          <EmptyState
            title="No investigation index is available"
            description="Stage 1 exposes creation and direct investigation detail, but does not provide a list or aggregate endpoint. Investigations can be opened only from a known detail URL or a successful creation response."
            action={<Link className="button secondary" href="/investigations/new">Start an investigation</Link>}
          />
        </section>
        <section className="section">
          <Card className="detail-card"><h2>Recent activity</h2><p className="field-help">No activity index endpoint exists in Stage 1. Activity is available through each investigation’s exclusive event cursor after the detail URL is known.</p></Card>
        </section>
      </PageContainer>
    </>
  );
}
