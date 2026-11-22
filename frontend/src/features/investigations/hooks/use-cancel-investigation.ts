"use client";

import { useState } from "react";
import type { CancelOutcome, CancellationStateResponse, InvestigationDetail } from "@/types/api.types";
import { ApiRequestError } from "@/lib/api/errors";
import { apiRequest } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

export function useCancelInvestigation(onUpdated: (detail: InvestigationDetail) => void) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancel(id: string): Promise<CancelOutcome> {
    setSubmitting(true);
    setError(null);
    try {
      const csrf = await apiRequest<{ token: string }>(endpoints.csrf);
      const state = await apiRequest<CancellationStateResponse>(endpoints.cancel(id), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrf.token,
          "Idempotency-Key": `cancel-${crypto.randomUUID()}`,
        },
        body: "{}",
      });
      setError(null);
      return { kind: "cancelled", state };
    } catch (caught) {
      if (caught instanceof ApiRequestError && caught.status === 409) {
        const detail = await apiRequest<InvestigationDetail>(endpoints.investigation(id));
        onUpdated(detail);
        setError(detail.status === "cancelled"
          ? "The investigation is already cancelled."
          : `Cancellation lost a race to completion; current status is ${detail.status}.`);
        return { kind: "completion_won", detail };
      }
      setError(caught instanceof Error ? caught.message : "Cancellation could not be confirmed.");
      throw caught;
    } finally {
      setSubmitting(false);
    }
  }

  return { cancel, submitting, error };
}
