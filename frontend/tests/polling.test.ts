import { describe, expect, it } from "vitest";
import { isTerminalStatus } from "@/lib/api/errors";
import { mergeEventSequences, nextPollDelay } from "@/lib/polling";

describe("investigation polling", () => {
  it("stops terminal statuses and continues active statuses", () => {
    expect(isTerminalStatus("reviewable")).toBe(true);
    expect(isTerminalStatus("failed")).toBe(true);
    expect(isTerminalStatus("cancelled")).toBe(true);
    expect(isTerminalStatus("interrupted")).toBe(true);
    expect(isTerminalStatus("queued")).toBe(false);
    expect(isTerminalStatus("analyzing")).toBe(false);
  });

  it("backs off to a maximum of five seconds", () => {
    expect(nextPollDelay(1000)).toBe(1350);
    expect(nextPollDelay(4000)).toBe(5000);
  });

  it("deduplicates event sequences", () => {
    const first = { sequence: 1, type: "queued", created_at: "now", data: {} };
    const second = { sequence: 2, type: "started", created_at: "now", data: {} };
    expect(mergeEventSequences([first], [first, second])).toEqual([first, second]);
  });
});
