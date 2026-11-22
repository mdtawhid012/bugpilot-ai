# BugPilot AI

BugPilot AI is a Stage 1 local investigation product. The backend is a fixture-only Python/FastAPI application; the frontend is a Next.js App Router dashboard that communicates through same-origin Route Handlers.

## Run Locally

Backend setup and commands are documented in `backend/README.md`. Frontend setup and commands are documented in `frontend/README.md`.

The backend and frontend bind to loopback only. Mutations pass through the Next.js proxy and require the exact configured frontend Origin, same-origin Fetch Metadata, and CSRF token.

## Stage 1 Boundaries

- Curated fixtures only
- Deterministic fake AI provider
- Simulated execution
- No target-code or target-pytest execution
- No external LLM or GitHub integration
- No PostgreSQL, Redis, auth, billing, or PR creation

The frontend deliberately does not invent investigation-list or aggregate endpoints that are not present in the backend contract.
