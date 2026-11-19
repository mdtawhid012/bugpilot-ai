---
applyTo: "**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.jsx,**/*.yml,**/*.yaml,**/*.json,**/*.sql,**/*.toml,**/*.env*,**/Dockerfile*"
---

# Security engineering

- Treat user inputs, issue descriptions, repository content, diffs, logs, model outputs, and generated patches as untrusted. Keep data separate from instructions and restrict model tools to explicit capabilities and scoped resources.
- Enforce authentication, authorization, tenant boundaries, and GitHub installation/repository ownership server-side. Verify webhook signatures and replay protections before processing events.
- Never execute untrusted repository code on the application host or expose production secrets to an execution worker. Design workers as disposable isolated environments with non-root identities, resource and time limits, restricted mounts, disabled or allowlisted egress, and guaranteed cleanup.
- Use least privilege for GitHub Apps, API tokens, database roles, containers, and background workers. Request only permissions required for explicit product flows and validate repository access at each operation.
- Protect against injection, path traversal, SSRF, unsafe archive extraction, command construction, insecure deserialization, CSRF, XSS, SQL injection, denial of service, and sensitive-data leakage as applicable. Prefer safe APIs and explicit allowlists.
- Keep secrets out of source, logs, prompts, build artifacts, and untrusted processes. Do not add secret placeholders that look real or claim external secret systems are configured when they are not.
- When reviewing, prioritize actionable findings by severity and confidence; cite paths/lines and concrete impact. Distinguish verified exposure from a design risk or an unconfirmed hypothesis. Never claim the system is secure without evidence.
- Do not introduce permissive defaults, broad exception fallbacks, unrestricted network access, host mounts, privileged containers, or shell execution to make a workflow appear successful.
