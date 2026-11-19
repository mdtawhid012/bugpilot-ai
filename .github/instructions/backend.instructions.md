---
applyTo: "**/*.py"
---

# Backend engineering

- Inspect the existing application layout and dependency versions before proposing module locations or APIs. Keep a modular monolith by default and follow established boundaries; do not scaffold a new service just because the intended stack mentions FastAPI.
- Keep HTTP routing, request/response schemas, application use cases, persistence, and infrastructure concerns separated where the existing project benefits from it. Avoid layers that only forward calls.
- Define FastAPI endpoints with explicit HTTP methods, status codes, response models, pagination/filter semantics where applicable, and stable error behavior. Validate untrusted input at the boundary with Pydantic; do not expose ORM entities as public response contracts.
- Keep SQLAlchemy operations and transaction boundaries explicit. Use parameterized ORM/Core expressions, avoid N+1 queries, and ensure failures roll back. Match sync or async database usage to the configured driver consistently.
- Enforce authentication and authorization on the server for every protected resource and verify tenant/installation ownership at the data boundary.
- Use dependency injection for shared infrastructure only when it improves testability or lifecycle management. Keep configuration typed and load secrets from configured environment/secret providers, never source code.
- Log structured operational events with request or job correlation where available. Redact secrets and sensitive payloads; do not turn expected client errors into noisy stack traces.
- Add focused pytest coverage for success, validation, authorization, persistence/transaction behavior, and relevant failure paths. Reuse existing fixtures and test commands; do not invent commands when project tooling is absent.
