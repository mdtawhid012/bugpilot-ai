import { NextRequest, NextResponse } from "next/server";

const FORWARD_BLOCKLIST = new Set([
  "forwarded",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-proto",
  "x-real-ip",
]);

function backendOrigin(): string {
  const origin = process.env.BUGPILOT_BACKEND_ORIGIN;
  if (!origin) throw new Error("BUGPILOT_BACKEND_ORIGIN is not configured");
  const parsed = new URL(origin);
  const hostname = parsed.hostname.replace(/^\[|\]$/g, "");
  if (!["127.0.0.1", "::1"].includes(hostname)) {
    throw new Error("BUGPILOT_BACKEND_ORIGIN must be loopback");
  }
  return parsed.origin;
}

function frontendOrigin(): string {
  const origin = process.env.BUGPILOT_FRONTEND_ORIGIN;
  if (!origin) throw new Error("BUGPILOT_FRONTEND_ORIGIN is not configured");
  const parsed = new URL(origin);
  const hostname = parsed.hostname.replace(/^\[|\]$/g, "");
  if (!["127.0.0.1", "::1"].includes(hostname) || parsed.pathname !== "" && parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new Error("BUGPILOT_FRONTEND_ORIGIN must be an exact loopback origin");
  }
  return parsed.origin;
}

export function validateBrowserMutation(request: NextRequest): NextResponse | null {
  let origin: string;
  try {
    origin = frontendOrigin();
  } catch {
    return NextResponse.json(
      { code: "internal_error", message: "The proxy configuration is unavailable", request_id: crypto.randomUUID() },
      { status: 500 },
    );
  }
  if (request.headers.get("origin") !== origin) {
    return NextResponse.json(
      { code: "invalid_request", message: "Request origin is not allowed", request_id: crypto.randomUUID() },
      { status: 403 },
    );
  }
  if (request.headers.get("sec-fetch-site") !== "same-origin") {
    return NextResponse.json(
      { code: "invalid_request", message: "Request site is not allowed", request_id: crypto.randomUUID() },
      { status: 403 },
    );
  }
  const csrf = request.headers.get("x-csrf-token")?.trim();
  if (!csrf) {
    return NextResponse.json(
      { code: "invalid_request", message: "CSRF token is required", request_id: crypto.randomUUID() },
      { status: 403 },
    );
  }
  return null;
}

export async function proxyBackend(request: NextRequest, backendPath: string, allowedMethods: string[]): Promise<NextResponse> {
  if (!allowedMethods.includes(request.method)) {
    return NextResponse.json({ code: "invalid_request", message: "Method not allowed", request_id: crypto.randomUUID() }, { status: 405 });
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    const validationError = validateBrowserMutation(request);
    if (validationError) return validationError;
  }
  if (request.method === "POST" && backendPath === "/api/v1/investigations") {
    if (!request.headers.get("idempotency-key")?.trim()) {
      return NextResponse.json(
        { code: "invalid_request", message: "Idempotency-Key is required", request_id: crypto.randomUUID() },
        { status: 422 },
      );
    }
  }

  let destination: URL;
  try {
    destination = new URL(backendPath, backendOrigin());
  } catch {
    return NextResponse.json({ code: "internal_error", message: "The backend proxy is unavailable.", request_id: crypto.randomUUID() }, { status: 502 });
  }

  const headers = new Headers();
  headers.set("Accept", "application/json");
  for (const [name, value] of request.headers.entries()) {
    const lower = name.toLowerCase();
    if (!FORWARD_BLOCKLIST.has(lower) && lower !== "host" && lower !== "connection") {
      if (lower === "origin" || lower === "sec-fetch-site" || lower === "cookie") continue;
      headers.set(name, value);
    }
  }

  if (request.method !== "GET") {
    headers.set("Origin", frontendOrigin());
    headers.set("Sec-Fetch-Site", "same-origin");
  }

  const csrf = request.headers.get("x-csrf-token");
  if (csrf) headers.set("X-CSRF-Token", csrf);
  const idempotencyKey = request.headers.get("idempotency-key");
  if (idempotencyKey) headers.set("Idempotency-Key", idempotencyKey);

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
  }

  try {
    const response = await fetch(destination, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });
    const responseBody = await response.text();
    const nextResponse = new NextResponse(responseBody || null, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" },
    });
    const requestId = response.headers.get("x-request-id");
    if (requestId) nextResponse.headers.set("X-Request-ID", requestId);
    return nextResponse;
  } catch {
    return NextResponse.json({ code: "internal_error", message: "The backend is unavailable.", request_id: crypto.randomUUID() }, { status: 502 });
  }
}
