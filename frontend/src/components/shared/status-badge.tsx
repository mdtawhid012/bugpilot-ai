import { Badge } from "@/components/ui/badge";
import type { InvestigationStatus } from "@/types/api.types";

export function StatusBadge({ status }: { status: InvestigationStatus }) {
  return <Badge className={`status status-${status}`}>{status}</Badge>;
}
