import { PageContainer } from "@/components/layout/page-container";
import { AppHeader } from "@/components/layout/app-header";
import { InvestigationDetailView } from "@/features/investigations/components/investigation-detail";

export default async function InvestigationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <AppHeader title="Investigation detail" />
      <PageContainer><InvestigationDetailView id={id} /></PageContainer>
    </>
  );
}
