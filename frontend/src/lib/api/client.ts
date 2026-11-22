import type { ApiError } from "@/types/api.types";
import { ApiRequestError } from "./errors";

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
    cache: "no-store",
  });

  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      throw new ApiRequestError(response.status, {
        code: "invalid_response",
        message: "The application received an invalid response.",
        request_id: response.headers.get("x-request-id") ?? "unknown",
      });
    }
  }

  if (!response.ok) {
    const apiError = isApiError(data)
      ? data
      : {
          code: "request_failed",
          message: `Request failed with status ${response.status}.`,
          request_id: response.headers.get("x-request-id") ?? "unknown",
        };
    throw new ApiRequestError(response.status, apiError);
  }

  return data as T;
}

function isApiError(value: unknown): value is ApiError {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.code === "string" && typeof candidate.message === "string" && typeof candidate.request_id === "string";
}
