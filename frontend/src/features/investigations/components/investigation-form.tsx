"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { AlertCircle, ArrowRight } from "lucide-react";
import { apiRequest } from "@/lib/api/client";
import { ApiRequestError } from "@/lib/api/errors";
import { endpoints } from "@/lib/api/endpoints";
import { utf8ByteLength } from "@/lib/utils";
import type { CreateInvestigationResponse, FixtureListResponse } from "@/types/api.types";
import { investigationSchema } from "../schemas/investigation.schema";
import type { InvestigationFormValues } from "../types/investigation.types";

export function InvestigationForm() {
  const router = useRouter();
  const [fixturesLoading, setFixturesLoading] = useState(true);
  const [fixtures, setFixtures] = useState<FixtureListResponse["items"]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const idempotencyKey = useRef(crypto.randomUUID());
  const submittedFingerprint = useRef<string | null>(null);

  const form = useForm<InvestigationFormValues>({
    resolver: zodResolver(investigationSchema),
    defaultValues: { fixtureId: "", report: "" },
  });
  const report = form.watch("report");
  const reportBytes = utf8ByteLength(report);

  useEffect(() => {
    apiRequest<FixtureListResponse>(endpoints.fixtures)
      .then((response) => setFixtures(response.items))
      .catch((error: unknown) => setSubmitError(error instanceof Error ? error.message : "Unable to load fixtures."))
      .finally(() => setFixturesLoading(false));
  }, []);

  async function submit(values: InvestigationFormValues) {
    setSubmitError(null);
    const fingerprint = JSON.stringify({ fixtureId: values.fixtureId, report: values.report });
    if (submittedFingerprint.current !== fingerprint) {
      submittedFingerprint.current = fingerprint;
      idempotencyKey.current = crypto.randomUUID();
    }
    if (reportBytes > 16 * 1024) return;
    const body = JSON.stringify({ fixture_id: values.fixtureId, report: values.report });
    if (new TextEncoder().encode(body).length > 32 * 1024) {
      setSubmitError("The complete JSON request exceeds the 32 KiB limit.");
      return;
    }

    setSubmitting(true);
    try {
      const csrf = await apiRequest<{ token: string }>(endpoints.csrf);
      const created = await apiRequest<CreateInvestigationResponse>(endpoints.investigations, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey.current,
          "X-CSRF-Token": csrf.token,
        },
        body,
      });
      router.push(`/investigations/${created.id}`);
    } catch (error) {
      if (error instanceof ApiRequestError) setSubmitError(`${error.apiError.message} (${error.apiError.code})`);
      else setSubmitError("The investigation could not be submitted. Retry with the same form data.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card form-card" onSubmit={form.handleSubmit(submit)} noValidate>
      <div className="form-grid">
        {submitError ? <div className="error-state" role="alert"><AlertCircle size={16} /><p>{submitError}</p></div> : null}
        <div className="field">
          <label htmlFor="fixtureId">Fixture</label>
          <select id="fixtureId" className="input" disabled={fixturesLoading} {...form.register("fixtureId")}>
            <option value="">{fixturesLoading ? "Loading fixtures…" : "Select a fixture"}</option>
            {fixtures.map((fixture) => <option key={fixture.id} value={fixture.id}>{fixture.title} · {fixture.revision}</option>)}
          </select>
          {form.formState.errors.fixtureId ? <span className="field-error">{form.formState.errors.fixtureId.message}</span> : null}
        </div>

        <div className="field">
          <label htmlFor="report">Bug report</label>
          <textarea id="report" className="textarea" placeholder="Describe the observed behavior and the expected behavior…" {...form.register("report")} />
          <div className="field-help" style={{ display: "flex", justifyContent: "space-between" }}>
            <span>Stage 1 report limit: 16 KiB UTF-8</span>
            <span className={reportBytes > 16 * 1024 ? "field-error" : "byte-count"}>{reportBytes.toLocaleString()} / 16384 bytes</span>
          </div>
          {form.formState.errors.report ? <span className="field-error">{form.formState.errors.report.message}</span> : null}
        </div>

        <div className="form-footer">
          <span className="field-help">A new submission receives one idempotency key. Retrying preserves it for this form.</span>
          <button className="button" type="submit" disabled={submitting || fixturesLoading}>
            {submitting ? "Submitting…" : "Start investigation"}<ArrowRight size={16} />
          </button>
        </div>
      </div>
    </form>
  );
}
