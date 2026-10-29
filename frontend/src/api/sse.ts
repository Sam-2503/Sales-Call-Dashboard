import {
  EventStreamContentType,
  fetchEventSource,
  type EventSourceMessage,
} from "@microsoft/fetch-event-source";
import { useCallback, useEffect, useRef, useState } from "react";

import { copy, errorMessage } from "@/copy";

import { API_BASE, authHeaders, client, request } from "./client";
import { ApiError, isApiError } from "./errors";
import type { JobResponse } from "./hooks/types";
import { useAccessKey } from "./useAccessKey";

const STAGE_TO_STEP: Record<string, number> = {
  ingest: 0,
  transcribe: 0,
  assign_roles: 1,
  audio_metrics: 1,
  rubric_results: 2,
  missed_moments: 3,
  customer_signals: 3,
  grounding: 3,
  next_steps: 4,
  coaching: 4,
};

export type JobStatus = "idle" | "queued" | "processing" | "succeeded" | "failed";

export type JobProgressError = { code: string; message: string };

export type JobProgress = {
  percent: number;
  stage: string | null;
  step: string;
  stepIndex: number;
  queuePosition: number | null;
  status: JobStatus;
  error: JobProgressError | null;
  polling: boolean;
};

class FatalStreamError extends Error {
  constructor(readonly apiError: ApiError) {
    super(apiError.message);
    this.name = "FatalStreamError";
  }
}

function initialProgress(): JobProgress {
  return {
    percent: 0,
    stage: null,
    step: copy.progress.steps[0],
    stepIndex: 0,
    queuePosition: null,
    status: "idle",
    error: null,
    polling: false,
  };
}

function asJobStatus(value: string | null | undefined): JobStatus {
  if (value === "queued" || value === "processing" || value === "succeeded" || value === "failed") {
    return value;
  }
  return "processing";
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function stepIndexFor(stage: string | null | undefined, previous: number): number {
  if (!stage) return previous;
  return STAGE_TO_STEP[stage] ?? previous;
}

function parsePayload(message: EventSourceMessage): Record<string, unknown> | null {
  if (!message.data) return null;
  try {
    const parsed: unknown = JSON.parse(message.data);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

export function useJobEvents(
  jobId: string | null | undefined,
  options: { enabled?: boolean; pollIntervalMs?: number } = {},
): JobProgress {
  const enabled = options.enabled ?? true;
  const pollIntervalMs = options.pollIntervalMs ?? 2_000;
  const accessKey = useAccessKey();
  const [state, setState] = useState<JobProgress>(initialProgress);
  const [polling, setPolling] = useState(false);
  const terminal = useRef(false);
  const failures = useRef(0);

  useEffect(() => {
    terminal.current = false;
    failures.current = 0;
    setPolling(false);
    setState(initialProgress());
  }, [jobId]);

  const applyJob = useCallback((job: JobResponse) => {
    const status = asJobStatus(job.status);
    if (terminal.current && status !== "succeeded" && status !== "failed") return;
    const stepIndex = status === "succeeded" ? 4 : stepIndexFor(job.current_stage, 0);
    if (status === "succeeded" || status === "failed") terminal.current = true;
    setState((previous) => ({
      ...previous,
      percent: status === "succeeded" ? 100 : Math.max(previous.percent, clampPercent(job.percent)),
      stage: job.current_stage ?? previous.stage,
      stepIndex,
      step: copy.progress.steps[stepIndex] ?? copy.progress.steps[0],
      queuePosition: job.queue_position ?? null,
      status,
      error:
        job.error_code !== null
          ? { code: job.error_code, message: errorMessage(job.error_code) }
          : status === "failed"
            ? { code: "internal_error", message: errorMessage("internal_error") }
            : previous.error,
    }));
  }, []);

  useEffect(() => {
    if (!jobId || !enabled || !accessKey) return;
    let cancelled = false;
    request<JobResponse>(
      client.GET("/api/v1/jobs/{job_id}", { params: { path: { job_id: jobId } } }),
    )
      .then((job) => {
        if (!cancelled) applyJob(job);
      })
      .catch((error: unknown) => {
        if (cancelled || !isApiError(error) || error.status === 401) return;
        setState((previous) => ({
          ...previous,
          status: "failed",
          error: { code: error.code, message: error.message },
        }));
      });
    return () => {
      cancelled = true;
    };
  }, [accessKey, applyJob, enabled, jobId]);

  useEffect(() => {
    if (!jobId || !enabled || !accessKey || polling) return;
    const controller = new AbortController();

    void fetchEventSource(`${API_BASE}/jobs/${jobId}/events`, {
      headers: authHeaders(),
      signal: controller.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (!response.ok) {
          const apiError = await ApiError.fromResponse(response);
          terminal.current = true;
          setState((previous) => ({
            ...previous,
            status: "failed",
            error: { code: apiError.code, message: apiError.message },
          }));
          throw new FatalStreamError(apiError);
        }
        if (!response.headers.get("content-type")?.startsWith(EventStreamContentType)) {
          throw new Error("Unexpected progress stream");
        }
        failures.current = 0;
      },
      onmessage(message) {
        const payload = parsePayload(message);
        if (!payload) return;
        if (message.event === "progress") {
          const stage = typeof payload.stage === "string" ? payload.stage : null;
          const percent =
            typeof payload.percent === "number" ? clampPercent(payload.percent) : undefined;
          setState((previous) => {
            const stepIndex = stepIndexFor(stage, previous.stepIndex);
            return {
              ...previous,
              percent: Math.max(previous.percent, percent ?? previous.percent),
              stage,
              stepIndex,
              step: copy.progress.steps[stepIndex] ?? copy.progress.steps[0],
              queuePosition: null,
              status:
                previous.status === "succeeded" || previous.status === "failed"
                  ? previous.status
                  : "processing",
            };
          });
          return;
        }
        if (message.event === "done") {
          terminal.current = true;
          setState((previous) => ({
            ...previous,
            percent: 100,
            stepIndex: 4,
            step: copy.progress.steps[4],
            queuePosition: null,
            status: "succeeded",
            error: null,
          }));
          return;
        }
        if (message.event === "error") {
          terminal.current = true;
          const error = payload.error;
          const code =
            error && typeof error === "object" && "code" in error && typeof error.code === "string"
              ? error.code
              : "internal_error";
          setState((previous) => ({
            ...previous,
            status: "failed",
            queuePosition: null,
            error: { code, message: errorMessage(code) },
          }));
        }
      },
      onclose() {
        if (terminal.current) return;
        failures.current += 1;
        if (failures.current >= 2) setPolling(true);
      },
      onerror(error) {
        if (error instanceof FatalStreamError) throw error;
        failures.current += 1;
        if (failures.current >= 2) {
          setPolling(true);
          controller.abort();
          return 0;
        }
        return 1000;
      },
    }).catch(() => {
      // The callbacks above surface the stream or polling state.
    });

    return () => controller.abort();
  }, [accessKey, enabled, jobId, polling]);

  useEffect(() => {
    if (!jobId || !enabled || !accessKey || !polling) return;
    let active = true;
    const tick = async () => {
      try {
        const job = await request<JobResponse>(
          client.GET("/api/v1/jobs/{job_id}", { params: { path: { job_id: jobId } } }),
        );
        if (!active) return;
        applyJob(job);
        if (terminal.current) setPolling(false);
      } catch (error) {
        if (!active || !isApiError(error)) return;
        if (error.status >= 400 && error.status < 500) {
          setState((previous) => ({
            ...previous,
            status: "failed",
            error: { code: error.code, message: error.message },
          }));
          setPolling(false);
        }
      }
    };
    void tick();
    const timer = setInterval(() => void tick(), pollIntervalMs);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [accessKey, applyJob, enabled, jobId, pollIntervalMs, polling]);

  return { ...state, polling };
}
