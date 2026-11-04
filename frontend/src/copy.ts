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
    main: "Main",
    calls: "Calls",
    progress: "Progress",
    settings: "Settings",
  },
  theme: {
    label: "Colour theme",
    system: "System",
    light: "Light",
    dark: "Dark",
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
  shell: {
    offlineTitle: "You're offline",
    offlineBody: "Some things won't load until you reconnect.",
    storageTitle: "This browser can't remember you",
    storageBody: "Keep this tab open, or copy your access key before you close it.",
    embeddedTitle: "Open this app in its own tab",
    embeddedBody:
      "Embedded windows can block saved access. Open in a new tab so we can remember you.",
    openNewTab: "Open in a new tab",
    copyKey: "Copy access key",
    footer: "How this works",
    errorTitle: "Something went wrong",
    errorBody: "Reload the page to try again. Your saved calls are not affected.",
    reload: "Reload page",
  },
  welcome: {
    headline: "Know what to fix before your next call.",
    intro:
      "Upload a short cold call and get a clear review: what worked, what to try next, and the exact line to say.",
    upload: "Upload a call",
    trySample: "Try a sample review",
    haveKey: "I have an access key",
    starting: "Starting...",
    openingSample: "Opening the sample...",
    privacyRetention: (days: number) => `Calls are deleted after ${days} days.`,
    privacyKey: "Your access key is the only way back to these calls on another device or browser.",
    keyTitle: "Enter your access key",
    keyBody: "Paste the key you saved when you started. It opens your calls on this browser.",
    keyLabel: "Access key",
    keyPlaceholder: "Paste your access key",
    keySubmit: "Open my calls",
    keyChecking: "Checking...",
    keyInvalid: "That access key doesn't work. Paste the whole key and try again.",
    keyCancel: "Cancel",
    metaErrorTitle: "We couldn't load the limits",
    metaErrorBody: "Check your connection and try again.",
  },
  settings: {
    title: "Settings",
    intro: "Manage the reps, your access key and what this browser keeps.",
    repsHeading: "Reps",
    repsBody: "Add the people whose calls you review.",
    addRep: "Add a rep",
    repName: "Rep's name",
    addSubmit: "Add rep",
    adding: "Adding...",
    renameRep: "Rename rep",
    rename: "Rename",
    saveName: "Save name",
    saving: "Saving...",
    repAdded: "Rep added.",
    repRenamed: "Rep name saved.",
    repsErrorTitle: "We couldn't load your reps",
    repsErrorBody: "Check your connection and try again.",
    repError: "That didn't save. Try again.",
    accessHeading: "Access key",
    accessBody:
      "This key is the only way back to these calls on another device or browser. Keep it somewhere safe.",
    maskedKey: "••••••••",
    copyKey: "Copy access key",
    differentKey: "Use a different access key",
    keyChanged: "Access key changed.",
    deleteHeading: "Delete all my data",
    deleteBody:
      "This removes every call, its audio, its review and your access key from this browser. You can't undo this.",
    deleteButton: "Delete all my data",
    deleteTitle: "Delete all your calls?",
    deleteConfirmBody:
      "This removes every call, its audio, its review and the saved access key from this browser. You can't undo this.",
    deleting: "Deleting...",
    deleted: "All your data was deleted.",
    deleteError: "That didn't delete. Try again.",
    themeHeading: "Colour theme",
    privacyHeading: "What we keep",
    privacyRetention: (days: number) =>
      `Calls are kept for ${days} days, then deleted automatically.`,
    privacyKey: "Your access key is saved in this browser so you can come back.",
    privacyDelete: "Use Delete all my data to remove everything now.",
  },
  howItWorks: {
    title: "How this works",
    intro:
      "A short review of one cold call, with the moments that mattered and what to try next time.",
    looksHeading: "What the review looks at",
    looksBody:
      "We check the call against a short checklist, then point to the exact moments that helped or got in the way.",
    categoriesLabel: "The checklist covers",
    quotesHeading: "How quotes are checked",
    quotesBody:
      "Every quote shown in a review is checked against the transcript. If we can't confirm it, we leave it out.",
    adviceHeading: "Where the advice comes from",
    adviceBody:
      "The advice comes from what happened on the call, plus a book of sales guidance when it is available.",
    adviceNoBook:
      "The review uses what happened on the call. Book guidance isn't available right now.",
    errorTitle: "We couldn't load this page",
    errorBody: "Check your connection and try again.",
  },
  calls: {
    title: "Your calls",
    intro: "Calls you have added on this browser.",
    loading: "Loading your calls",
    emptyTitle: "No calls yet",
    emptyBody: "Your calls will appear here after you upload one.",
    errorTitle: "We couldn't load your calls",
    errorBody: "Check your connection and try again.",
    count: (count: number) => (count === 1 ? "1 call" : `${count} calls`),
    open: "Open call",
    untitled: "Untitled call",
  },
  callPage: {
    loading: "Loading the call",
    errorTitle: "We couldn't open this call",
    errorBody: "Check your connection and try again.",
    reviewPending: "The review will appear here when it is ready.",
    back: "Back to calls",
  },
  progressPage: {
    title: "Progress",
    intro: "See how your scores change and what keeps coming up.",
    empty: "Your progress will appear after you review a few calls.",
  },
  notFound: {
    title: "This page isn't here",
    body: "Check the address or go back to your calls.",
    action: "Go to calls",
  },
  routeError: {
    title: "This page didn't load",
    body: "Reload the page to try again.",
    reload: "Reload page",
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
  bookTitle: "Book title",
  notAvailable: "Not available",
  stageTimes: "Time by stage",
  models: "Models used",
  promptVersions: "Prompt versions",
  analysisModel: "Analysis model",
  fastModel: "Fast model",
  transcriptionModel: "Transcription model",
  embeddingModel: "Embedding model",
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
