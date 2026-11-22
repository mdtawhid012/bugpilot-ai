import { Badge } from "@/components/ui/badge";
import type { EvidenceItem } from "@/types/api.types";

export function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  const producerLabel = evidence.producer_kind === "fake_provider"
    ? "Deterministic fake AI output"
    : evidence.producer_kind === "simulated_runner"
      ? "Simulated execution"
      : evidence.producer_kind;

  const displayedSummary = evidence.kind === "patch_proposal"
    ? evidence.summary.split("\nDiff proposal:")[0]
    : evidence.summary;

  return (
    <article className="card evidence-card">
      <div className="evidence-card-header">
        <h3>{evidence.title}</h3>
        <Badge>{evidence.kind.replaceAll("_", " ")}</Badge>
      </div>
      <p className="evidence-summary">{displayedSummary}</p>
      <div className="provenance" aria-label="Evidence provenance">
        <span>Content: {evidence.content_type}</span>
        <span>Producer: {producerLabel}</span>
        <span>Version: {evidence.producer_version}</span>
        {evidence.source_fixture_id ? <span>Fixture: {evidence.source_fixture_id}</span> : null}
        {evidence.source_ref ? (
          <span>
            Source: {evidence.source_ref.path}:{evidence.source_ref.line_start}–{evidence.source_ref.line_end}
            <br />Revision {evidence.source_ref.revision} · SHA-256 {evidence.source_ref.content_hash.slice(0, 12)}…
          </span>
        ) : null}
      </div>
    </article>
  );
}
