/**
 * Generated from backend/openapi.json by `npm run gen:api`.
 * Do not edit by hand.
 */
export interface paths {
    "/api/v1/admin/feedback.jsonl": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Feedback Jsonl */
        get: operations["getAdminFeedback"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin Stats */
        get: operations["getAdminStats"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/agents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Agents */
        get: operations["listAgents"];
        put?: never;
        /** Create Agent */
        post: operations["createAgent"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/agents/{agent_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Agent */
        patch: operations["updateAgent"];
        trace?: never;
    };
    "/api/v1/benchmarks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Benchmarks */
        get: operations["getBenchmarks"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Calls */
        get: operations["listCalls"];
        put?: never;
        /** Upload Call */
        post: operations["createCall"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Call */
        get: operations["getCall"];
        put?: never;
        post?: never;
        /** Delete Call */
        delete: operations["deleteCall"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/audio-url": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Audio Url */
        get: operations["getCallAudioUrl"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Feedback */
        get: operations["listFeedback"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/feedback/{finding_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Upsert Feedback */
        put: operations["upsertFeedback"];
        post?: never;
        /** Delete Feedback */
        delete: operations["deleteFeedback"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/job": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Call Job */
        get: operations["getCallJob"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/job/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Call Job */
        post: operations["cancelCallJob"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/job/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Call Job Events */
        get: operations["getCallJobEvents"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/job/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Retry Call Job */
        post: operations["retryCallJob"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/reanalyse": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reanalyse Call */
        post: operations["reanalyseCall"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/reanalyze": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reanalyze Call */
        post: operations["reanalyzeCall"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/calls/{call_id}/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Call Report */
        get: operations["getCallReport"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Job */
        get: operations["getJob"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/jobs/{job_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Job Events */
        get: operations["streamJobEvents"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Workspace */
        get: operations["getWorkspace"];
        put?: never;
        post?: never;
        /** Delete Workspace */
        delete: operations["deleteWorkspace"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/media/audio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Media Audio */
        get: operations["getMediaAudio"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/meta": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Public Meta */
        get: operations["getMeta"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/playbook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Playbook Metadata */
        get: operations["getPlaybook"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rubric": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Active Rubric */
        get: operations["getRubric"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/trends/scores": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Trend Scores */
        get: operations["getTrendScores"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/trends/weak-spots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Weak Spots */
        get: operations["getWeakSpots"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/workspaces": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Workspace */
        post: operations["createWorkspace"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/workspaces/demo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Demo Workspace */
        post: operations["createDemoWorkspace"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/healthz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Healthz */
        get: operations["healthz"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/readyz": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Readyz */
        get: operations["readyz"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AgentCreate */
        AgentCreate: {
            /** Name */
            name: string;
        };
        /** AgentResponse */
        AgentResponse: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** AgentUpdate */
        AgentUpdate: {
            /** Name */
            name: string;
        };
        /** AudioMetrics */
        AudioMetrics: {
            /** Agent Customer Talk Ratio */
            agent_customer_talk_ratio?: number | null;
            /** Agent Talk Ratio */
            agent_talk_ratio?: number | null;
            /** Agent Words Per Minute */
            agent_words_per_minute?: number | null;
            /** Customer Talk Ratio */
            customer_talk_ratio?: number | null;
            /** Customer Words Per Minute */
            customer_words_per_minute?: number | null;
            /** Duration S */
            duration_s: number;
            /**
             * Filler Count
             * @default 0
             */
            filler_count: number;
            /** Filler Rate Agent */
            filler_rate_agent?: number | null;
            /** Filler Rate Customer */
            filler_rate_customer?: number | null;
            /**
             * Interruptions Unavailable Reason
             * @default Transcript segments are sequential; overlapping speech is not measurable in v1.
             */
            interruptions_unavailable_reason: string;
            /** Longest Monologue End S */
            longest_monologue_end_s?: number | null;
            /** Longest Monologue S */
            longest_monologue_s?: number | null;
            /** Longest Monologue Start S */
            longest_monologue_start_s?: number | null;
            /** Longest Monologue Turn Ids */
            longest_monologue_turn_ids?: string[];
            /** Overlap Ratio */
            overlap_ratio?: number | null;
            /** Response Delay Median S */
            response_delay_median_s?: number | null;
            /** Response Delay P90 S */
            response_delay_p90_s?: number | null;
            /** Silence Ratio */
            silence_ratio?: number | null;
            /** Timeline Flags */
            timeline_flags?: components["schemas"]["TimelineFlag"][];
            /**
             * Timing Resolution
             * @default segment_interpolated
             * @enum {string}
             */
            timing_resolution: "segment_interpolated" | "word";
        };
        /** AudioUrlResponse */
        AudioUrlResponse: {
            /** Url */
            url: string;
        };
        /** Body_createCall */
        Body_createCall: {
            /** Agent Id */
            agent_id?: string | null;
            /** Consent */
            consent: boolean;
            /** File */
            file: string;
            /** Title */
            title?: string | null;
        };
        /** CallListResponse */
        CallListResponse: {
            /** Items */
            items: components["schemas"]["CallSummary"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** CallReport */
        CallReport: {
            audio_metrics?: components["schemas"]["AudioMetrics"] | null;
            coaching?: components["schemas"]["Coaching"] | null;
            customer_signals?: components["schemas"]["CustomerSignals"] | null;
            debug?: components["schemas"]["DebugReport"];
            meta: components["schemas"]["ReportMeta"];
            /** Missed Moments */
            missed_moments?: components["schemas"]["MissedMoment"][];
            next_steps?: components["schemas"]["NextSteps"] | null;
            /** Reason */
            reason?: string | null;
            /** Rubric Results */
            rubric_results?: components["schemas"]["RubricResult"][];
            /**
             * Schema Version
             * @default 1.0
             */
            schema_version: string;
            scorecard?: components["schemas"]["Scorecard"] | null;
            /**
             * Status
             * @enum {string}
             */
            status: "ok" | "insufficient_data";
            transcript?: components["schemas"]["Transcript"] | null;
            /**
             * Unverified Count
             * @default 0
             */
            unverified_count: number;
            /** Warnings */
            warnings?: string[];
        };
        /** CallResponse */
        CallResponse: {
            /** Agent Id */
            agent_id?: string | null;
            /** Agent Name */
            agent_name?: string | null;
            /** Audio Bytes */
            audio_bytes?: number | null;
            /** Audio Mime */
            audio_mime?: string | null;
            /** Completed At */
            completed_at?: string | null;
            /**
             * Consent At
             * Format: date-time
             */
            consent_at: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Duration S */
            duration_s: number | null;
            /**
             * Has Audio
             * @default false
             */
            has_audio: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Demo
             * @default false
             */
            is_demo: boolean;
            job?: components["schemas"]["JobResponse"] | null;
            /** Original Filename */
            original_filename?: string | null;
            /** Outcome */
            outcome?: string | null;
            /** Overall Score */
            overall_score?: number | null;
            /** Percent */
            percent?: number | null;
            /**
             * Reanalysis Count
             * @default 0
             */
            reanalysis_count: number;
            /** Report Status */
            report_status?: string | null;
            /** Status */
            status: string;
            /** Title */
            title: string | null;
        };
        /** CallSummary */
        CallSummary: {
            /** Agent Id */
            agent_id?: string | null;
            /** Agent Name */
            agent_name?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Duration S */
            duration_s: number | null;
            /**
             * Has Audio
             * @default false
             */
            has_audio: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Is Demo
             * @default false
             */
            is_demo: boolean;
            /** Outcome */
            outcome?: string | null;
            /** Overall Score */
            overall_score?: number | null;
            /** Percent */
            percent?: number | null;
            /** Report Status */
            report_status?: string | null;
            /** Status */
            status: string;
            /** Title */
            title: string | null;
        };
        /** CallUploadResponse */
        CallUploadResponse: {
            /**
             * Call Id
             * Format: uuid
             */
            call_id: string;
            /**
             * Job Id
             * Format: uuid
             */
            job_id: string;
            /** Status */
            status: string;
        };
        /** Coaching */
        Coaching: {
            /** Strength */
            strength?: string | null;
            /** Top Fixes */
            top_fixes?: components["schemas"]["CoachingItem"][];
        };
        /** CoachingItem */
        CoachingItem: {
            /** Explanation */
            explanation: string;
            /** Finding Id */
            finding_id: string;
            /** Practice Drill */
            practice_drill: string;
        };
        /** Commitment */
        Commitment: {
            /** Due */
            due: string;
            evidence: components["schemas"]["Evidence"];
            /** Party */
            party: string;
            /** What */
            what: string;
        };
        /** CustomerSignals */
        CustomerSignals: {
            /** Buying Signals */
            buying_signals?: components["schemas"]["Evidence"][];
            /** Commitments */
            commitments?: components["schemas"]["Commitment"][];
            /** Objections */
            objections?: components["schemas"]["Objection"][];
            /**
             * Outcome
             * @default unclear
             * @enum {string}
             */
            outcome: "advanced" | "stalled" | "lost" | "unclear";
            /** Sentiment Arc */
            sentiment_arc?: components["schemas"]["SentimentPoint"][];
            /** Unanswered Questions */
            unanswered_questions?: components["schemas"]["Evidence"][];
        };
        /** DebugReport */
        DebugReport: {
            /** Dropped Findings */
            dropped_findings?: {
                [key: string]: unknown;
            }[];
            /** Retrieved Passage Ids */
            retrieved_passage_ids?: {
                [key: string]: string[];
            };
        };
        /** Evidence */
        Evidence: {
            /** Attempt */
            attempt: number;
            /** End S */
            end_s: number;
            /** Match Score */
            match_score: number;
            /** Quote */
            quote: string;
            /**
             * Role
             * @enum {string}
             */
            role: "agent" | "customer" | "other";
            /** Speaker */
            speaker: string;
            /** Start S */
            start_s: number;
            /** Turn Id */
            turn_id: string;
        };
        /** FeedbackCreate */
        FeedbackCreate: {
            /** Comment */
            comment?: string | null;
            /** Finding Id */
            finding_id: string;
            /** Kind */
            kind: string;
            /**
             * Verdict
             * @enum {string}
             */
            verdict: "helpful" | "disagree";
        };
        /** FeedbackResponse */
        FeedbackResponse: {
            /**
             * Call Id
             * Format: uuid
             */
            call_id: string;
            /** Comment */
            comment: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Finding Id */
            finding_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Verdict */
            verdict: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** JobActionResponse */
        JobActionResponse: {
            /**
             * Call Id
             * Format: uuid
             */
            call_id: string;
            /**
             * Job Id
             * Format: uuid
             */
            job_id: string;
            /** Status */
            status: string;
        };
        /** JobEventResponse */
        JobEventResponse: {
            /** Detail */
            detail: {
                [key: string]: unknown;
            };
            /** Elapsed S */
            elapsed_s: number | null;
            /** Id */
            id: number;
            /** Percent */
            percent: number;
            /** Stage */
            stage: string;
            /** Status */
            status: string;
            /**
             * Ts
             * Format: date-time
             */
            ts: string;
        };
        /** JobResponse */
        JobResponse: {
            /** Attempts */
            attempts: number;
            /**
             * Call Id
             * Format: uuid
             */
            call_id: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Current Stage */
            current_stage: string | null;
            /** Error Code */
            error_code: string | null;
            /** Error Message */
            error_message: string | null;
            /** Finished At */
            finished_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Max Attempts */
            max_attempts: number;
            /** Percent */
            percent: number;
            /** Queue Position */
            queue_position?: number | null;
            /** Started At */
            started_at: string | null;
            /** Status */
            status: string;
        };
        /** MissedMoment */
        MissedMoment: {
            /** Better Alternative */
            better_alternative?: string | null;
            /** Category */
            category: string;
            /**
             * Confidence
             * @default medium
             * @enum {string}
             */
            confidence: "high" | "medium" | "low";
            evidence?: components["schemas"]["Evidence"] | null;
            /**
             * Grounded
             * @default false
             */
            grounded: boolean;
            /** Id */
            id: string;
            /** Model Confidence */
            model_confidence: number;
            /** Playbook Refs */
            playbook_refs?: components["schemas"]["PlaybookRef"][];
            /** Rubric Item Id */
            rubric_item_id: string;
            /**
             * Severity
             * @enum {string}
             */
            severity: "low" | "medium" | "high" | "critical";
            /** What Happened */
            what_happened: string;
            /** Why It Hurt */
            why_it_hurt?: string | null;
        };
        /** NextSteps */
        NextSteps: {
            /** Follow Up Message */
            follow_up_message?: string | null;
            /** Recommended Actions */
            recommended_actions?: string[];
        };
        /** Objection */
        Objection: {
            raised_evidence: components["schemas"]["Evidence"];
            resolution_evidence?: components["schemas"]["Evidence"] | null;
            /** Resolved */
            resolved: boolean;
            /** Text */
            text: string;
        };
        /** PlaybookRef */
        PlaybookRef: {
            /** Book Title */
            book_title: string;
            /** Chapter */
            chapter: string;
            /** Excerpt */
            excerpt: string;
            /** Page End */
            page_end: number;
            /** Page Start */
            page_start: number;
            /** Passage Id */
            passage_id: string;
        };
        /** ReanalyseRequest */
        ReanalyseRequest: {
            /** Agent Speaker */
            agent_speaker?: string | null;
        };
        /** ReportMeta */
        ReportMeta: {
            /** Audio Sha256 */
            audio_sha256?: string | null;
            /** Duration S */
            duration_s?: number | null;
            /** Models */
            models?: {
                [key: string]: string;
            };
            /** Pipeline Version */
            pipeline_version: string;
            /** Playbook Identity */
            playbook_identity?: {
                [key: string]: unknown;
            } | null;
            /** Prompt Ids */
            prompt_ids?: {
                [key: string]: string;
            };
            /** Rubric Id */
            rubric_id?: string | null;
            /** Rubric Version */
            rubric_version?: string | null;
            /** Stage Latency S */
            stage_latency_s?: {
                [key: string]: number;
            };
            /** Usage */
            usage?: {
                [key: string]: number;
            };
        };
        /** Rubric */
        Rubric: {
            /** Categories */
            categories: components["schemas"]["RubricCategory"][];
            /** Id */
            id: string;
            /** Items */
            items: components["schemas"]["RubricItem"][];
            /** Name */
            name: string;
            /** Scoring */
            scoring?: {
                [key: string]: number;
            };
            /** Version */
            version: string;
        };
        /** RubricCategory */
        RubricCategory: {
            /** Id */
            id: string;
            /** Name */
            name: string;
            /**
             * Weight
             * @default 1
             */
            weight: number;
        };
        /** RubricItem */
        RubricItem: {
            /** Applies When */
            applies_when?: string | null;
            /** Category */
            category: string;
            /** Common Failures */
            common_failures?: string[];
            /**
             * Critical
             * @default false
             */
            critical: boolean;
            /** Description */
            description: string;
            /** Good Looks Like */
            good_looks_like: string;
            /** Id */
            id: string;
            /** Source Refs */
            source_refs?: string[];
            /** Title */
            title: string;
            /**
             * Weight
             * @default 1
             */
            weight: number;
        };
        /** RubricResult */
        RubricResult: {
            /** Category */
            category: string;
            /**
             * Confidence
             * @default medium
             * @enum {string}
             */
            confidence: "high" | "medium" | "low";
            evidence?: components["schemas"]["Evidence"] | null;
            /** Id */
            id: string;
            /** Model Confidence */
            model_confidence: number;
            /** Rationale */
            rationale: string;
            /** Rubric Item Id */
            rubric_item_id?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "met" | "partial" | "missed" | "not_applicable";
        };
        /** Scorecard */
        Scorecard: {
            /** Category Scores */
            category_scores?: {
                [key: string]: number;
            };
            /** Critical Failures */
            critical_failures?: string[];
            /** Overall Score */
            overall_score?: number | null;
        };
        /** SentimentPoint */
        SentimentPoint: {
            /** Quote */
            quote: string;
            /**
             * Sentiment
             * @enum {string}
             */
            sentiment: "positive" | "neutral" | "negative" | "mixed";
            /** Turn Id */
            turn_id: string;
        };
        /** TimelineFlag */
        TimelineFlag: {
            /** Detail */
            detail: string;
            /** End S */
            end_s: number;
            /**
             * Kind
             * @enum {string}
             */
            kind: "dead_air" | "overlap" | "fast_pace" | "filler_cluster" | "slow_response" | "long_monologue";
            /** Speaker */
            speaker?: string | null;
            /** Start S */
            start_s: number;
        };
        /** Transcript */
        Transcript: {
            /** Duration S */
            duration_s: number;
            /**
             * Language
             * @default en
             */
            language: string;
            /**
             * Source Model
             * @default unknown
             */
            source_model: string;
            /** Speaker Roles */
            speaker_roles?: {
                [key: string]: "agent" | "customer" | "other";
            };
            /** Speakers */
            speakers?: string[];
            /**
             * Timing
             * @default segment_interpolated
             * @enum {string}
             */
            timing: "segment_interpolated" | "word";
            /** Turns */
            turns?: components["schemas"]["Turn"][];
        };
        /** Turn */
        Turn: {
            /** End S */
            end_s: number;
            /** Id */
            id: string;
            /**
             * Role
             * @default other
             * @enum {string}
             */
            role: "agent" | "customer" | "other";
            /** Speaker */
            speaker: string;
            /** Start S */
            start_s: number;
            /** Text */
            text: string;
            /** Words */
            words: components["schemas"]["Word"][];
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** Word */
        Word: {
            /** End S */
            end_s: number;
            /** Speaker */
            speaker: string;
            /** Start S */
            start_s: number;
            /** Text */
            text: string;
        };
        /** WorkspaceInfo */
        WorkspaceInfo: {
            /** Calls Today */
            calls_today: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Is Demo
             * @default false
             */
            is_demo: boolean;
            /** Label */
            label?: string | null;
            /**
             * Last Activity At
             * Format: date-time
             */
            last_activity_at: string;
            /**
             * Quota Remaining
             * @default 0
             */
            quota_remaining: number;
            /**
             * Workspace Id
             * Format: uuid
             */
            workspace_id: string;
        };
        /** WorkspaceResponse */
        WorkspaceResponse: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Token */
            token: string;
            /**
             * Workspace Id
             * Format: uuid
             */
            workspace_id: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    getAdminFeedback: {
        parameters: {
            query?: never;
            header?: {
                "X-Admin-Token"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getAdminStats: {
        parameters: {
            query?: never;
            header?: {
                "X-Admin-Token"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listAgents: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AgentResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    createAgent: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AgentCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AgentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    updateAgent: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                agent_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AgentUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AgentResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getBenchmarks: {
        parameters: {
            query: {
                call_id: string;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listCalls: {
        parameters: {
            query?: {
                limit?: number;
                cursor?: string | null;
                agent_id?: string | null;
                status?: string | null;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallListResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    createCall: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_createCall"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallUploadResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getCall: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deleteCall: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getCallAudioUrl: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AudioUrlResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listFeedback: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeedbackResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upsertFeedback: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
                finding_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FeedbackCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeedbackResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deleteFeedback: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
                finding_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getCallJob: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cancelCallJob: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobActionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getCallJobEvents: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobEventResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    retryCallJob: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobActionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reanalyseCall: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: {
            content: {
                "application/json": components["schemas"]["ReanalyseRequest"] | null;
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobActionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reanalyzeCall: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobActionResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getCallReport: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CallReport"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getJob: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["JobResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    streamJobEvents: {
        parameters: {
            query?: never;
            header?: {
                "Last-Event-ID"?: string | null;
                authorization?: string | null;
            };
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getWorkspace: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deleteWorkspace: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getMediaAudio: {
        parameters: {
            query: {
                t: string;
                call_id: string;
            };
            header?: {
                Range?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getMeta: {
        parameters: {
            query?: never;
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getPlaybook: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    getRubric: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Rubric"];
                };
            };
        };
    };
    getTrendScores: {
        parameters: {
            query?: {
                agent_id?: string | null;
                since?: string | null;
                until?: string | null;
                limit?: number;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    getWeakSpots: {
        parameters: {
            query?: {
                agent_id?: string | null;
                last_n?: number;
            };
            header?: {
                authorization?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    createWorkspace: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceResponse"];
                };
            };
        };
    };
    createDemoWorkspace: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WorkspaceResponse"];
                };
            };
        };
    };
    healthz: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
    readyz: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}

export type CallReport = components["schemas"]["CallReport"];
