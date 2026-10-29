import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useJobEvents } from "@/api/sse";
import { clearAccessKey, setAccessKey } from "@/api/storage";
import { mockIds } from "@/mocks/data";

const originalFetch = window.fetch;

function streamResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

beforeEach(() => {
  setAccessKey("mock-access-key");
});

afterEach(() => {
  clearAccessKey();
  window.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("useJobEvents with the real stream client", () => {
  it("reconnects after a dropped stream and sends Last-Event-ID", async () => {
    let eventRequests = 0;
    let lastEventIdOnReconnect: string | null = null;

    const fakeFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      if (!url.endsWith("/events")) {
        return originalFetch(input, init);
      }
      eventRequests += 1;
      if (eventRequests === 1) {
        const encoder = new TextEncoder();
        const stream = new ReadableStream<Uint8Array>({
          start(controller) {
            controller.enqueue(
              encoder.encode(
                'retry: 10\nid: 1\nevent: progress\ndata: {"stage":"audio_metrics","percent":40}\n\n',
              ),
            );
            setTimeout(() => controller.error(new Error("simulated drop")), 10);
          },
        });
        return new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        });
      }

      lastEventIdOnReconnect = new Headers(init?.headers).get("last-event-id");
      return streamResponse([
        'id: 2\nevent: progress\ndata: {"stage":"rubric_results","percent":55}\n\n',
        'event: done\ndata: {"call_id":"c3333333-3333-4333-8333-333333333333"}\n\n',
      ]);
    });

    window.fetch = fakeFetch;

    const { result } = renderHook(() => useJobEvents(mockIds.processingJob));

    await waitFor(
      () => {
        expect(result.current.status).toBe("succeeded");
        expect(result.current.percent).toBe(100);
      },
      { timeout: 4000 },
    );

    expect(eventRequests).toBeGreaterThanOrEqual(2);
    expect(lastEventIdOnReconnect).toBe("1");
    expect(result.current.step).toBe("Putting it together");
    expect(result.current.stepIndex).toBe(4);
  });
});
