const configuredName = import.meta.env.VITE_APP_NAME?.trim();

export const APP_NAME =
  configuredName && configuredName.length > 0 ? configuredName : "Call review";

type ErrorContext = {
  maxMb?: number;
  maxMinutes?: number;
  minSeconds?: number;
  retryAfterSeconds?: number;
  requestId?: string;
};

function seconds(value: number | undefined): string {
  if (value === undefined) return "a moment";
  return value === 1 ? "1 second" : `${value} seconds`;
}

function minutes(value: number | undefined): string {
  if (value === undefined) return "the limit";
  return value === 1 ? "1 minute" : `${value} minutes`;
}

function megabytes(value: number | undefined): string {
  if (value === undefined) return "the limit";
  return `${value} MB`;
}

export const copy = {
  appName: APP_NAME,
  nav: {
    calls: "Calls",
    progress: "Progress",
    settings: "Settings",
  },
  common: {
    skipToContent: "Skip to content",
    close: "Close",
    cancel: "Cancel",
    save: "Save",
    copy: "Copy",
    copied: "Copied",
    copyFailed: "Copy failed. Select the text and copy it yourself.",
    retry: "Try again",
    loading: "Loading",
    showDetails: "Show details",
    hideDetails: "Hide details",
    showAll: "Show all",
    showLess: "Show less",
    moreInformation: "More information",
    dismiss: "Dismiss",
    dismissNotification: "Dismiss notification",
    optional: "Optional",
    of: "of",
    and: "and",
  },
  status: {
    queued: "Waiting",
    processing: "Reviewing",
    completed: "Ready",
    failed: "Couldn't review",
    done: "Done",
    partly: "Partly done",
    missed: "Missed",
    notApplicable: "Didn't apply",
    unavailable: "Not available",
  },
  outcome: {
    advanced: "Moving forward",
    stalled: "Stalled",
    lost: "Lost",
    unclear: "Unclear",
  },
  impact: {
    high: "Big impact",
    medium: "Medium impact",
    low: "Small impact",
  },
  timelineFlag: {
    longMonologue: "Long stretch of talking",
    deadAir: "Long silence",
    slowResponse: "Slow reply",
    unknown: "Note",
  },
  components: {
    scoreLabel: "Overall score",
    scoreUnavailable: "Score not available",
    emptyTitle: "Nothing here yet",
    errorTitle: "This didn't load",
    errorFallback: "Try again. If it keeps happening, come back in a few minutes.",
    supportReference: "Reference for support",
    toastRegion: "Notifications",
    dialogClose: "Close dialog",
    popoverLabel: "Details",
    infoLabel: "More information",
    copyLabel: "Copy text",
    skeletonLabel: "Loading content",
  },
  feedback: {
    honesty:
      "This review is written by AI. Every quote is checked against the transcript, but use your own judgment on the advice.",
    leftOut: (count: number) =>
      count === 1
        ? "We left out 1 finding we couldn't confirm in the transcript."
        : `We left out ${count} findings we couldn't confirm in the transcript.`,
    approximateTimes: "Times are approximate.",
  },
  errors: {
    consentRequired: "Tick the permission box before uploading.",
    fileTooLarge: (maxMb?: number) =>
      `That file is larger than ${megabytes(maxMb)}. Choose a smaller file or trim it.`,
    unsupportedMedia:
      "That file type isn't supported. Choose an MP3, WAV, M4A or another common audio file.",
    invalidAudio: "We couldn't read that audio. Try another file or export it again.",
    audioTooLong: (maxMinutes?: number) =>
      `That call is longer than ${minutes(maxMinutes)}. Trim it and upload a shorter section.`,
    audioTooShort: (minSeconds?: number) =>
      `That call is shorter than ${seconds(minSeconds)}. Upload a longer conversation.`,
    quotaExceeded: "You've used today's uploads. Try again tomorrow.",
    rateLimited: (retryAfterSeconds?: number) =>
      `Too many requests. Try again in ${seconds(retryAfterSeconds)}.`,
    budgetExceeded: "The sample has reached its daily limit. Try again tomorrow.",
    notReady: "This review isn't ready yet. Wait a moment and try again.",
    conflict: "Something changed while you were working. Refresh the page and try again.",
    playbookUnavailable:
      "The book guidance isn't available right now. You can still read the rest of the review.",
    serviceUnavailable: "The service is unavailable right now. Try again in a minute.",
    unauthorized:
      "We couldn't open these calls. Enter your access key, or start fresh. Starting fresh leaves the old calls behind.",
    internal: "Something went wrong. Try again. If it keeps happening, share the reference below.",
    unknown: "Something went wrong. Try again.",
    job: {
      transcription_failed:
        "We couldn't hear enough of the call to review it. Check the audio and try again.",
      content_blocked:
        "This call couldn't be reviewed because part of it was blocked. Try a different call.",
      analysis_failed: "The review didn't finish. Try again; your call is still saved.",
      worker_lost: "The review stopped unexpectedly. Try again; your call is still saved.",
      playbook_unavailable:
        "The book guidance isn't available right now. Try again; your call is still saved.",
      invalid_audio: "We couldn't read that audio. Try another file or export it again.",
      internal_error: "The review didn't finish. Try again; your call is still saved.",
    },
  },
  progress: {
    steps: [
      "Listening to the call",
      "Measuring the conversation",
      "Checking it against your checklist",
      "Finding stronger ways to say it",
      "Putting it together",
    ],
    queuedAhead: (count: number) =>
      count === 1 ? "1 call ahead of you" : `${count} calls ahead of you`,
    canLeave: "You can leave this page. Your review will be in your list when it's done.",
    waiting: "Waiting to start",
  },
  labels: {
    you: "You",
    customer: "Customer",
    call: "Call",
    rep: "Rep",
    score: "Score",
    outcome: "Outcome",
    date: "Date",
    duration: "Duration",
    impact: "Impact",
    lessSure: "Less sure",
    whatWasSaid: "What was said",
    whyItMatters: "Why it matters",
    strongerLine: "A stronger line",
    fromBook: "From",
    chapter: "Chapter",
    pages: "Pages",
    showPassage: "Show passage",
    customerReaction: "How the customer reacted",
    handled: "Handled",
    notHandled: "Not handled",
    checklist: "Checklist",
    momentToImprove: "Moment to improve",
    runAgain: "Run again",
    changeRep: "Change who the rep is",
    yourCalls: "Your calls on this browser",
    accessKey: "Access key",
  },
  preview: {
    title: "Interface preview",
    intro:
      "This page shows the shared building blocks for the review screens. The review screens themselves are not built yet.",
    sectionActions: "Actions",
    sectionStatus: "Status and scores",
    sectionSurfaces: "Panels and notices",
    sectionStates: "Loading and empty states",
    sectionText: "Transcript marks",
    primaryAction: "Upload a call",
    secondaryAction: "Show details",
    quietAction: "Not now",
    exampleHeading: "Three things to work on",
    exampleBody:
      "Each finding will show what was said, why it matters, and a line you can try next time.",
    exampleQuote: "I'm not sure we have budget this quarter.",
    exampleMoment: "Ask what would make budget available",
    exampleSpeaker: "Customer",
    exampleSpeakerLabel: "Customer",
    themeLabel: "Colour theme",
    themeSystem: "System",
    themeLight: "Light",
    themeDark: "Dark",
    toastAction: "Show a notification",
    toastTitle: "Call deleted",
    toastBody: "The call and its audio were removed.",
    dialogOpen: "Open a dialog",
    dialogTitle: "Delete this call?",
    dialogBody: "This removes the call, its audio, and its review. You can't undo this.",
    dialogConfirm: "Delete call",
    popoverOpen: "Show a moment",
    popoverBody: "Play from here, or open the full moment.",
    popoverLabel: "Moment details",
    tabsLabel: "Review sections",
    tabSummary: "Summary",
    tabMoments: "Moments",
    tabDetails: "Details",
    tabTranscript: "Transcript",
    disclosureLabel: "About this review",
    disclosureBody: "Versions and timings sit here, out of the way of the review.",
    copyText: "Hi Sam, thanks for the conversation today.",
    emptyTitle: "No calls yet",
    emptyBody: "Upload a call to get your first review.",
    errorTitle: "We couldn't load your calls",
    errorBody: "Check your connection and try again.",
    skeletonLabel: "Loading the call",
    sampleRequestId: "REQ-2F8C1",
  },
} as const;

// Technical terms are allowed only inside this block, which appears collapsed in
// the review footer. Keep product copy outside it plain.
export const technicalCopy = {
  heading: "About this review",
  checklistVersion: "Checklist version",
  pipelineVersion: "Review engine version",
  bookVersion: "Book index",
  stageTimes: "Time by stage",
  models: "Models used",
  promptVersions: "Prompt versions",
  examplePipelineVersion: "0.1.0",
  exampleChecklistVersion: "sales_v1, 0.1",
  exampleBookVersion: "Example guide, 2026",
  apiContract: "API contract",
  jsonExport: "JSON export",
  confidenceNote: "Model confidence is shown as Less sure when it is low.",
  workspaceNote: "The workspace is anonymous and tied to the access token.",
  agentNote: "The agent speaker is the sales rep.",
  evidenceNote: "Evidence quotes are matched against the transcript.",
  unverifiedNote: "Unverified findings are omitted from the review.",
} as const;

const errorCodeCopy: Record<string, (context: ErrorContext) => string> = {
  consent_required: () => copy.errors.consentRequired,
  file_too_large: (context) => copy.errors.fileTooLarge(context.maxMb),
  unsupported_media: () => copy.errors.unsupportedMedia,
  invalid_audio: () => copy.errors.invalidAudio,
  audio_too_long: (context) => copy.errors.audioTooLong(context.maxMinutes),
  audio_too_short: (context) => copy.errors.audioTooShort(context.minSeconds),
  quota_exceeded: () => copy.errors.quotaExceeded,
  rate_limited: (context) => copy.errors.rateLimited(context.retryAfterSeconds),
  budget_exceeded: () => copy.errors.budgetExceeded,
  not_ready: () => copy.errors.notReady,
  conflict: () => copy.errors.conflict,
  playbook_unavailable: () => copy.errors.playbookUnavailable,
  service_unavailable: () => copy.errors.serviceUnavailable,
  unauthorized: () => copy.errors.unauthorized,
  internal_error: () => copy.errors.internal,
  transcription_failed: () => copy.errors.job.transcription_failed,
  content_blocked: () => copy.errors.job.content_blocked,
  analysis_failed: () => copy.errors.job.analysis_failed,
  worker_lost: () => copy.errors.job.worker_lost,
};

export function errorMessage(code: string | undefined, context: ErrorContext = {}): string {
  if (!code) return copy.errors.unknown;
  return errorCodeCopy[code]?.(context) ?? copy.errors.unknown;
}

export function retryAfterSeconds(value: number | null | undefined): number | undefined {
  return typeof value === "number" && Number.isFinite(value) && value >= 0
    ? Math.ceil(value)
    : undefined;
}
