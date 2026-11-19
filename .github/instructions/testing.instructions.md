---
applyTo: "**/*test*.py,**/tests/**/*.py,**/*.spec.ts,**/*.test.ts,**/*.spec.tsx,**/*.test.tsx"
---

# Testing conventions

- Read existing test configuration, fixtures, and neighboring tests before adding or changing tests. Use the repository's configured runner and documented commands; if none exist, say so rather than installing tooling unless requested.
- Test observable behavior and meaningful failure cases, not implementation details. Keep unit tests isolated; reserve integration tests for real boundaries such as database transactions or API contracts.
- Make tests deterministic: control clocks, randomness, network calls, and external services with the project's established fakes or mocks. Never require real credentials or contact production services.
- Cover relevant validation, authorization, error handling, retries/idempotency, and cleanup paths. Check that failed work is not represented as a successful result.
- For AI features, assert schemas, tool permissions, state transitions, and evidence handling with deterministic fixtures; do not assert that free-form model reasoning is factual.
- For isolated execution, test timeout, resource-limit, network-denial, artifact, and cleanup behavior at the available safe boundary; do not execute untrusted repository code on the host as a shortcut.
- Report exactly which tests ran and whether they passed. Do not claim coverage or verification from a test that was not executed.
