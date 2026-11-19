---
name: code-review
description: Provides a systematic, evidence-based review workflow for BugPilot AI changes, covering correctness, security, tests, maintainability, and severity-ranked findings with file and line references. Use when reviewing a diff or implementation.
---

# Code review workflow

1. Read the applicable instructions, diff, and surrounding code. Trace important call paths, interfaces, data ownership, error handling, and test behavior; do not infer correctness from a patch summary.
2. Check for defects that can be reproduced or tied to a concrete execution path: incorrect logic, broken contracts, unsafe authorization/input handling, transaction/race issues, resource leaks, misleading success states, and missing tests for risky behavior.
3. For frontend changes, inspect real API state handling, TypeScript boundaries, accessibility, responsive behavior, and security-sensitive rendering. For backend changes, inspect validation, authorization, transactions, query bounds, and error/logging behavior.
4. For AI and sandbox changes, treat all retrieved content as untrusted; verify tool scope, deterministic stop conditions, distinction between hypotheses and observed evidence, isolation, resource limits, secret exclusion, and cleanup.
5. Report findings ordered by severity: Critical, High, Medium, Low. Include exact file/line references when available, impact, triggering conditions, confidence, and a specific minimal remediation.
6. Report only actionable issues. Exclude stylistic preferences, hypothetical concerns without evidence, and findings already disproven by code/tests. If there are no findings, state what areas were not verified.
7. Never claim checks passed unless actually run. Review findings do not themselves mean the reviewer should edit code; implementation belongs to the responsible engineer unless explicitly delegated.
