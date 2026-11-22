import Link from "next/link";
import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { EmptyState } from "@/components/shared/empty-state";

export default function InvestigationsPage() {
  return (
    <>
      <AppHeader title="Investigations" actions={<Link className="button" href="/investigations/new">New investigation</Link>} />
      <PageContainer>
        <EmptyState
          title="Investigation listing unavailable"
          description="The Stage 1 backend does not expose a list-investigations endpoint or investigation pagination. This UI will not invent records or statuses. Open a known investigation ID or create a new investigation."
          action={<Link className="button secondary" href="/investigations/new">Create investigation</Link>}
        />
      </PageContainer>
    </>
  );
}
