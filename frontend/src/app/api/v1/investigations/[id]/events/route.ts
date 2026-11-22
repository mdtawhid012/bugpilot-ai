import { NextRequest, NextResponse } from "next/server";
import { proxyBackend } from "../../../proxy";

export function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  return context.params.then(({ id }) => {
    const after = request.nextUrl.searchParams.get("after") ?? "0";
    if (!/^\d+$/.test(after)) {
      return NextResponse.json(
        { code: "invalid_request", message: "after must be a non-negative integer", request_id: crypto.randomUUID() },
        { status: 422 },
      );
    }
    return proxyBackend(request, `/api/v1/investigations/${encodeURIComponent(id)}/events?after=${after}`, ["GET"]);
  });
}
