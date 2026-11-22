import { beforeEach, describe, expect, it } from "vitest";
import { NextRequest } from "next/server";
import { validateBrowserMutation } from "@/app/api/v1/proxy";

function mutationRequest(headers: Record<string, string> = {}): NextRequest {
  return new NextRequest("http://127.0.0.1:3000/api/v1/investigations", {
    method: "POST",
    headers,
  });
}

describe("Next.js mutation proxy security", () => {
  beforeEach(() => {
    process.env.BUGPILOT_FRONTEND_ORIGIN = "http://127.0.0.1:3000";
  });

  it("accepts exact same-origin browser mutation headers", () => {
    const response = validateBrowserMutation(mutationRequest({
      origin: "http://127.0.0.1:3000",
      "sec-fetch-site": "same-origin",
      "x-csrf-token": "token",
    }));
    expect(response).toBeNull();
  });

  it("accepts exact bracketed IPv6 loopback origin", () => {
    process.env.BUGPILOT_FRONTEND_ORIGIN = "http://[::1]:3011";
    const response = validateBrowserMutation(mutationRequest({
      origin: "http://[::1]:3011",
      "sec-fetch-site": "same-origin",
      "x-csrf-token": "token",
    }));
    expect(response).toBeNull();
  });

  it.each([
    {},
    { origin: "null", "sec-fetch-site": "same-origin", "x-csrf-token": "token" },
    { origin: "http://attacker.example", "sec-fetch-site": "same-origin", "x-csrf-token": "token" },
    { origin: "http://127.0.0.1:3000", "x-csrf-token": "token" },
    { origin: "http://127.0.0.1:3000", "sec-fetch-site": "cross-site", "x-csrf-token": "token" },
    { origin: "http://127.0.0.1:3000", "sec-fetch-site": "same-origin" },
  ])("rejects invalid browser mutation headers", (headers) => {
    const normalizedHeaders = Object.fromEntries(
      Object.entries(headers).filter((entry): entry is [string, string] => typeof entry[1] === "string"),
    );
    const response = validateBrowserMutation(mutationRequest(normalizedHeaders));
    expect(response?.status).toBe(403);
  });
});
