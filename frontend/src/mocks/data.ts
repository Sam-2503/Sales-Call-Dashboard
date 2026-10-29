import type {
  CallReport,
  CallResponse,
  CallSummary,
  JobResponse,
  Meta,
  Rubric,
  WorkspaceInfo,
} from "@/api/hooks/types";
import type { Feedback } from "@/api/hooks/types";

import fullReportJson from "./fixtures/full_report.json";
import insufficientReportJson from "./fixtures/insufficient_data_report.json";

const fullReport = fullReportJson as unknown as CallReport;
const insufficientReport = insufficientReportJson as unknown as CallReport;

export const MOCK_TOKEN = "mock-access-key";

const WORKSPACE_ID = "11111111-1111-4111-8111-111111111111";
const ME_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const ALEX_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";

const CALL_FULL = "c1111111-1111-4111-8111-111111111111";
const CALL_SHORT = "c2222222-2222-4222-8222-222222222222";
const CALL_PROCESSING = "c3333333-3333-4333-8333-333333333333";
const CALL_QUEUED = "c4444444-4444-4444-8444-444444444444";
const CALL_FAILED = "c5555555-5555-4555-8555-555555555555";
const CALL_DEMO = "c6666666-6666-4666-8666-666666666666";
const CALL_DEMO_SHORT = "c7777777-7777-4777-8777-777777777777";

const JOB_FULL = "d1111111-1111-4111-8111-111111111111";
const JOB_SHORT = "d2222222-2222-4222-8222-222222222222";
const JOB_PROCESSING = "d3333333-3333-4333-8333-333333333333";
const JOB_QUEUED = "d4444444-4444-4444-8444-444444444444";
const JOB_FAILED = "d5555555-5555-4555-8555-555555555555";
const JOB_DEMO = "d6666666-6666-4666-8666-666666666666";
const JOB_DEMO_SHORT = "d7777777-7777-4777-8777-777777777777";

const STAGES = [
  "ingest",
  "transcribe",
  "assign_roles",
  "audio_metrics",
  "rubric_results",
  "missed_moments",
  "customer_signals",
  "grounding",
  "next_steps",
  "coaching",
] as const;
const PERCENTS = [5, 25, 30, 40, 55, 65, 75, 90, 95, 100] as const;
const STAGE_DELAY_MS = 400;

export type MockJob = {
  id: string;
  callId: string;
  status: "queued" | "processing" | "succeeded" | "failed";
  auto: boolean;
  startedAtMs: number;
  floor: number;
  attempts: number;
  maxAttempts: number;
  errorCode: string | null;
};

export type MockCall = {
  id: string;
  title: string | null;
  status: "queued" | "processing" | "completed" | "failed";
  createdAt: string;
  consentAt: string;
  durationS: number | null;
  overallScore: number | null;
  outcome: string | null;
  reportStatus: "ok" | "insufficient_data" | null;
  hasAudio: boolean;
  isDemo: boolean;
  agentId: string | null;
  agentName: string | null;
  originalFilename: string | null;
  audioMime: string | null;
  audioBytes: number | null;
  reanalysisCount: number;
  completedAt: string | null;
  report: CallReport | null;
  jobId: string | null;
};

export type MockState = {
  workspace: WorkspaceInfo;
  isDemo: boolean;
  quotaRemaining: number;
  agents: Array<{ id: string; name: string; created_at: string }>;
  calls: MockCall[];
  jobs: Record<string, MockJob>;
  feedback: Record<string, Feedback[]>;
  scoresAvailable: boolean;
  weakSpotsAvailable: boolean;
};

export const rubric: Rubric = {
  id: "sales_v1",
  version: "0.1",
  name: "Sales cold-call placeholder",
  scoring: { met: 1, partial: 0.5, missed: 0 },
  categories: [
    { id: "opening", name: "Opening", weight: 0.2 },
    { id: "discovery", name: "Discovery", weight: 0.2 },
    { id: "objection_handling", name: "Objection handling", weight: 0.2 },
    { id: "compliance", name: "Compliance", weight: 0.2 },
    { id: "closing", name: "Closing", weight: 0.2 },
  ],
  items: [
    {
      id: "opening_permission",
      category: "opening",
      title: "Ask permission to continue",
      description: "Ask whether it is a good time to speak.",
      good_looks_like: "Ask for a brief amount of time and accept a no.",
      common_failures: ["Launching into a pitch"],
      weight: 1,
      critical: false,
    },
    {
      id: "opening_context",
      category: "opening",
      title: "Establish relevant context",
      description: "Explain why the call may be relevant.",
      good_looks_like: "Connect the reason for calling to the prospect's role.",
      common_failures: ["Using a generic introduction"],
      weight: 1,
      critical: false,
    },
    {
      id: "discovery_current_state",
      category: "discovery",
      title: "Explore the current state",
      description: "Ask about the current process.",
      good_looks_like: "Open questions reveal the existing workflow.",
      common_failures: ["Asking only yes-or-no questions"],
      weight: 1,
      critical: false,
    },
    {
      id: "discovery_impact",
      category: "discovery",
      title: "Understand business impact",
      description: "Identify the cost of the situation.",
      good_looks_like: "Questions connect the problem to a business result.",
      common_failures: ["Accepting a surface-level problem"],
      weight: 1,
      critical: false,
    },
    {
      id: "objection_acknowledge",
      category: "objection_handling",
      title: "Acknowledge objections",
      description: "Show that the objection was heard.",
      good_looks_like: "Validate the concern before responding.",
      common_failures: ["Arguing immediately"],
      weight: 1,
      critical: false,
    },
    {
      id: "objection_answer",
      category: "objection_handling",
      title: "Respond to objections",
      description: "Give a relevant, concise response.",
      good_looks_like: "Address the stated concern and check whether it helped.",
      common_failures: ["Giving an unrelated feature dump"],
      weight: 1,
      critical: false,
    },
    {
      id: "compliance_consent",
      category: "compliance",
      title: "Respect consent and boundaries",
      description: "Respect requests about timing and contact.",
      good_looks_like: "Stop or adapt when the prospect sets a boundary.",
      common_failures: ["Continuing after an explicit stop"],
      weight: 1,
      critical: true,
    },
    {
      id: "compliance_claims",
      category: "compliance",
      title: "Keep claims supportable",
      description: "Avoid misleading guarantees.",
      good_looks_like: "Qualify claims and tie them to verifiable capabilities.",
      common_failures: ["Promising guaranteed outcomes"],
      weight: 1,
      critical: true,
    },
    {
      id: "closing_next_step",
      category: "closing",
      title: "Secure a clear next step",
      description: "Propose a specific next action.",
      good_looks_like: "The next action has an owner and a time.",
      common_failures: ["Ending with a vague follow-up"],
      weight: 1,
      critical: false,
    },
    {
      id: "closing_confirm",
      category: "closing",
      title: "Confirm commitments",
      description: "Recap agreed actions.",
      good_looks_like: "Confirm the prospect's understanding and commitment.",
      common_failures: ["Assuming agreement"],
      weight: 1,
      critical: false,
    },
  ],
};

function makeJob(
  id: string,
  callId: string,
  status: MockJob["status"],
  options: {
    auto?: boolean;
    startedAtMs?: number;
    floor?: number;
    errorCode?: string | null;
  } = {},
): MockJob {
  return {
    id,
    callId,
    status,
    auto: options.auto ?? false,
    startedAtMs: options.startedAtMs ?? Date.now(),
    floor: options.floor ?? 0,
    attempts: status === "failed" ? 1 : 1,
    maxAttempts: 3,
    errorCode: options.errorCode ?? null,
  };
}

function makeCall(
  id: string,
  jobId: string,
  title: string,
  status: MockCall["status"],
  report: CallReport | null,
  options: Partial<MockCall> = {},
): MockCall {
  return {
    id,
    title,
    status,
    createdAt: "2026-10-28T10:12:00Z",
    consentAt: "2026-10-28T10:10:00Z",
    durationS: 222,
    overallScore: report?.scorecard?.overall_score ?? null,
    outcome: report?.customer_signals?.outcome ?? null,
    reportStatus: report?.status ?? null,
    hasAudio: status === "completed",
    isDemo: false,
    agentId: ME_ID,
    agentName: "Me",
    originalFilename: "synthetic-call.mp3",
    audioMime: "audio/mpeg",
    audioBytes: 1024,
    reanalysisCount: 0,
    completedAt: status === "completed" ? "2026-10-28T10:20:00Z" : null,
    report,
    jobId,
    ...options,
  };
}

function makeFeedback(callId: string, findingId: string, verdict: string): Feedback {
  return {
    id: "e1111111-1111-4111-8111-111111111111",
    call_id: callId,
    finding_id: findingId,
    kind: "moment",
    verdict,
    comment: null,
    created_at: "2026-10-28T10:30:00Z",
    updated_at: "2026-10-28T10:30:00Z",
  };
}

function initialState(): MockState {
  const now = Date.now();
  const jobs: Record<string, MockJob> = {
    [JOB_FULL]: makeJob(JOB_FULL, CALL_FULL, "succeeded"),
    [JOB_SHORT]: makeJob(JOB_SHORT, CALL_SHORT, "succeeded"),
    [JOB_PROCESSING]: makeJob(JOB_PROCESSING, CALL_PROCESSING, "processing", {
      auto: true,
      startedAtMs: now - 80,
      floor: 3,
    }),
    [JOB_QUEUED]: makeJob(JOB_QUEUED, CALL_QUEUED, "queued", {
      auto: true,
      startedAtMs: now + 6_000,
      floor: 0,
    }),
    [JOB_FAILED]: makeJob(JOB_FAILED, CALL_FAILED, "failed", {
      errorCode: "analysis_failed",
    }),
    [JOB_DEMO]: makeJob(JOB_DEMO, CALL_DEMO, "succeeded"),
    [JOB_DEMO_SHORT]: makeJob(JOB_DEMO_SHORT, CALL_DEMO_SHORT, "succeeded"),
  };

  const calls: MockCall[] = [
    makeCall(CALL_FULL, JOB_FULL, "Cold call with Acme", "completed", fullReport),
    makeCall(CALL_SHORT, JOB_SHORT, "A very short call", "completed", insufficientReport, {
      durationS: 12,
      overallScore: null,
      outcome: null,
      reportStatus: "insufficient_data",
      hasAudio: true,
      agentId: ALEX_ID,
      agentName: "Alex",
    }),
    makeCall(CALL_PROCESSING, JOB_PROCESSING, "Discovery follow-up", "processing", fullReport, {
      hasAudio: true,
      completedAt: null,
    }),
    makeCall(CALL_QUEUED, JOB_QUEUED, "Queued call", "queued", null, {
      durationS: 140,
      overallScore: null,
      outcome: null,
      reportStatus: null,
      hasAudio: true,
      completedAt: null,
    }),
    makeCall(CALL_FAILED, JOB_FAILED, "Call that could not be reviewed", "failed", null, {
      durationS: 90,
      overallScore: null,
      outcome: null,
      reportStatus: null,
      hasAudio: true,
      completedAt: null,
    }),
    makeCall(CALL_DEMO, JOB_DEMO, "Sample: Acme discovery", "completed", fullReport, {
      isDemo: true,
      hasAudio: false,
      originalFilename: null,
      audioMime: null,
      audioBytes: null,
    }),
    makeCall(
      CALL_DEMO_SHORT,
      JOB_DEMO_SHORT,
      "Sample: short call",
      "completed",
      insufficientReport,
      {
        isDemo: true,
        hasAudio: false,
        durationS: 12,
        overallScore: null,
        outcome: null,
        reportStatus: "insufficient_data",
        originalFilename: null,
        audioMime: null,
        audioBytes: null,
      },
    ),
  ];

  return {
    workspace: {
      workspace_id: WORKSPACE_ID,
      created_at: "2026-10-01T09:00:00Z",
      last_activity_at: "2026-10-28T10:30:00Z",
      calls_today: 2,
      quota_remaining: 5,
      is_demo: false,
      label: null,
    },
    isDemo: false,
    quotaRemaining: 5,
    agents: [
      { id: ME_ID, name: "Me", created_at: "2026-10-01T09:00:00Z" },
      { id: ALEX_ID, name: "Alex", created_at: "2026-10-01T09:05:00Z" },
    ],
    calls,
    jobs,
    feedback: { [CALL_FULL]: [makeFeedback(CALL_FULL, "moment-discovery-impact", "helpful")] },
    scoresAvailable: true,
    weakSpotsAvailable: false,
  };
}

export const mockState: MockState = initialState();

export function resetMockState(): void {
  Object.assign(mockState, initialState());
}

export function resetDemoState(): void {
  resetMockState();
  mockState.isDemo = true;
  mockState.workspace = {
    ...mockState.workspace,
    is_demo: true,
    label: "Sample workspace",
    quota_remaining: 0,
  };
  mockState.quotaRemaining = 0;
  mockState.calls = mockState.calls.filter((call) => call.isDemo);
  mockState.weakSpotsAvailable = true;
}

export function snapshotJob(job: MockJob): JobResponse {
  if (!job.auto || job.status === "failed") {
    return jobResponse(
      job,
      job.status,
      job.status === "failed" ? 30 : job.status === "succeeded" ? 100 : 0,
      null,
    );
  }
  const elapsed = Date.now() - job.startedAtMs;
  if (elapsed < 0) {
    return jobResponse(job, "queued", 0, null);
  }
  const advanced = Math.floor(elapsed / STAGE_DELAY_MS);
  const index = job.floor + advanced;
  if (index >= STAGES.length) return jobResponse(job, "succeeded", 100, null);
  return jobResponse(job, "processing", PERCENTS[index] ?? 0, STAGES[index] ?? null);
}

function jobResponse(
  job: MockJob,
  status: JobResponse["status"],
  percent: number,
  currentStage: string | null,
): JobResponse {
  return {
    id: job.id,
    call_id: job.callId,
    status,
    attempts: job.attempts,
    max_attempts: job.maxAttempts,
    percent,
    current_stage: currentStage,
    error_code: status === "failed" ? (job.errorCode ?? "internal_error") : null,
    error_message: status === "failed" ? "The analysis failed." : null,
    queue_position: status === "queued" ? 2 : null,
    created_at: "2026-10-28T10:12:00Z",
    started_at: status === "queued" ? null : "2026-10-28T10:12:01Z",
    finished_at: status === "succeeded" || status === "failed" ? "2026-10-28T10:20:00Z" : null,
  };
}

export function currentJob(call: MockCall): JobResponse | null {
  const job = call.jobId ? mockState.jobs[call.jobId] : undefined;
  return job ? snapshotJob(job) : null;
}

export function currentCallStatus(call: MockCall): MockCall["status"] {
  const job = currentJob(call);
  if (job?.status === "succeeded") return "completed";
  if (job?.status === "failed") return "failed";
  if (job?.status === "processing") return "processing";
  if (job?.status === "queued") return "queued";
  return call.status;
}

export function ensureUploadedReport(call: MockCall): void {
  const job = currentJob(call);
  if (job?.status === "succeeded" && !call.report) {
    call.report = fullReport;
    call.reportStatus = "ok";
  }
}

export function toCallSummary(call: MockCall): CallSummary {
  ensureUploadedReport(call);
  const job = currentJob(call);
  const status = currentCallStatus(call);
  return {
    id: call.id,
    title: call.title,
    status,
    created_at: call.createdAt,
    duration_s: call.durationS,
    overall_score: status === "completed" ? call.overallScore : null,
    outcome: status === "completed" ? call.outcome : null,
    report_status: status === "completed" ? call.reportStatus : null,
    percent: job?.percent ?? null,
    has_audio: call.hasAudio && !call.isDemo,
    is_demo: call.isDemo,
    agent_id: call.agentId,
    agent_name: call.agentName,
  };
}

export function toCallResponse(call: MockCall): CallResponse {
  const summary = toCallSummary(call);
  return {
    ...summary,
    original_filename: call.originalFilename,
    consent_at: call.consentAt,
    audio_mime: call.audioMime,
    audio_bytes: call.audioBytes,
    reanalysis_count: call.reanalysisCount,
    completed_at: summary.status === "completed" ? call.completedAt : null,
    job: currentJob(call),
  };
}

export function callById(callId: string): MockCall | undefined {
  return mockState.calls.find((call) => call.id === callId);
}

export function reportFor(call: MockCall): CallReport | null {
  return call.report;
}

export function meta(): Meta {
  return {
    max_minutes: 5,
    max_upload_mb: 25,
    allowed_audio_extensions: [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"],
    retention_days: 30,
    max_reanalyses_per_call: 2,
    grounding: true,
    demo_available: true,
    pipeline_version: "0.1.0",
    rubric: { id: rubric.id, version: rubric.version },
    models: {
      analysis: "mock-analysis",
      fast: "mock-fast",
      transcribe: "mock-transcribe",
      embedding: "mock-embedding",
    },
    quota_remaining: mockState.quotaRemaining,
  };
}

export function workspaceInfo(): WorkspaceInfo {
  return {
    ...mockState.workspace,
    calls_today: mockState.isDemo ? 0 : mockState.workspace.calls_today,
    quota_remaining: mockState.quotaRemaining,
    is_demo: mockState.isDemo,
  };
}

export function weakSpots() {
  if (!mockState.weakSpotsAvailable) {
    return {
      available: false as const,
      reason: "at least 3 analysed calls are required",
      n_calls: mockState.calls.filter((call) => call.report).length,
      items: [] as const,
    };
  }
  return {
    available: true as const,
    rubric: { id: rubric.id, version: rubric.version },
    n_calls: 8,
    items: [
      {
        item_id: "discovery_impact",
        title: "Understand business impact",
        category: "Discovery",
        issue_calls: 5,
        missed_calls: 3,
        applicable_calls: 8,
        n_calls: 8,
      },
      {
        item_id: "discovery_current_state",
        title: "Explore the current state",
        category: "Discovery",
        issue_calls: 4,
        missed_calls: 1,
        applicable_calls: 8,
        n_calls: 8,
      },
    ],
  };
}

export function trendScores() {
  const points = mockState.calls
    .filter((call) => call.report?.scorecard?.overall_score != null)
    .map((call) => ({
      call_id: call.id,
      created_at: call.createdAt,
      title: call.title,
      overall_score: call.report?.scorecard?.overall_score ?? null,
      category_scores: call.report?.scorecard?.category_scores ?? {},
    }));
  return {
    rubric: { id: rubric.id, version: rubric.version },
    categories: rubric.categories.map((category) => ({ id: category.id, name: category.name })),
    points,
    n: points.length,
  };
}

export function benchmarks(call: MockCall) {
  const categoryScores = call.report?.scorecard?.category_scores ?? {};
  return {
    call_id: call.id,
    rubric: { id: rubric.id, version: rubric.version },
    overall: {
      call: call.report?.scorecard?.overall_score ?? null,
      agent_best: 82,
      team_average: 71,
      team_reason: null,
    },
    categories: rubric.categories.map((category) => ({
      id: category.id,
      name: category.name,
      call: categoryScores[category.id] ?? null,
      agent_best: Math.min(100, (categoryScores[category.id] ?? 50) + 8),
      team_average: Math.min(100, (categoryScores[category.id] ?? 50) + 3),
    })),
    n: { agent: 2, team: 2 },
  };
}

export const mockIds = {
  workspace: WORKSPACE_ID,
  me: ME_ID,
  alex: ALEX_ID,
  fullCall: CALL_FULL,
  shortCall: CALL_SHORT,
  processingCall: CALL_PROCESSING,
  queuedCall: CALL_QUEUED,
  failedCall: CALL_FAILED,
  demoCall: CALL_DEMO,
  demoShortCall: CALL_DEMO_SHORT,
  fullJob: JOB_FULL,
  processingJob: JOB_PROCESSING,
  failedJob: JOB_FAILED,
  demoJob: JOB_DEMO,
};

export const mockReports = { fullReport, insufficientReport };
export const stageDelayMs = STAGE_DELAY_MS;
export const stageNames = STAGES;
export const stagePercents = PERCENTS;
