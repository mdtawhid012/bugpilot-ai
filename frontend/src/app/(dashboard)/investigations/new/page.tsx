import { AppHeader } from "@/components/layout/app-header";
import { PageContainer } from "@/components/layout/page-container";
import { InvestigationForm } from "@/features/investigations/components/investigation-form";

export default function NewInvestigationPage() {
  return (
    <>
      <AppHeader title="New investigation" />
      <PageContainer><InvestigationForm /></PageContainer>
    </>
  );
}
