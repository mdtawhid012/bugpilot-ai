import { NextRequest } from "next/server";
import { proxyBackend } from "../proxy";

export function POST(request: NextRequest) {
  return proxyBackend(request, "/api/v1/investigations", ["POST"]);
}
