import { fetchEventSource, type EventSourceMessage } from "@microsoft/fetch-event-source";
import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useJobEvents } from "@/api/sse";
import { clearAccessKey, setAccessKey } from "@/api/storage";
import { mockIds, mockState } from "@/mocks/data";

vi.mock("@microsoft/fetch-event-source", () => ({
  EventStreamContentType: "text/event-stream",
  fetchEventSource: vi.fn(),
}));

const mockedFetch = vi.mocked(fetchEventSource);

function message(event: string, data: Record<string, unknown>, id?: string): EventSourceMessage {
  return { id: id ?? "", event, data: JSON.stringify(data) };
}

function streamResponse(): Response {
  return new Response(null, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

beforeEach(() => {
  mockedFetch.mockReset();
  setAccessKey("mock-access-key");
});

afterEach(() => {
  clearAccessKey();
});

describe("useJobEvents", () => {
  it("streams progress, keeps the previous step for unknown stages, and stops on done", async () => {
    mockedFetch.mockImplementation(async (_url, init) => {
      await init.onopen?.(streamResponse());
      init.onmessage?.(message("progress", { stage: "audio_metrics", percent: 40 }, "1"));
      init.onmessage?.(message("progress", { stage: "mystery_stage", percent: 45 }, "2"));
      init.onmessage?.(message("progress", { stage: "rubric_results", percent: 55 }, "3"));
      init.onmessage?.(message("done", {}, "4"));
      init.onclose?.();
    });

    const { result } = renderHook(() => useJobEvents(mockIds.processingJob));

    await waitFor(() => expect(result.current.status).toBe("succeeded"));
    expect(result.current.percent).toBe(100);
    expect(result.current.stepIndex).toBe(4);
    expect(result.current.step).toBe("Putting it together");
    expect(result.current.error).toBeNull();
    expect(mockedFetch).toHaveBeenCalledWith(
      expect.stringContaining(`/jobs/${mockIds.processingJob}/events`),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer mock-access-key" }),
      }),
    );
  });

  it("keeps the previous step when a stage name is unknown", async () => {
    mockedFetch.mockImplementation(async (_url, init) => {
      await init.onopen?.(streamResponse());
      init.onmessage?.(message("progress", { stage: "audio_metrics", percent: 40 }, "1"));
      init.onmessage?.(message("progress", { stage: "future_stage", percent: 46 }, "2"));
    });

    const { result } = renderHook(() => useJobEvents(mockIds.processingJob));

    await waitFor(() => expect(result.current.percent).toBe(46));
    expect(result.current.stepIndex).toBe(1);
    expect(result.current.step).toBe("Measuring the conversation");
    expect(result.current.status).toBe("processing");
  });

  it("falls back to job polling after repeated stream failures", async () => {
    mockedFetch.mockImplementation(async (_url, init) => {
      await init.onopen?.(streamResponse());
      init.onerror?.(new Error("first drop"));
      init.onerror?.(new Error("second drop"));
    });

    const { result } = renderHook(() =>
      useJobEvents(mockIds.processingJob, { pollIntervalMs: 20 }),
    );

    await waitFor(() => expect(result.current.polling).toBe(true));
    mockState.jobs[mockIds.processingJob] = {
      ...mockState.jobs[mockIds.processingJob]!,
      auto: false,
      status: "succeeded",
    };

    await waitFor(
      () => {
        expect(result.current.status).toBe("succeeded");
        expect(result.current.percent).toBe(100);
      },
      { timeout: 2000 },
    );
  });

  it("stops the stream and reports the job error event", async () => {
    mockedFetch.mockImplementation(async (_url, init) => {
      await init.onopen?.(streamResponse());
      init.onmessage?.(
        message("error", {
          error: { code: "analysis_failed", message: "The review did not finish." },
        }),
      );
      init.onclose?.();
    });

    const { result } = renderHook(() => useJobEvents(mockIds.processingJob));

    await waitFor(() => expect(result.current.status).toBe("failed"));
    expect(result.current.error).toMatchObject({ code: "analysis_failed" });
    expect(result.current.error?.message).toContain("Try again");
  });
});
