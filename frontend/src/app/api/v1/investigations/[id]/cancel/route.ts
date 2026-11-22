import { NextRequest } from "next/server";
import { proxyBackend } from "../../../proxy";

export function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  return context.params.then(({ id }) => proxyBackend(request, `/api/v1/investigations/${encodeURIComponent(id)}/cancel`, ["POST"]));
}
