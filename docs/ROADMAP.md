# BugPilot AI — Staged Development Roadmap

**Status:** Proposed; no implementation until architecture approval

**Date:** 2026-11-05

The roadmap separates a low-cost local prototype from a hosted pilot and multi-tenant SaaS. It assumes `ARCHITECTURE.md`; controls are proposals until implemented and tested.

## Stages

| Stage | Scope | Exit criteria |
|---|---|---|
| **0. Approval and contract freeze** | Approve local boundaries, API/state/evidence schemas, fixture strategy, verification outcomes, dependency policy, local-browser protection, and execution gates. | Contract decisions recorded; architect, backend, frontend, AI and security owners agree or note residual questions. |
| **1. Local end-to-end vertical slice** | FastAPI modular-monolith core, SQLite, curated fixture manifest, fake provider, simulated runner, local in-process bounded coordinator, minimal Next.js UI. No auth, GitHub, live model, target dependency installation, or target-code execution. | Developer submits report for fixture, sees persisted state/events, fake hypotheses/proposals and explicit simulated/not-run state; backend/frontend/AI/security acceptance tests pass. Restart marks unfinished runs `interrupted`; no false resume. |
| **2. Read-only Python repository context** | Explicit safe snapshot interface, Python/pytest detection, bounded AST/symbol/traceback context and provenance. No execution. | Containment, symlink, secret/config exclusions and deterministic context tests pass. |
| **3. Provider-backed proposal mode** | One provider adapter, approved data policy, opt-in credentials outside repo, schema-validated hypotheses/tests/patch proposals, budgets and evaluation fixtures. | Refusal/malformed/timeout/cost/prompt-injection tests pass; UI distinguishes fixture output from live provider/model origin. |
| **4. Isolated pytest execution pilot** | Curated dependency profile/wheelhouse, disabled plugin autoload, runner-owned config, fixed test harness, separate disposable runner, baseline and patch suite phases. | Fail-closed execution gate is enforced; independent security evidence matrix passes for network, metadata, filesystem, dependency, plugin, resource, timeout, worker-loss and cleanup behavior. |
| **5. Hosted single-tenant pilot** | Selected hosting, managed PostgreSQL, outbox/queue, private artifacts, secrets management, approved provider and limited invited users/repositories. GitHub read integration only if needed. | Privacy, auth, recovery, quota and operations checks pass; execution remains separately gated until Stage 4. |
| **6. GitHub App and explicit PR flow** | Repository access/webhooks; later approval bound to exact patch/base and PR creation with least privilege. | Signature/deduplication/access/race/idempotency and audit tests pass. PR writes remain disabled until sign-off. |
| **7. Multi-tenant SaaS** | Identity/workspaces/roles, tenant isolation, quotas, retention/deletion, billing, SLO/HA, support and abuse response. | Security/operations sign-off; tenant, recovery, deletion and cost controls validated. |
| **8. Expansion** | Additional language adapters, retrieval/embedding, SSE or scale improvements justified by benchmarks. | Conformance/security tests for new capability; measured benefit justifies complexity. |

## Stage 1 — first implementation milestone

### Exact deliverables and ownership

- **solution-architect (contract owner):** freeze Stage 1 endpoint/DTO/error/event schemas, transitions, fixture manifest format, origin/evidence model, module boundaries and acceptance tests. Resolve API disagreements before implementation.
- **backend-engineer:** implement `api`, `investigations`, `persistence` (SQLite), fixture catalog and local bounded coordinator. Endpoints: `GET /api/v1/csrf`; `GET /api/v1/fixtures`; `POST /api/v1/investigations`; `GET /api/v1/investigations/{id}`; `GET /api/v1/investigations/{id}/events?after=N`; `POST /api/v1/investigations/{id}/cancel`; `GET /api/v1/health`. Same idempotency key+same normalized body returns original result; different body conflicts, with unique reservation in the create transaction. `after` is exclusive; event sequence is monotonic per investigation.
- **frontend-engineer:** create fixture/report form and investigation page; use same-origin proxy; display true API state, generated fixture output and simulated/not-run notice; polling at 1s backing off to 5s, dedupe event sequence, stop on terminal state, preserve last-known data visibly as stale on transport errors. Cover loading/error/empty/validation/not-found/cancel/accessibility states.
- **ai-agent-engineer:** define provider-neutral protocol/output schema and deterministic fake provider only; attach `producer_kind=fake_provider`, producer version and source fixture ID. Add invariants preventing provider/fake output from changing state or verification.
- **security-engineer:** review local bind/Host/Origin/CSRF, fixture-root containment, local data directory, fake-vs-real adapter boundary and execution-disabled behavior. Define security evidence matrix before any real execution.
- **Reviewers:** backend-reviewer and frontend-reviewer inspect diffs read-only after implementation; they do not implement. Implementation owners address accepted findings.

### API contract and state

`POST` body `{fixture_id,report}` (16 KiB UTF-8 report limit, 32 KiB JSON body limit), `Idempotency-Key` and `X-CSRF-Token` required; returns `202` only after SQLite transaction commits `{id,status:"queued",verification_outcome:"not_run",execution_status:"not_requested",provider_mode:"fake"}`. Same-key/same-normalized-body requests, including concurrent duplicates, atomically resolve to one investigation; a changed body conflicts. Status transitions: `queued -> analyzing|cancelled|interrupted`; `analyzing -> reviewable|failed|cancelled|interrupted`. `reviewable` is terminal for this investigation; Stage 1 has no retry endpoint. Repeated cancel on cancelled returns current state; cancel on another terminal state is `409`.

If cancel and completion race, an atomic status/version compare-and-set decides the winner. If cancellation commits first, the coordinator's durable cancellation flag prevents later transitions/evidence writes; a late result is discarded. If completion wins, cancel returns `409` with current terminal state. On restart, mark queued/running investigations `interrupted`; do not resume implicitly.

Event fields: monotonic `sequence`, `type`, `created_at`, bounded `data` with safe codes and evidence IDs. Event append and state transition are atomic in the `investigations` module. `after=N` is exclusive. Evidence has `content_type` (`generated`, `observed`, `simulated`), `producer_kind` (`fixture`, `fake_provider`, `simulated_runner`) and producer version; fake-provider proposals also identify the source fixture. Stage 1 verification outcome remains `not_run`; execution status may be `simulated`, which is not a verification outcome or actual execution.

Investigation detail response fields: `{id,status,verification_outcome,execution_status,fixture:{id,title,revision},created_at,updated_at,latest_event_sequence,evidence:[EvidenceItem]}`. Each evidence item is `{id,kind,content_type,producer_kind,producer_version,source_fixture_id?,title,summary,source_ref?}`; `source_ref` contains relative path, line range, revision and content digest only. Event response `{items:[{sequence,type,created_at,data}],next_cursor}`. Stable errors use `{code,message,request_id}`. `GET /api/v1/csrf` returns a per-process token through the same-origin proxy; the browser sends `X-CSRF-Token` for create/cancel.

### Acceptance and tests

1. Fixture IDs come only from a server-owned manifest. Resolve beneath a canonical trusted root using race-resistant no-follow file access (or equivalent platform-safe handle-relative open); reject traversal, symlink/reparse points, special files and unknown IDs; user input is never joined into a filesystem path.
2. App binds to IPv4/IPv6 loopback, uses a same-origin Next proxy that strips forwarded headers, exact Host and non-null Origin checks, same-origin Fetch Metadata, and a CSRF token endpoint/header. Test the actual proxied flow, hostile/missing/null Origin, invalid Host, forged forwarding headers, CSRF failure and LAN bind prevention.
3. Store SQLite/artifacts in per-OS application-data paths with owner-only permissions (Windows `%LOCALAPPDATA%\BugPilotAI\prototype` with inheritance disabled and current-user/system ACL; macOS `~/Library/Application Support/BugPilotAI/prototype`; Linux `${XDG_DATA_HOME:-~/.local/share}/bugpilot-ai/prototype`, owner-only directories/files). Keep outside repository/webroot/synced/shared folders; verify effective permissions and that report/source data is neither logged nor served as arbitrary files.
4. Create validates report/body limits, idempotency and fixture; key reservation, investigation and initial event commit atomically. Test sequential and concurrent same-key/body replay yields one ID; changed-body conflict; event order/exclusive cursor; cancel/completion race; late result fence; restart interruption.
5. UI renders actual API data, polls with bounded backoff and stops on terminal; network failure is visibly stale/transport error, not investigation failure.
6. Fake provider outputs carry `producer_kind=fake_provider`, version and source fixture; simulated runner is `simulated`, verification is `not_run`; tests prove impossible to reach `verified_patch`.
7. No target dependencies are installed, no target code is executed, no external service is contacted, and no credentials are needed. Fixture replacement between validation/open must not escape the manifest root.

### Remain disabled

Target repository filesystem access beyond curated fixture manifest; pytest of target repositories; dynamic pip installation; actual LLM calls; GitHub App/webhooks/issues; hosted auth/workspaces; Redis/Postgres/object storage; PR writes; billing. These remain deferred to later stages and gates.

## Cross-agent workflow

Architect publishes contracts first. Backend, frontend and AI tasks are non-overlapping and use explicit interfaces. Security independently reviews boundaries. Review agents are read-only and act only after changes exist. The main Copilot session provides each agent the necessary context, resolves findings and reports checks actually run. No automatic agent collaboration/context sharing is assumed.
