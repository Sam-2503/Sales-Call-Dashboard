import { QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  useAgents,
  useBenchmarks,
  useCall,
  useCalls,
  useFeedback,
  useJob,
  useMe,
  useMeta,
  usePlaybook,
  useReport,
  useRubric,
  useTrendsScores,
  useWeakSpots,
} from "@/api/hooks";
import { createQueryClient } from "@/api/queryClient";
import { clearAccessKey, setAccessKey } from "@/api/storage";
import { mockIds } from "@/mocks/data";

function Wrapper({ children }: { children: ReactNode }) {
  const [client] = useState(() => createQueryClient());
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function hook<T>(callback: () => T) {
  return renderHook(callback, { wrapper: Wrapper });
}

beforeEach(() => {
  setAccessKey("mock-access-key");
});

afterEach(() => {
  clearAccessKey();
});

describe("resource hooks", () => {
  it("loads public metadata, rubric and playbook", async () => {
    const meta = hook(() => useMeta());
    const rubric = hook(() => useRubric());
    const playbook = hook(() => usePlaybook());

    await waitFor(() => expect(meta.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(rubric.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(playbook.result.current.isSuccess).toBe(true));
    expect(meta.result.current.data?.max_minutes).toBe(5);
    expect(rubric.result.current.data?.items).toHaveLength(10);
    expect(playbook.result.current.data?.available).toBe(true);
  });

  it("loads the workspace and reps when an access key is present", async () => {
    const me = hook(() => useMe());
    const agents = hook(() => useAgents());
    await waitFor(() => expect(me.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(agents.result.current.isSuccess).toBe(true));
    expect(me.result.current.data?.workspace_id).toBe(mockIds.workspace);
    expect(agents.result.current.data?.map((agent) => agent.name)).toEqual(["Me", "Alex"]);
  });

  it("pages calls and loads call detail, report, job and feedback", async () => {
    const calls = hook(() => useCalls({ limit: 2 }));
    const call = hook(() => useCall(mockIds.fullCall));
    const report = hook(() => useReport(mockIds.fullCall));
    const job = hook(() => useJob(mockIds.processingJob));
    const feedback = hook(() => useFeedback(mockIds.fullCall));

    await waitFor(() => expect(calls.result.current.isSuccess).toBe(true));
    expect(calls.result.current.data?.pages[0]?.items).toHaveLength(2);
    expect(calls.result.current.hasNextPage).toBe(true);

    await act(async () => {
      await calls.result.current.fetchNextPage();
    });
    await waitFor(() => expect(calls.result.current.data?.pages).toHaveLength(2));
    expect(calls.result.current.data?.pages[1]?.items.length).toBeGreaterThan(0);

    await waitFor(() => expect(call.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(report.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(job.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(feedback.result.current.isSuccess).toBe(true));
    expect(call.result.current.data?.title).toBe("Cold call with Acme");
    expect(report.result.current.data?.scorecard?.overall_score).toBe(68);
    expect(job.result.current.data?.id).toBe(mockIds.processingJob);
    expect(feedback.result.current.data?.[0]?.verdict).toBe("helpful");
  });

  it("loads trends, weak spots and benchmarks", async () => {
    const scores = hook(() => useTrendsScores());
    const weak = hook(() => useWeakSpots());
    const benchmark = hook(() => useBenchmarks(mockIds.fullCall));

    await waitFor(() => expect(scores.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(weak.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(benchmark.result.current.isSuccess).toBe(true));
    expect(scores.result.current.data?.points.length).toBeGreaterThan(0);
    expect(weak.result.current.data?.available).toBe(false);
    expect(benchmark.result.current.data?.overall.agent_best).toBe(82);
  });
});
