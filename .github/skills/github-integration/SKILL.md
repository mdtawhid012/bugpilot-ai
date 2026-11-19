---
name: github-integration
description: Guides secure BugPilot AI GitHub App integration, installation authorization, webhook processing, repository access, branch/commit/PR creation, and least-privilege permissions. Use when implementing GitHub integration.
---

# GitHub App integration workflow

1. Inspect existing app configuration and approved product/API contracts. Do not assume an App, credentials, webhook endpoint, or permission grant has been configured.
2. Use a GitHub App installation identity for repository operations. Resolve and verify the installation and repository from trusted authenticated context; never accept an arbitrary client-supplied repository identifier as sufficient authorization.
3. Request only necessary repository and organization permissions, separate read from write operations, and document why each permission is needed. Avoid personal access tokens and broad organization access where App installation scope suffices.
4. Verify webhook signatures against the raw request body before processing. Validate event/action, installation and repository ownership, delivery identifiers, timestamps/replay handling, and payload shape. Acknowledge and enqueue safely; make handlers idempotent.
5. Keep App private keys, installation tokens, and webhook secrets in configured secret storage. Mint short-lived tokens only when needed; scope them to authorized installations and never log, commit, prompt with, or expose them to sandboxed code.
6. For branches, commits, and pull requests, use explicit base/head repositories and refs, guard against races, avoid force-pushing over user work, and create reviewable changes with a clear title/body linking evidence and actual verification.
7. Handle rate limits, permission failures, revoked installations, network failures, and partial operations explicitly. Use bounded retries only for safe/idempotent requests; do not disguise failures as success.
8. Test signature rejection, replay/idempotency, installation/repository authorization, permission denial, and partial failures without contacting production or requiring real credentials.
