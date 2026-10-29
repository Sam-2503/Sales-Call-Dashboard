import type { CallReport, components } from "@/api/schema";

export type CallSummary = components["schemas"]["CallSummary"];
export type CallResponse = components["schemas"]["CallResponse"];
export type CallListResponse = components["schemas"]["CallListResponse"];
export type JobResponse = components["schemas"]["JobResponse"];
export type Feedback = components["schemas"]["FeedbackResponse"];
export type WorkspaceInfo = components["schemas"]["WorkspaceInfo"];
export type Agent = components["schemas"]["AgentResponse"];
export type Rubric = components["schemas"]["Rubric"];

export type { CallReport };

export type Meta = {
  max_minutes: number;
  max_upload_mb: number;
  allowed_audio_extensions: string[];
  retention_days: number;
  max_reanalyses_per_call: number;
  grounding: boolean;
  demo_available: boolean;
  pipeline_version: string;
  rubric: { id: string; version: string };
  models: {
    analysis: string;
    fast: string;
    transcribe: string;
    embedding: string;
  };
  quota_remaining: number | null;
};

export type PlaybookMetadata = {
  available: boolean;
  reason?: string;
  title?: string | null;
  author?: string | null;
  edition?: string | null;
  chunk_count?: number;
};

export type TrendPoint = {
  call_id: string;
  created_at: string;
  title: string | null;
  overall_score: number | null;
  category_scores: Record<string, number>;
};

export type TrendScores = {
  rubric: { id: string; version: string };
  categories: Array<{ id: string; name: string }>;
  points: TrendPoint[];
  n: number;
};

export type WeakSpot = {
  item_id: string;
  title: string;
  category: string;
  issue_calls: number;
  missed_calls: number;
  applicable_calls: number;
  n_calls: number;
};

export type WeakSpots =
  | {
      available: true;
      rubric: { id: string; version: string };
      n_calls: number;
      items: WeakSpot[];
    }
  | {
      available: false;
      reason: string;
      n_calls: number;
      items: [];
    };

export type BenchmarkCategory = {
  id: string;
  name: string;
  call: number | null;
  agent_best: number | null;
  team_average: number | null;
};

export type Benchmarks = {
  call_id: string;
  rubric: { id: string; version: string };
  overall: {
    call: number | null;
    agent_best: number | null;
    team_average: number | null;
    team_reason: string | null;
  };
  categories: BenchmarkCategory[];
  n: { agent: number; team: number };
};

export type CallFilters = {
  agentId?: string;
  status?: string;
  limit?: number;
};

export type TrendsScoresFilters = {
  agentId?: string;
  since?: string;
  until?: string;
  limit?: number;
};

export type WeakSpotsFilters = {
  agentId?: string;
  lastN?: number;
};
