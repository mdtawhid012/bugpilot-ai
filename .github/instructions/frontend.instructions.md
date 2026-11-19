---
applyTo: "**/*.ts,**/*.tsx,**/*.js,**/*.jsx,**/*.css"
---

# Frontend engineering

- Inspect the installed Next.js/React versions, routing structure, design system, and existing conventions before implementation. Do not assume an app router, component library, or generated API client exists until verified.
- Use strict TypeScript and explicit contracts for backend data. Prefer server components and server-side data access where appropriate; add client components only for interactions that require browser state or APIs.
- Keep components cohesive and reusable without abstracting one-off UI prematurely. Follow existing Tailwind and shadcn/ui conventions when configured; preserve semantic HTML and established visual tokens.
- Integrate only real API contracts. Model loading, empty, success, partial, and error states from actual responses; never hardcode fabricated bugs, execution events, test results, or investigation statuses as if they came from the backend.
- Handle network errors, cancellation, stale responses, and user-visible retry behavior where relevant. Do not expose server credentials in browser bundles or rely on client-side checks for authorization.
- Ensure keyboard access, visible focus, meaningful labels, appropriate contrast, semantic landmarks, and accessible status/error announcements. Do not communicate state by color alone.
- Avoid unnecessary client-side JavaScript, broad global state, expensive rerenders, and unbounded data rendering. Use responsive layouts and verify behavior at narrow and wide viewport sizes.
- Add focused tests for user-visible behavior and API state transitions using the existing test setup. Do not add packages or invent a test runner before inspecting the repository.
