---
name: docker-sandbox
description: Guides secure design and assessment of disposable Docker or worker environments for running untrusted BugPilot AI repository code, including isolation, resource limits, networking, timeouts, artifacts, logs, and cleanup. Use when designing execution sandboxes.
---

# Untrusted execution sandbox workflow

1. Map the threat model and trust boundaries first. Repository code, build scripts, package hooks, tests, issue content, and generated patches are hostile. The application host and production credentials are out of bounds.
2. Run work in disposable, non-root workers with a read-only base image where feasible, minimal capabilities, no privileged mode, no host socket, and narrowly scoped temporary workspace mounts. Never mount sensitive host paths.
3. Apply explicit CPU, memory, process-count, disk, output-size, and wall-clock limits. Ensure cancellation and timeout terminate the entire workload and descendants.
4. Deny network egress by default. If a documented use case requires network access, use narrowly scoped controls and account for DNS, metadata endpoints, local services, and exfiltration.
5. Provide no production secrets, source-control credentials, or privileged tokens to untrusted processes. Keep any necessary short-lived credentials out of environment/output when possible, and revoke them promptly.
6. Treat archives and artifacts as untrusted: validate paths and sizes, prevent traversal and symlink escapes, store outside privileged paths, and scan/limit before retrieval.
7. Capture bounded stdout/stderr and structured exit/timeout/resource metadata. Redact sensitive values; do not let untrusted output become trusted prompts or executable instructions.
8. Guarantee cleanup on success, error, cancellation, and worker loss. Make cleanup idempotent and verify workspaces, containers, volumes, and temporary credentials are removed.
9. Test isolation and failure behavior at safe boundaries. Do not claim isolation from configuration alone; require evidence and independent security review.
