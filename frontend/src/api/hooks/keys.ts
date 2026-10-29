import type { CallFilters, TrendsScoresFilters, WeakSpotsFilters } from "./types";

export const queryKeys = {
  meta: ["meta"] as const,
  me: ["me"] as const,
  agents: ["agents"] as const,
  calls: (filters: CallFilters) => ["calls", filters] as const,
  call: (callId: string) => ["call", callId] as const,
  report: (callId: string) => ["report", callId] as const,
  job: (jobId: string) => ["job", jobId] as const,
  rubric: ["rubric"] as const,
  playbook: ["playbook"] as const,
  feedback: (callId: string) => ["feedback", callId] as const,
  trendsScores: (filters: TrendsScoresFilters) => ["trends", "scores", filters] as const,
  weakSpots: (filters: WeakSpotsFilters) => ["trends", "weak-spots", filters] as const,
  benchmarks: (callId: string) => ["benchmarks", callId] as const,
};

export function isActiveCallStatus(status: string | null | undefined): boolean {
  return status === "queued" || status === "processing";
}
