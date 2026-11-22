"use client";

import { useState } from "react";
import { RotateCw, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { ErrorState } from "@/components/shared/error-state";
import { InvestigationOverview } from "./investigation-overview";
import { HypothesisCard } from "./hypothesis-card";
import { TestProposalCard } from "./test-proposal-card";
import { PatchProposalCard } from "./patch-proposal-card";
import { EvidenceCard } from "./evidence-card";
import { useInvestigation } from "../hooks/use-investigation";
import { useCancelInvestigation } from "../hooks/use-cancel-investigation";
import { isTerminalStatus } from "@/lib/api/errors";
import { applyCancellationOutcome } from "@/lib/cancellation";

export function InvestigationDetailView({ id }: { id: string }) {
  const { investigation, events, loading, stale, error, refresh, setInvestigation } = useInvestigation(id);
  const [confirmCancel, setConfirmCancel] = useState(false);
  const { cancel, submitting, error: cancelError } = useCancelInvestigation((updated) => setInvestigation(updated));

  if (loading && !investigation) return <LoadingSkeleton rows={5} />;
  if (error && !investigation) return <ErrorState title="Investigation unavailable" message={error} retry={refresh} />;
  if (!investigation) return null;

  const hypotheses = investigation.evidence.filter((item) => item.kind === "hypothesis");
  const tests = investigation.evidence.filter((item) => item.kind === "test_proposal");
  const patches = investigation.evidence.filter((item) => item.kind === "patch_proposal");
  const sources = investigation.evidence.filter((item) => item.kind === "source_reference");
  const execution = investigation.evidence.filter((item) => item.kind === "execution_result");

  async function handleCancel() {
    try {
      const outcome = await cancel(id);
      setConfirmCancel(false);
      setInvestigation((current) => applyCancellationOutcome(current, outcome));
    } catch {
      setConfirmCancel(false);
    }
  }

  return (
    <div>
      {stale ? <div className="stale-banner" role="status">Live data is stale. Last-known investigation state is retained until the next successful refresh.</div> : null}
      {cancelError ? <div className="error-state" role="alert">{cancelError}</div> : null}
      <div className="section-header">
        <div>
          <p className="eyebrow">Investigation</p>
          <h2>{investigation.id}</h2>
        </div>
        <div className="header-actions">
          <Button className="secondary" onClick={refresh} aria-label="Refresh investigation"><RotateCw size={16} />Refresh</Button>
          {!isTerminalStatus(investigation.status) ? (
            confirmCancel ? (
              <>
                <Button className="danger" onClick={handleCancel} disabled={submitting}><Square size={15} />{submitting ? "Cancelling…" : "Confirm cancel"}</Button>
                <Button className="secondary" onClick={() => setConfirmCancel(false)}>Keep running</Button>
              </>
            ) : (
              <Button className="danger" onClick={() => setConfirmCancel(true)}>Cancel investigation</Button>
            )
          ) : null}
        </div>
      </div>

      <InvestigationOverview investigation={investigation} />

      <section className="evidence-section">
        <div className="section-header"><div><h2>Hypotheses</h2><p>Generated possibilities, not confirmed root causes.</p></div></div>
        <div className="evidence-grid">{hypotheses.length ? hypotheses.map((item) => <HypothesisCard key={item.id} evidence={item} />) : <Card className="detail-card">No hypotheses are available yet.</Card>}</div>
      </section>

      <section className="evidence-section">
        <div className="section-header"><div><h2>Test proposals</h2><p>Proposed tests only; Stage 1 does not execute tests.</p></div></div>
        <div className="evidence-grid">{tests.length ? tests.map((item) => <TestProposalCard key={item.id} evidence={item} />) : <Card className="detail-card">No test proposals are available yet.</Card>}</div>
      </section>

      <section className="evidence-section">
        <div className="section-header"><div><h2>Patch proposals</h2><p>Proposed changes only; no patch is applied or verified.</p></div></div>
        <div className="evidence-grid">{patches.length ? patches.map((item) => <PatchProposalCard key={item.id} evidence={item} />) : <Card className="detail-card">No patch proposals are available yet.</Card>}</div>
      </section>

      <section className="evidence-section">
        <div className="section-header"><div><h2>Evidence and execution</h2><p><strong>Execution: {investigation.execution_status}</strong>. Verification outcome: <strong>{investigation.verification_outcome}</strong>. Simulated output is not test execution.</p></div></div>
        <div className="evidence-grid">
          {[...sources, ...execution].map((item) => <EvidenceCard key={item.id} evidence={item} />)}
        </div>
      </section>

      {events.length ? (
        <section className="evidence-section">
          <div className="section-header"><div><h2>Timeline</h2><p>Persisted events received during this session.</p></div></div>
          <Card className="detail-card">
            <div className="evidence-grid">
              {events.map((event) => <div key={event.sequence} className="meta-item"><span>Sequence {event.sequence}</span><strong>{event.type}</strong></div>)}
            </div>
          </Card>
        </section>
      ) : null}
    </div>
  );
}
