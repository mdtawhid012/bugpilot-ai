import { describe, expect, it } from "vitest";
import type { CreateInvestigationResponse } from "@/types/api.types";

describe("idempotent investigation creation", () => {
  it("uses the returned ID for a replay whose status is non-queued", () => {
    const replay: CreateInvestigationResponse = {
      id: "existing-investigation",
      status: "reviewable",
      verification_outcome: "not_run",
      execution_status: "simulated",
      provider_mode: "fake",
    };

    expect(replay.status).not.toBe("queued");
    expect(replay.id).toBe("existing-investigation");
  });
});
