import { useInfiniteQuery, useQuery, type QueryClient } from "@tanstack/react-query";

import { client, request } from "@/api/client";
import { useAccessKey } from "@/api/useAccessKey";

import { isActiveCallStatus, queryKeys } from "./keys";
import type {
  Agent,
  Benchmarks,
  CallFilters,
  CallListResponse,
  CallReport,
  CallResponse,
  Feedback,
  JobResponse,
  Meta,
  PlaybookMetadata,
  Rubric,
  TrendsScoresFilters,
  TrendScores,
  WeakSpots,
  WeakSpotsFilters,
  WorkspaceInfo,
} from "./types";

const LONG_STALE = 30 * 60_000;

export function invalidateReport(client: QueryClient, callId: string): Promise<void> {
  return client.invalidateQueries({ queryKey: queryKeys.report(callId) });
}

export function invalidateCall(client: QueryClient, callId: string): Promise<void> {
  return client.invalidateQueries({ queryKey: queryKeys.call(callId) });
}

export function useMeta() {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: [...queryKeys.meta, Boolean(accessKey)],
    queryFn: () => request<Meta>(client.GET("/api/v1/meta")),
    staleTime: LONG_STALE,
    gcTime: LONG_STALE,
  });
}

export function useMe() {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => request<WorkspaceInfo>(client.GET("/api/v1/me")),
    enabled: Boolean(accessKey),
    staleTime: 30_000,
  });
}

export function useAgents() {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: () => request<Agent[]>(client.GET("/api/v1/agents")),
    enabled: Boolean(accessKey),
    staleTime: 60_000,
  });
}

export function useCalls(filters: CallFilters = {}) {
  const accessKey = useAccessKey();
  return useInfiniteQuery({
    queryKey: queryKeys.calls(filters),
    queryFn: ({ pageParam }) =>
      request<CallListResponse>(
        client.GET("/api/v1/calls", {
          params: {
            query: {
              limit: filters.limit ?? 20,
              cursor: pageParam ?? undefined,
              agent_id: filters.agentId,
              status: filters.status,
            },
          },
        }),
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: Boolean(accessKey),
    staleTime: 10_000,
    refetchInterval: (query) => {
      const active = query.state.data?.pages.some((page) =>
        page.items.some((call) => isActiveCallStatus(call.status)),
      );
      return active ? 3_000 : false;
    },
  });
}

export function useCall(callId: string | null | undefined) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.call(callId ?? ""),
    queryFn: () =>
      request<CallResponse>(
        client.GET("/api/v1/calls/{call_id}", { params: { path: { call_id: callId! } } }),
      ),
    enabled: Boolean(accessKey && callId),
    refetchInterval: (query) => (isActiveCallStatus(query.state.data?.status) ? 3_000 : false),
  });
}

export function useReport(callId: string | null | undefined) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.report(callId ?? ""),
    queryFn: () =>
      request<CallReport>(
        client.GET("/api/v1/calls/{call_id}/report", { params: { path: { call_id: callId! } } }),
      ),
    enabled: Boolean(accessKey && callId),
    staleTime: Infinity,
    gcTime: LONG_STALE,
  });
}

export function useJob(jobId: string | null | undefined, options: { poll?: boolean } = {}) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.job(jobId ?? ""),
    queryFn: () =>
      request<JobResponse>(
        client.GET("/api/v1/jobs/{job_id}", { params: { path: { job_id: jobId! } } }),
      ),
    enabled: Boolean(accessKey && jobId),
    staleTime: 0,
    refetchInterval: (query) => {
      if (!options.poll) return false;
      return isActiveCallStatus(query.state.data?.status) ? 2_000 : false;
    },
  });
}

export function useRubric() {
  return useQuery({
    queryKey: queryKeys.rubric,
    queryFn: () => request<Rubric>(client.GET("/api/v1/rubric")),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

export function usePlaybook() {
  return useQuery({
    queryKey: queryKeys.playbook,
    queryFn: () => request<PlaybookMetadata>(client.GET("/api/v1/playbook")),
    staleTime: LONG_STALE,
  });
}

export function useFeedback(callId: string | null | undefined) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.feedback(callId ?? ""),
    queryFn: () =>
      request<Feedback[]>(
        client.GET("/api/v1/calls/{call_id}/feedback", {
          params: { path: { call_id: callId! } },
        }),
      ),
    enabled: Boolean(accessKey && callId),
    staleTime: 30_000,
  });
}

export function useTrendsScores(filters: TrendsScoresFilters = {}) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.trendsScores(filters),
    queryFn: () =>
      request<TrendScores>(
        client.GET("/api/v1/trends/scores", {
          params: {
            query: {
              agent_id: filters.agentId,
              since: filters.since,
              until: filters.until,
              limit: filters.limit ?? 50,
            },
          },
        }),
      ),
    enabled: Boolean(accessKey),
    staleTime: 60_000,
  });
}

export function useWeakSpots(filters: WeakSpotsFilters = {}) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.weakSpots(filters),
    queryFn: () =>
      request<WeakSpots>(
        client.GET("/api/v1/trends/weak-spots", {
          params: {
            query: {
              agent_id: filters.agentId,
              last_n: filters.lastN ?? 10,
            },
          },
        }),
      ),
    enabled: Boolean(accessKey),
    staleTime: 60_000,
  });
}

export function useBenchmarks(callId: string | null | undefined) {
  const accessKey = useAccessKey();
  return useQuery({
    queryKey: queryKeys.benchmarks(callId ?? ""),
    queryFn: () =>
      request<Benchmarks>(
        client.GET("/api/v1/benchmarks", {
          params: { query: { call_id: callId! } },
        }),
      ),
    enabled: Boolean(accessKey && callId),
    staleTime: 60_000,
  });
}

export { queryKeys };
export type {
  Agent,
  Benchmarks,
  CallFilters,
  CallListResponse,
  CallReport,
  CallResponse,
  Feedback,
  JobResponse,
  Meta,
  PlaybookMetadata,
  Rubric,
  TrendsScoresFilters,
  TrendScores,
  WeakSpots,
  WeakSpotsFilters,
  WorkspaceInfo,
};
