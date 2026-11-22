import { EvidenceCard } from "./evidence-card";
import type { EvidenceItem } from "@/types/api.types";

export function PatchProposalCard({ evidence }: { evidence: EvidenceItem }) {
  const diff = evidence.summary.match(/Diff proposal:\n([\s\S]*)$/)?.[1];
  return (
    <div>
      <p className="field-help">Patch proposal only; no source file was modified or verified.</p>
      <EvidenceCard evidence={evidence} />
      {diff ? <pre className="diff" aria-label="Proposed code diff">{diff}</pre> : null}
    </div>
  );
}
