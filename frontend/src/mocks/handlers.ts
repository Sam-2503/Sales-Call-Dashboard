import { http, HttpResponse } from "msw";

import type { Feedback } from "@/api/hooks/types";

import {
  benchmarks,
  callById,
  ensureUploadedReport,
  meta,
  mockIds,
  mockReports,
  mockState,
  MOCK_TOKEN,
  reportFor,
  resetDemoState,
  resetMockState,
  rubric,
  snapshotJob,
  stageDelayMs,
  stageNames,
  stagePercents,
  toCallResponse,
  toCallSummary,
  trendScores,
  weakSpots,
  workspaceInfo,
} from "./data";
import type { MockCall, MockJob } from "./data";

const BASE = "/api/v1";

function apiError(
  code: string,
  status: number,
  options: { message?: string; retryAfter?: number } = {},
) {
  return HttpResponse.json(
    {
      error: {
        code,
        message: options.message ?? code,
        request_id: "mock-request-id",
      },
    },
    {
      status,
      headers:
        options.retryAfter === undefined
          ? undefined
          : { "Retry-After": String(options.retryAfter) },
    },
  );
}

function unauthorized(request: Request): Response | null {
  const value = request.headers.get("Authorization");
  if (!value?.startsWith("Bearer ")) return apiError("unauthorized", 401);
  return null;
}

function notFound(): Response {
  return apiError("not_found", 404, { message: "Not found." });
}

function uniqueId(): string {
  return globalThis.crypto.randomUUID();
}

type UploadedFile = { name: string; size: number; type: string };
type UploadedForm = { fields: Record<string, string>; file: UploadedFile | null };

function parseBoundary(contentType: string): string | null {
  const match = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(contentType);
  const value = match?.[1] ?? match?.[2];
  return value ? value.trim() : null;
}

function indexOfBytes(bytes: Uint8Array, needle: Uint8Array, from = 0): number {
  outer: for (let index = from; index <= bytes.length - needle.length; index += 1) {
    for (let offset = 0; offset < needle.length; offset += 1) {
      if (bytes[index + offset] !== needle[offset]) continue outer;
    }
    return index;
  }
  return -1;
}

function parseMultipart(buffer: ArrayBuffer, contentType: string): UploadedForm | null {
  const boundary = parseBoundary(contentType);
  if (!boundary) return null;
  const bytes = new Uint8Array(buffer);
  const delimiter = new TextEncoder().encode(`--${boundary}`);
  const separator = new Uint8Array([13, 10, 13, 10]);
  const decoder = new TextDecoder();
  const fields: Record<string, string> = {};
  let file: UploadedFile | null = null;
  let position = indexOfBytes(bytes, delimiter);

  while (position >= 0) {
    if (
      bytes[position + delimiter.length] === 45 &&
      bytes[position + delimiter.length + 1] === 45
    ) {
      break;
    }
    const headerStart = position + delimiter.length + 2;
    const headerEnd = indexOfBytes(bytes, separator, headerStart);
    if (headerEnd < 0) break;
    const headers = decoder.decode(bytes.slice(headerStart, headerEnd));
    const next = indexOfBytes(bytes, delimiter, headerEnd + separator.length);
    if (next < 0) break;
    const content = bytes.slice(
      headerEnd + separator.length,
      Math.max(headerEnd + separator.length, next - 2),
    );
    const name = /name="([^"]+)"/i.exec(headers)?.[1];
    const filename = /filename="([^"]*)"/i.exec(headers)?.[1];
    if (name) {
      if (filename) {
        file = {
          name: filename,
          size: content.length,
          type:
            /content-type:\s*([^\r\n]+)/i.exec(headers)?.[1]?.trim() ?? "application/octet-stream",
        };
      } else {
        fields[name] = decoder.decode(content);
      }
    }
    position = next;
  }
  return { fields, file };
}

function formDataUpload(form: FormData): UploadedForm {
  const fileValue = form.get("file");
  const fields: Record<string, string> = {};
  for (const key of ["consent", "title", "agent_id"]) {
    const value = form.get(key);
    if (typeof value === "string") fields[key] = value;
  }
  return {
    fields,
    file:
      fileValue && typeof fileValue !== "string"
        ? { name: fileValue.name, size: fileValue.size, type: fileValue.type }
        : null,
  };
}

async function readUpload(request: Request): Promise<UploadedForm | null> {
  const fallback = request.clone();
  try {
    return formDataUpload(await request.formData());
  } catch {
    try {
      return parseMultipart(
        await fallback.arrayBuffer(),
        request.headers.get("content-type") ?? "",
      );
    } catch {
      return null;
    }
  }
}

function queryInteger(value: string | null, fallback: number, min: number, max: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, Math.trunc(parsed)));
}

function filterCalls(request: Request): MockCall[] {
  const params = new URL(request.url).searchParams;
  const agentId = params.get("agent_id");
  const status = params.get("status");
  return mockState.calls.filter((call) => {
    const summary = toCallSummary(call);
    return (!agentId || call.agentId === agentId) && (!status || summary.status === status);
  });
}

function sseBlock(id: number | null, event: string, data: Record<string, unknown>): string {
  const prefix = id === null ? "" : `id: ${id}\n`;
  return `${prefix}event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

function streamJob(job: MockJob, request: Request): Response {
  const encoder = new TextEncoder();
  const cursor = Math.max(0, Number.parseInt(request.headers.get("Last-Event-ID") ?? "0", 10) || 0);
  let timer: ReturnType<typeof setTimeout> | undefined;
  let closed = false;

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (text: string) => {
        if (!closed) controller.enqueue(encoder.encode(text));
      };
      const finish = () => {
        if (closed) return;
        closed = true;
        if (timer) clearTimeout(timer);
        try {
          controller.close();
        } catch {
          // The stream may already have been cancelled.
        }
      };
      const wait = (ms: number) =>
        new Promise<void>((resolve) => {
          timer = setTimeout(resolve, ms);
        });

      request.signal.addEventListener("abort", finish);
      const snapshot = snapshotJob(job);
      if (snapshot.status === "failed") {
        send(
          sseBlock(null, "error", {
            error: {
              code: snapshot.error_code ?? "internal_error",
              message: snapshot.error_message ?? "The review did not finish.",
            },
          }),
        );
        finish();
        return;
      }
      if (snapshot.status === "succeeded") {
        send(sseBlock(null, "done", { call_id: job.callId }));
        finish();
        return;
      }
      while (Date.now() < job.startedAtMs && !closed) {
        send(": keep-alive\n\n");
        await wait(1000);
      }
      const start = Math.max(job.floor, cursor);
      for (let index = start; index < stageNames.length && !closed; index += 1) {
        if (index + 1 <= cursor) continue;
        send(
          sseBlock(index + 1, "progress", {
            job_id: job.id,
            stage: stageNames[index],
            status: "finished",
            percent: stagePercents[index],
            elapsed_s: (index + 1) * (stageDelayMs / 1000),
            ts: new Date().toISOString(),
          }),
        );
        await wait(stageDelayMs);
      }
      if (!closed) {
        send(sseBlock(null, "done", { call_id: job.callId }));
        finish();
      }
    },
    cancel() {
      closed = true;
      if (timer) clearTimeout(timer);
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

const handlers = [
  http.get(`${BASE}/meta`, () => HttpResponse.json(meta())),
  http.get(`${BASE}/rubric`, () => HttpResponse.json(rubric)),
  http.get(`${BASE}/playbook`, () =>
    HttpResponse.json({
      available: true,
      title: "The Sales Acceleration Formula",
      author: "Mark Roberge",
      edition: "Example edition",
      chunk_count: 42,
    }),
  ),

  http.post(`${BASE}/workspaces`, () => {
    resetMockState();
    mockState.calls = [];
    mockState.workspace = {
      ...mockState.workspace,
      calls_today: 0,
      quota_remaining: 5,
    };
    mockState.quotaRemaining = 5;
    return HttpResponse.json(
      {
        workspace_id: mockIds.workspace,
        token: MOCK_TOKEN,
        expires_at: "2027-10-29T00:00:00Z",
      },
      { status: 201 },
    );
  }),
  http.post(`${BASE}/workspaces/demo`, () => {
    resetDemoState();
    return HttpResponse.json(
      {
        workspace_id: mockIds.workspace,
        token: MOCK_TOKEN,
        expires_at: "2027-10-29T00:00:00Z",
      },
      { status: 201 },
    );
  }),
  http.get(`${BASE}/me`, ({ request }) => {
    const denied = unauthorized(request);
    return denied ?? HttpResponse.json(workspaceInfo());
  }),
  http.delete(`${BASE}/me`, ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    resetMockState();
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE}/agents`, ({ request }) => {
    const denied = unauthorized(request);
    return denied ?? HttpResponse.json(mockState.agents);
  }),
  http.post(`${BASE}/agents`, async ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const body = (await request.json()) as { name?: unknown };
    const name = typeof body.name === "string" ? body.name.trim() : "";
    if (!name) return apiError("validation_error", 422);
    const agent = { id: uniqueId(), name, created_at: new Date().toISOString() };
    mockState.agents.push(agent);
    return HttpResponse.json(agent, { status: 201 });
  }),
  http.patch(`${BASE}/agents/:agentId`, async ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const agent = mockState.agents.find((item) => item.id === params.agentId);
    if (!agent) return notFound();
    const body = (await request.json()) as { name?: unknown };
    if (typeof body.name === "string" && body.name.trim()) agent.name = body.name.trim();
    return HttpResponse.json(agent);
  }),

  http.get(`${BASE}/calls`, ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const params = new URL(request.url).searchParams;
    const calls = filterCalls(request);
    const limit = queryInteger(params.get("limit"), 20, 1, 100);
    const offset = queryInteger(params.get("cursor"), 0, 0, Number.MAX_SAFE_INTEGER);
    const page = calls.slice(offset, offset + limit);
    return HttpResponse.json({
      items: page.map(toCallSummary),
      next_cursor: offset + limit < calls.length ? String(offset + limit) : null,
    });
  }),
  http.post(`${BASE}/calls`, async ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    if (request.headers.get("x-mock-rate-limit") === "1") {
      return apiError("rate_limited", 429, { retryAfter: 12 });
    }
    const upload = await readUpload(request);
    if (!upload) return apiError("validation_error", 422);
    if (upload.fields.consent !== "true") return apiError("consent_required", 400);
    const file = upload.file;
    if (!file) return apiError("invalid_audio", 422);
    if (mockState.quotaRemaining <= 0) return apiError("quota_exceeded", 429, { retryAfter: 3600 });
    if (file.size > 25 * 1024 * 1024) return apiError("file_too_large", 413);
    const name = file.name.toLowerCase();
    if (!/\.(mp3|wav|m4a|ogg|flac|webm)$/.test(name)) {
      return apiError("unsupported_media", 415);
    }
    const callId = uniqueId();
    const jobId = uniqueId();
    const agentId = upload.fields.agent_id ?? mockIds.me;
    const agent = mockState.agents.find((item) => item.id === agentId) ?? mockState.agents[0];
    const title = upload.fields.title?.trim() || file.name || "Untitled call";
    const call: MockCall = {
      id: callId,
      title,
      status: "queued",
      createdAt: new Date().toISOString(),
      consentAt: new Date().toISOString(),
      durationS: null,
      overallScore: null,
      outcome: null,
      reportStatus: null,
      hasAudio: true,
      isDemo: false,
      agentId: agent?.id ?? null,
      agentName: agent?.name ?? null,
      originalFilename: file.name,
      audioMime: file.type || "audio/mpeg",
      audioBytes: file.size,
      reanalysisCount: 0,
      completedAt: null,
      report: null,
      jobId,
    };
    mockState.calls.unshift(call);
    mockState.jobs[jobId] = {
      id: jobId,
      callId,
      status: "queued",
      auto: true,
      startedAtMs: Date.now(),
      floor: 0,
      attempts: 1,
      maxAttempts: 3,
      errorCode: null,
    };
    mockState.quotaRemaining = Math.max(0, mockState.quotaRemaining - 1);
    mockState.workspace.calls_today += 1;
    return HttpResponse.json({ call_id: callId, job_id: jobId, status: "queued" }, { status: 202 });
  }),
  http.get(`${BASE}/calls/:callId`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const call = callById(String(params.callId));
    return call ? HttpResponse.json(toCallResponse(call)) : notFound();
  }),
  http.delete(`${BASE}/calls/:callId`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const index = mockState.calls.findIndex((call) => call.id === params.callId);
    if (index < 0) return notFound();
    const [removed] = mockState.calls.splice(index, 1);
    if (removed?.jobId) delete mockState.jobs[removed.jobId];
    delete mockState.feedback[String(params.callId)];
    return new HttpResponse(null, { status: 204 });
  }),
  http.get(`${BASE}/calls/:callId/report`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const call = callById(String(params.callId));
    if (!call) return notFound();
    ensureUploadedReport(call);
    const report = reportFor(call);
    if (!report) return apiError("not_ready", 409);
    return HttpResponse.json(report, { headers: { "Cache-Control": "no-store" } });
  }),
  http.get(`${BASE}/calls/:callId/audio-url`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const call = callById(String(params.callId));
    if (!call || call.isDemo || !call.hasAudio) return notFound();
    return HttpResponse.json({
      url: `${BASE}/media/audio?t=mock-media-token&call_id=${encodeURIComponent(call.id)}`,
    });
  }),
  http.post(`${BASE}/calls/:callId/reanalyse`, async ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const call = callById(String(params.callId));
    if (!call) return notFound();
    if (!call.report) return apiError("not_ready", 409);
    if (call.reanalysisCount >= 2) return apiError("conflict", 409);
    const jobId = uniqueId();
    call.reanalysisCount += 1;
    call.jobId = jobId;
    mockState.jobs[jobId] = {
      id: jobId,
      callId: call.id,
      status: "queued",
      auto: true,
      startedAtMs: Date.now(),
      floor: 0,
      attempts: 1,
      maxAttempts: 3,
      errorCode: null,
    };
    return HttpResponse.json(
      { call_id: call.id, job_id: jobId, status: "queued" },
      { status: 202 },
    );
  }),
  http.get(`${BASE}/calls/:callId/feedback`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    return HttpResponse.json(mockState.feedback[String(params.callId)] ?? []);
  }),
  http.put(`${BASE}/calls/:callId/feedback/:findingId`, async ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const call = callById(String(params.callId));
    if (!call) return notFound();
    const body = (await request.json()) as {
      kind?: string;
      verdict?: string;
      comment?: string | null;
    };
    if (body.verdict !== "helpful" && body.verdict !== "disagree") {
      return apiError("validation_error", 422);
    }
    const list = (mockState.feedback[call.id] ??= []);
    const existing = list.find((item) => item.finding_id === params.findingId);
    const now = new Date().toISOString();
    const feedback: Feedback = {
      id: existing?.id ?? uniqueId(),
      call_id: call.id,
      finding_id: String(params.findingId),
      kind: body.kind ?? "moment",
      verdict: body.verdict,
      comment: body.comment ?? null,
      created_at: existing?.created_at ?? now,
      updated_at: now,
    };
    const next = list.filter((item) => item.finding_id !== params.findingId);
    next.push(feedback);
    mockState.feedback[call.id] = next;
    return HttpResponse.json(feedback);
  }),
  http.delete(`${BASE}/calls/:callId/feedback/:findingId`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const list = mockState.feedback[String(params.callId)] ?? [];
    mockState.feedback[String(params.callId)] = list.filter(
      (item) => item.finding_id !== params.findingId,
    );
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE}/jobs/:jobId`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const job = mockState.jobs[String(params.jobId)];
    return job ? HttpResponse.json(snapshotJob(job)) : notFound();
  }),
  http.get(`${BASE}/jobs/:jobId/events`, ({ request, params }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const job = mockState.jobs[String(params.jobId)];
    return job ? streamJob(job, request) : notFound();
  }),

  http.get(`${BASE}/trends/scores`, ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const data = trendScores();
    const agentId = new URL(request.url).searchParams.get("agent_id");
    const points = agentId
      ? data.points.filter((point) => callById(point.call_id)?.agentId === agentId)
      : data.points;
    return HttpResponse.json({ ...data, points, n: points.length });
  }),
  http.get(`${BASE}/trends/weak-spots`, ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    return HttpResponse.json(weakSpots());
  }),
  http.get(`${BASE}/benchmarks`, ({ request }) => {
    const denied = unauthorized(request);
    if (denied) return denied;
    const callId = new URL(request.url).searchParams.get("call_id") ?? "";
    const call = callById(callId);
    if (!call) return notFound();
    if (!call.report) return apiError("not_ready", 409);
    return HttpResponse.json(benchmarks(call));
  }),

  http.get(`${BASE}/media/audio`, () => new HttpResponse(null, { status: 404 })),
];

export { handlers };
export { mockReports };
