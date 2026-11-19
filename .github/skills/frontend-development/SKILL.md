---
name: frontend-development
description: Guides BugPilot AI Next.js and React frontend work, including reusable components, strict TypeScript contracts, API integration, loading/error states, accessibility, and responsive dashboards. Use when implementing or reviewing frontend UI.
---

# Frontend development workflow

1. Inspect the app's Next.js version, routing and rendering model, existing component structure, styling system, API contracts, and tests. Do not assume app-router conventions or shadcn/ui are installed.
2. Define or reuse strict TypeScript types from the real API contract. Keep data flow explicit and avoid `any`, duplicated schemas, and invented backend fields.
3. Build cohesive components using established Tailwind, shadcn/ui, and design-token conventions when present. Prefer server components for non-interactive content and client components only where browser interaction requires them.
4. Model actual request states: loading, success, empty, and error; handle retries, cancellation, and stale responses where relevant. Never substitute hardcoded bug records, statuses, events, or test outcomes for backend data.
5. Keep credentials server-side and treat client-side visibility as presentation, never authorization. Render untrusted content safely.
6. Make dashboards responsive and accessible: semantic landmarks, meaningful labels, keyboard interaction, visible focus, appropriate contrast, and announced status/error changes.
7. Add focused tests for user-visible behavior and API state transitions using the existing framework and fixtures. Run available checks; do not install dependencies or invent unconfigured commands.
