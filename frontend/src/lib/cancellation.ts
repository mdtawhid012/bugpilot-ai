import type { CancelOutcome, InvestigationDetail } from "@/types/api.types";

export function applyCancellationOutcome(
  current: InvestigationDetail | null,
  outcome: CancelOutcome,
): InvestigationDetail | null {
  if (outcome.kind === "completion_won") return outcome.detail;
  if (!current) return null;
  return {
    ...current,
    status: outcome.state.status,
    execution_status: outcome.state.execution_status,
    verification_outcome: outcome.state.verification_outcome,
    updated_at: outcome.state.updated_at,
    latest_event_sequence: outcome.state.latest_event_sequence,
  };
}
