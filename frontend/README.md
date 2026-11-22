# BugPilot AI Frontend

Next.js App Router frontend for the Stage 1 BugPilot backend. It communicates only through same-origin Next.js Route Handlers.

## Requirements

- Node.js 22.x
- npm 11.x
- FastAPI backend running locally

The frontend package versions are pinned in `package.json`, and `package-lock.json` is committed. The lockfile currently resolves packages from public `registry.npmjs.org`. The repository does not declare an approved npm registry or credentials, so an approved clean installation cannot be claimed. Do not silently replace or delete the lockfile to work around that policy.

## Environment

Copy `.env.example` and configure server-only values:

```powershell
Copy-Item .env.example .env.local
```

```sh
cp .env.example .env.local
```

- `BUGPILOT_BACKEND_ORIGIN`: exact loopback FastAPI origin, default intended as `http://127.0.0.1:8000`
- `BUGPILOT_FRONTEND_ORIGIN`: exact frontend origin, default `http://127.0.0.1:3000`

Neither variable is exposed as `NEXT_PUBLIC_*`.

## Install and Run

From `frontend/`, after an approved npm source and lockfile policy are available:

```powershell
npm ci
npm run dev
```

```sh
npm ci
npm run dev
```

The frontend binds loopback in the npm script. Run FastAPI separately from `backend/`:

```powershell
python -m app.server
```

## Proxy

Browser requests use `/api/v1/*`. Next.js Route Handlers send them to `BUGPILOT_BACKEND_ORIGIN` with forwarding headers removed. Mutations set exact loopback `Origin` and `Sec-Fetch-Site: same-origin`; browser-provided CSRF and idempotency headers are forwarded explicitly.

## Tests and Checks

```powershell
npm run typecheck
npm run lint
npm run test
npm run build
```

The tests cover UTF-8 validation, terminal polling status, proxy browser mutation validation, cancellation outcomes, event deduplication and polling backoff. Package scripts and lockfile reproducibility cannot be fully approved until dependencies are installed through an approved source.

## IPv4 and IPv6

Next.js CLI does not expose a supported dual-host startup mode in these scripts. IPv4 and IPv6 are therefore separate explicit scripts: `npm run dev`/`npm run start` bind 127.0.0.1, and `npm run dev:ipv6`/`npm run start:ipv6` bind ::1. Never use 0.0.0.0 or ::.

## UI Components

The UI intentionally uses small custom primitives under `src/components/ui`. These primitives are not shadcn-generated components, and shadcn tooling is not a runtime dependency.

## Backend Limitations

Stage 1 has no list-investigations or aggregate statistics endpoint. The overview and investigation list therefore do not fabricate counts or records. Detail and events remain available by direct ID or successful creation response.
