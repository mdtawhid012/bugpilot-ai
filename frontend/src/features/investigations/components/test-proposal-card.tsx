import { EvidenceCard } from "./evidence-card";
import type { EvidenceItem } from "@/types/api.types";

export function TestProposalCard({ evidence }: { evidence: EvidenceItem }) {
  return (
    <div>
      <p className="field-help">Proposed test only; it was not executed.</p>
      <EvidenceCard evidence={evidence} />
    </div>
  );
}
