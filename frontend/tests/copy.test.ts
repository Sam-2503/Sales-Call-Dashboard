import { describe, expect, it } from "vitest";

import { copy, errorMessage, retryAfterSeconds } from "@/copy";

const codes = [
  "consent_required",
  "file_too_large",
  "unsupported_media",
  "invalid_audio",
  "audio_too_long",
  "audio_too_short",
  "quota_exceeded",
  "rate_limited",
  "budget_exceeded",
  "not_ready",
  "conflict",
  "playbook_unavailable",
  "service_unavailable",
  "unauthorized",
  "internal_error",
  "transcription_failed",
  "content_blocked",
  "analysis_failed",
  "worker_lost",
];

describe("plain-language copy", () => {
  it.each(codes)("maps %s to a sentence without the raw error code", (code) => {
    const message = errorMessage(code);
    expect(message.length).toBeGreaterThan(0);
    expect(message).not.toContain(code);
    expect(message).not.toMatch(/[a-z]+_[a-z]+/);
  });

  it("uses the limits and retry delay it is given", () => {
    expect(errorMessage("file_too_large", { maxMb: 25 })).toContain("25 MB");
    expect(errorMessage("audio_too_long", { maxMinutes: 5 })).toContain("5 minutes");
    expect(errorMessage("audio_too_short", { minSeconds: 20 })).toContain("20 seconds");
    expect(errorMessage("rate_limited", { retryAfterSeconds: 30 })).toContain("30 seconds");
    expect(errorMessage("rate_limited", { retryAfterSeconds: 1 })).toContain("1 second");
  });

  it("uses the review language for the progress steps", () => {
    expect(copy.progress.steps).toEqual([
      "Listening to the call",
      "Measuring the conversation",
      "Checking it against your checklist",
      "Finding stronger ways to say it",
      "Putting it together",
    ]);
    expect(copy.progress.queuedAhead(1)).toBe("1 call ahead of you");
    expect(copy.progress.queuedAhead(4)).toBe("4 calls ahead of you");
  });

  it("uses the honesty note once and explains omitted findings", () => {
    expect(copy.feedback.honesty.match(/\bAI\b/g)).toHaveLength(1);
    expect(copy.feedback.leftOut(1)).toContain("1 finding");
    expect(copy.feedback.leftOut(3)).toContain("3 findings");
  });

  it("keeps the plain labels for checklist states", () => {
    expect(copy.status.done).toBe("Done");
    expect(copy.status.partly).toBe("Partly done");
    expect(copy.status.missed).toBe("Missed");
    expect(copy.status.notApplicable).toBe("Didn't apply");
    expect(copy.outcome.advanced).toBe("Moving forward");
  });

  it("parses Retry-After values without accepting nonsense", () => {
    expect(retryAfterSeconds(3.2)).toBe(4);
    expect(retryAfterSeconds(0)).toBe(0);
    expect(retryAfterSeconds(-1)).toBeUndefined();
    expect(retryAfterSeconds(Number.NaN)).toBeUndefined();
    expect(retryAfterSeconds(null)).toBeUndefined();
  });
});
