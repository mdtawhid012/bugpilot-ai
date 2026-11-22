import { EvidenceCard } from "./evidence-card";
import type { EvidenceItem } from "@/types/api.types";

export function HypothesisCard({ evidence }: { evidence: EvidenceItem }) {
  return (
    <div>
      <p className="field-help">Generated hypothesis, not a confirmed root cause.</p>
      <EvidenceCard evidence={evidence} />
    </div>
  );
}
