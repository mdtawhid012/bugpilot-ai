import type { ApiError } from "@/types/api.types";

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly apiError: ApiError,
  ) {
    super(apiError.message);
  }
}

export function isTerminalStatus(status: string): boolean {
  return status === "reviewable" || status === "failed" || status === "cancelled" || status === "interrupted";
}
