export type InvestigationStatus = "queued" | "analyzing" | "reviewable" | "failed" | "cancelled" | "interrupted";

export type EvidenceKind = "source_reference" | "hypothesis" | "test_proposal" | "patch_proposal" | "execution_result";
export type ContentType = "generated" | "observed" | "simulated";
export type ProducerKind = "fixture" | "fake_provider" | "simulated_runner" | "llm_provider" | "runner_supervisor";

export interface ApiError {
  code: string;
  message: string;
  request_id: string;
}

export interface FixtureItem {
  id: string;
  title: string;
  language: string;
  revision: string;
}

export interface FixtureListResponse {
  items: FixtureItem[];
}

export interface SourceReference {
  path: string;
  line_start: number;
  line_end: number;
  revision: string;
  content_hash: string;
}

export interface EvidenceItem {
  id: string;
  kind: EvidenceKind;
  content_type: ContentType;
  producer_kind: ProducerKind;
  producer_version: string;
  source_fixture_id?: string;
  title: string;
  summary: string;
  source_ref?: SourceReference;
}

export interface InvestigationDetail {
  id: string;
  status: InvestigationStatus;
  report: string;
  verification_outcome: "not_run";
  execution_status: "not_requested" | "simulated";
  fixture: { id: string; title: string; revision: string };
  created_at: string;
  updated_at: string;
  latest_event_sequence: number;
  evidence: EvidenceItem[];
}

export interface CreateInvestigationResponse {
  id: string;
  status: InvestigationStatus;
  verification_outcome: "not_run";
  execution_status: "not_requested" | "simulated";
  provider_mode: "fake";
}

export interface CancellationStateResponse {
  id: string;
  status: InvestigationStatus;
  verification_outcome: "not_run";
  execution_status: "not_requested" | "simulated";
  created_at: string;
  updated_at: string;
  latest_event_sequence: number;
}

export type CancelOutcome =
  | { kind: "cancelled"; state: CancellationStateResponse }
  | { kind: "completion_won"; detail: InvestigationDetail };

export interface InvestigationEvent {
  sequence: number;
  type: string;
  created_at: string;
  data: Record<string, unknown>;
}

export interface EventPageResponse {
  items: InvestigationEvent[];
  next_cursor: number | null;
}
