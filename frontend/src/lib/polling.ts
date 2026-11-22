import type { InvestigationEvent } from "@/types/api.types";

export function nextPollDelay(current: number): number {
  return Math.min(Math.max(current * 1.35, 1000), 5000);
}

export function mergeEventSequences(current: InvestigationEvent[], incoming: InvestigationEvent[]): InvestigationEvent[] {
  const known = new Set(current.map((event) => event.sequence));
  const unique = incoming.filter((event) => !known.has(event.sequence));
  return [...current, ...unique].sort((a, b) => a.sequence - b.sequence);
}
