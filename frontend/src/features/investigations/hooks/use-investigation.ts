"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { InvestigationDetail, InvestigationEvent } from "@/types/api.types";
import { apiRequest } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { isTerminalStatus } from "@/lib/api/errors";
import { mergeEventSequences, nextPollDelay } from "@/lib/polling";

export function useInvestigation(id: string) {
  const [investigation, setInvestigation] = useState<InvestigationDetail | null>(null);
  const [events, setEvents] = useState<InvestigationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);
  const activeId = useRef(id);
  const terminalObserved = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const cursor = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const interval = useRef(1000);

  const clearTimer = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);

  const poll = useCallback(async () => {
    if (inFlight.current || terminalObserved.current) return;
    inFlight.current = true;
    controller.current?.abort();
    const requestController = new AbortController();
    controller.current = requestController;
    try {
      const detail = await apiRequest<InvestigationDetail>(endpoints.investigation(id), { signal: requestController.signal });
      if (activeId.current !== id || requestController.signal.aborted) return;
      setInvestigation(detail);
      setLoading(false);
      setStale(false);
      setError(null);

      const page = await apiRequest<{ items: InvestigationEvent[]; next_cursor: number | null }>(
        endpoints.events(id, cursor.current),
        { signal: requestController.signal },
      );
      if (activeId.current !== id || requestController.signal.aborted) return;
      setEvents((current) => mergeEventSequences(current, page.items));
      if (page.next_cursor !== null) cursor.current = page.next_cursor;
      else if (page.items.length) cursor.current = page.items[page.items.length - 1].sequence;

      if (isTerminalStatus(detail.status)) {
        terminalObserved.current = true;
        clearTimer();
        return;
      }
      interval.current = nextPollDelay(interval.current);
      timer.current = setTimeout(() => void poll(), interval.current);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      if (activeId.current !== id) return;
      setLoading(false);
      setStale(true);
      setError(caught instanceof Error ? caught.message : "Unable to refresh investigation.");
      if (!terminalObserved.current) {
        interval.current = nextPollDelay(interval.current);
        timer.current = setTimeout(() => void poll(), interval.current);
      }
    } finally {
      inFlight.current = false;
    }
  }, [id, clearTimer]);

  useEffect(() => {
    activeId.current = id;
    terminalObserved.current = false;
    cursor.current = 0;
    interval.current = 1000;
    setLoading(true);
    setStale(false);
    setError(null);
    setEvents([]);
    void poll();
    return () => {
      activeId.current = "";
      controller.current?.abort();
      clearTimer();
    };
  }, [id, poll, clearTimer]);

  const refresh = useCallback(() => {
    interval.current = 1000;
    void poll();
  }, [poll]);

  return { investigation, events, loading, stale, error, refresh, setInvestigation };
}
