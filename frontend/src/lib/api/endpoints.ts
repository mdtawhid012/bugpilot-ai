export const endpoints = {
  csrf: "/api/v1/csrf",
  fixtures: "/api/v1/fixtures",
  investigations: "/api/v1/investigations",
  investigation: (id: string) => `/api/v1/investigations/${encodeURIComponent(id)}`,
  events: (id: string, after: number) => `/api/v1/investigations/${encodeURIComponent(id)}/events?after=${after}`,
  cancel: (id: string) => `/api/v1/investigations/${encodeURIComponent(id)}/cancel`,
} as const;
