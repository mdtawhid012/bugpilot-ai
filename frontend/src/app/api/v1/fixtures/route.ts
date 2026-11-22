import { NextRequest } from "next/server";
import { proxyBackend } from "../proxy";

export function GET(request: NextRequest) {
  return proxyBackend(request, "/api/v1/fixtures", ["GET"]);
}
