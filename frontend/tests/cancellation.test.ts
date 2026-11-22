import { describe, expect, it } from "vitest";
import { applyCancellationOutcome } from "@/lib/cancellation";
import type { InvestigationDetail } from "@/types/api.types";

const detail: InvestigationDetail = {
  id: "investigation-1",
  status: "analyzing",
  report: "The report",
  verification_outcome: "not_run",
  execution_status: "not_requested",
  fixture: { id: "discount-calculator", title: "Discount calculator", revision: "synthetic-v1" },
  created_at: "2026-11-22T00:00:00Z",
  updated_at: "2026-11-22T00:00:00Z",
  latest_event_sequence: 2,
  evidence: [],
};

describe("cancellation outcomes", () => {
  it("merges a successful cancellation state", () => {
    const result = applyCancellationOutcome(detail, {
      kind: "cancelled",
      state: {
        id: detail.id,
        status: "cancelled",
        verification_outcome: "not_run",
        execution_status: "not_requested",
        created_at: detail.created_at,
        updated_at: "2026-11-22T00:00:01Z",
        latest_event_sequence: 3,
      },
    });
    expect(result?.status).toBe("cancelled");
    expect(result?.latest_event_sequence).toBe(3);
  });

  it("accepts repeated cancellation as the same cancelled state", () => {
    const result = applyCancellationOutcome(detail, {
      kind: "cancelled",
      state: {
        id: detail.id,
        status: "cancelled",
        verification_outcome: "not_run",
        execution_status: "not_requested",
        created_at: detail.created_at,
        updated_at: detail.updated_at,
        latest_event_sequence: 3,
      },
    });
    expect(result?.status).toBe("cancelled");
  });

  it("uses the latest detail when completion wins", () => {
    const terminal = { ...detail, status: "reviewable" as const, latest_event_sequence: 5 };
    expect(applyCancellationOutcome(detail, { kind: "completion_won", detail: terminal })?.status).toBe("reviewable");
  });
});
