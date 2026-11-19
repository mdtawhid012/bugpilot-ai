---
name: backend-development
description: Guides implementation and review of BugPilot AI Python backends, especially FastAPI REST endpoints, Pydantic contracts, SQLAlchemy persistence and transactions, pytest tests, and consistent error handling. Use when working on backend code.
---

# Backend development workflow

1. Inspect the repository layout, dependency/configuration files, nearby endpoints and tests, and architect-approved API/data contracts. Confirm what actually exists before choosing a pattern.
2. Keep the modular monolith's domain and infrastructure boundaries consistent with existing code. Place HTTP concerns at the FastAPI boundary; keep request/response schemas explicit and use Pydantic validation for external data.
3. Design REST endpoints with appropriate methods, status codes, stable error shapes, authorization checks, and documented pagination/filter semantics where needed. Do not expose ORM models directly as public contracts.
4. Implement SQLAlchemy queries using parameterized ORM/Core expressions. Define transaction ownership and rollback behavior; consider concurrency, indexes, query count, pagination, and session lifecycle. Match synchronous or asynchronous access to the configured driver.
5. Centralize configuration through established typed settings and dependency patterns. Do not invent secret values or print secrets.
6. Handle expected validation, not-found, conflict, dependency, and internal failures explicitly. Return safe client errors and retain useful, redacted structured logs with request/job correlation where available.
7. Add focused pytest cases for success, validation, authorization, transaction behavior, and relevant failure paths. Reuse existing fixtures and test conventions; never require live credentials or production services.
8. Run the smallest available relevant checks and report exact outcomes. If no backend or test setup exists, state that rather than claiming verification or adding tooling without authorization.
