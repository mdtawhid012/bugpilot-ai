# BugPilot AI — Proposed Technology Stack and Cost Model

**Status:** Target choices for approval; nothing is installed or configured

**Date:** 2026-11-05

## Local prototype vs hosted stack

| Area | Local prototype | Hosted pilot/SaaS |
|---|---|---|
| UI | Next.js, React, strict TypeScript, Tailwind, shadcn/ui | Same frontend, hosted |
| API/domain | Python/FastAPI/Pydantic modular monolith | Same codebase, API/worker entry points as needed |
| State | SQLite local database; owner-private bounded artifacts | PostgreSQL, migrations, backup/restore |
| Jobs | Bounded in-process coordinator for fake flow; restart marks unfinished work interrupted | Transactional outbox plus durable queue (Redis candidate) and idempotent workers |
| AI | Deterministic fake provider and fixture responses | One selected replaceable LLM provider after data-policy review |
| Repository | Curated fixture IDs only | GitHub/source adapter after authorization stage |
| Execution | Simulated adapter only; arbitrary project execution disabled | Separate hardened disposable runner |
| Dependencies | Developer setup may download BugPilot dependencies from an approved package source using a reviewed lockfile; no target repository dependencies | Trusted curated runtime and hash/provenance-checked wheels; no target repo installs |
| Identity/integration | Single local developer; no login/GitHub | Explicit identity and GitHub App policies, introduced by stage |
| Operations | Local logs and tests | Secret manager, monitoring, retention, quotas and incident response |

The prototype intentionally needs no Postgres, Redis, hosted artifact storage, auth provider, GitHub App, billing, cloud accounts or paid model API.

## Dependency and pytest policy

Developer setup may download **BugPilot's own** dependencies from an approved package source using a reviewed pinned lockfile. This setup-time allowance does not authorize external-service contact at Stage 1 runtime or installing dependencies from target repositories.

Stage 1 runtime must not contact external services. It does not download target dependencies, call external LLM APIs, contact GitHub, execute target repository code, or run target pytest suites. Later Stage 3 may add provider-backed proposals under an approved data policy; Stage 4 may add execution only after its security gates. Later execution supports only reviewed Python dependency profiles pinned by version and hash. Prefer approved binary wheels from trusted sources with provenance review, vulnerability review, SBOM/attestation where available, and update/revocation ownership. A hash proves artifact identity, not that its code is benign. Build approved wheelhouses in a separate disposable unprivileged builder, with no production credentials and restricted network. Reject source distributions by default; any exceptional source build is treated as hostile and requires isolated build/review before promotion.

Runner has deny-by-default network access and uses immutable prebuilt runtime/wheelhouse; it never runs `pip install` against repository requirements or package indexes. Missing dependencies are `setup_failure`. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; runner-owned pytest config and fixed args; reject repository plugin options and permit only literal statically verifiable `pytest_plugins` declarations for approved plugins. Reject dynamic/indirect/uninspectable registrations. Do not trust repository config as command authority. `conftest.py`, tests and package code remain hostile executable code inside the isolated boundary.

## Version and tooling policy

No versions are pinned yet. At approved bootstrap choose supported stable Python/Node, Next.js/React, FastAPI/Pydantic, SQLAlchemy/DB drivers, pytest and frontend test tooling; lock dependencies and record actual validated commands. Choose a migration strategy and test hosted PostgreSQL migrations before hosted transition. Local SQLite data is prototype data, not a promised migration source. Pin runner images by digest and approved wheel hashes.

Prefer SQLite locally and PostgreSQL when hosted requirements begin. Keep workflow logic independent of backend-specific query behavior; verify portability through tests rather than assuming a repository abstraction is enough. Polling first; SSE only if measured UX justifies its replay/auth/proxy complexity. Defer embeddings/vector DB and microservices until benchmarks justify them.

## Cost model

Estimates are rough USD planning envelopes, not live quotes or vendor commitments. Validate provider/cloud rates, region and isolation requirements before deployment.

### Local development

- External infrastructure for Stage 1: **$0/month**—local Next/FastAPI, SQLite, curated fixtures, fake provider and simulated executor.
- Developer's existing hardware, electricity and time are excluded; own dependency downloads are incidental.
- Model/API spend: **$0** until provider integration is explicitly enabled.
- `$0` does not permit running arbitrary target code on a developer host or lowering production security.

### Hosted development and pilots

| Stage | Rough monthly spend | Assumptions |
|---|---:|---|
| Hosted development, no customer execution | **$50–$300** | Small app/API and DB, low-volume logs; no always-on isolated runner |
| Invited pilot with gated execution | **$300–$1,500+** | Small hosted services and limited dedicated isolated capacity; VM/microVM and uptime requirements may exceed range |
| Early production (illustrative 100 active users, 1,000 investigations/month) | **$800–$3,500+** | Managed DB/queue/storage, app/worker capacity and isolated runner |
| Growth (illustrative 1,000 active users, 10,000 investigations/month) | **$4,000–$20,000+** | Higher availability, concurrency, retention and monitoring |

Stronger per-job isolation, HA, idle runner capacity, large repositories, long retention, logs/egress and support can increase costs. Do not weaken runner controls to fit an estimate.

Stage 1 LLM costs are zero. Before any live provider or runner is enabled, centrally enforce per-investigation and aggregate caps for calls/retries, token or spend budgets, context bytes, wall time, runner resources, outputs/artifacts and concurrency. The workflow stops before scheduling more work at the cap and records an explicit budget-exhausted outcome; values must be selected from provider/runtime profiles and approved before enablement. Later illustrative arithmetic at `$3/million input` and `$15/million output` tokens (not current price claims): 50k/10k is `$0.30`; 200k/30k is `$1.05`; 600k/80k is `$3.00` per run. At 1,000 runs that is `$300–$3,000`; recalculate using selected provider rates, retries, caching, region and taxes.

Measure actual runner vCPU/memory/time/start overhead, tokens, retries, queue delay, artifact bytes, DB load and monitoring volume before forecasts. Establish per-run/workspace budgets and kill switches before enabling paid integrations.
