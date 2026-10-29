import { afterEach, describe, expect, it, vi } from "vitest";

import { request } from "@/api/client";
import { ApiError, parseRetryAfter, routeToRestore, setUnauthorizedHandler } from "@/api/errors";
import { shouldRetry } from "@/api/queryClient";
import { clearAccessKey, getAccessKey, setAccessKey } from "@/api/storage";
import { errorMessage } from "@/copy";

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

function errorResponse(code: string, status = 400, headers: Record<string, string> = {}): Response {
  return new Response(
    JSON.stringify({
      error: { code, message: "The server rejected this request.", request_id: "req-1" },
    }),
    { status, headers: { "Content-Type": "application/json", ...headers } },
  );
}

afterEach(() => {
  clearAccessKey();
  setUnauthorizedHandler(null);
  window.history.replaceState({}, "", "/");
});

describe("API errors", () => {
  it.each(codes)("maps the %s envelope without exposing the raw code as copy", async (code) => {
    const error = await ApiError.fromResponse(errorResponse(code));
    expect(error.code).toBe(code);
    expect(error.requestId).toBe("req-1");
    expect(error.message.length).toBeGreaterThan(0);
    if (code !== "unauthorized") expect(error.message).not.toContain(code);
  });

  it("keeps Retry-After seconds on a 429", async () => {
    const error = await ApiError.fromResponse(
      errorResponse("rate_limited", 429, { "Retry-After": "12" }),
    );
    expect(error.retryAfterSeconds).toBe(12);
    expect(errorMessage(error.code, { retryAfterSeconds: error.retryAfterSeconds })).toContain(
      "12 seconds",
    );
  });

  it("parses both Retry-After forms and rejects nonsense", () => {
    expect(parseRetryAfter("4.2")).toBe(5);
    expect(parseRetryAfter("0")).toBe(0);
    expect(parseRetryAfter("-2")).toBe(0);
    expect(parseRetryAfter("later")).toBeUndefined();
    const future = new Date(Date.now() + 20_000).toUTCString();
    expect(parseRetryAfter(future)).toBeGreaterThan(10);
  });

  it("clears the access key and invokes the restore route once on 401", async () => {
    const restore = vi.fn();
    setUnauthorizedHandler(restore);
    setAccessKey("access-key-123");

    await expect(
      request<never>(
        Promise.resolve({
          response: errorResponse("unauthorized", 401),
          error: { error: { code: "unauthorized", message: "no" } },
        }),
      ),
    ).rejects.toBeInstanceOf(ApiError);

    expect(getAccessKey()).toBeNull();
    expect(restore).toHaveBeenCalledTimes(1);
  });

  it("routes to the welcome restore state without putting a key in the URL", () => {
    window.history.replaceState({}, "", "/calls/123?tab=summary");
    const listener = vi.fn();
    window.addEventListener("popstate", listener);

    routeToRestore();

    expect(window.location.pathname).toBe("/");
    expect(window.location.search).toBe("?restore=1");
    expect(window.location.href).not.toContain("access-key");
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener("popstate", listener);
  });

  it("does not retry a 4xx, but retries a server or network failure", () => {
    expect(shouldRetry(0, new ApiError({ code: "internal_error", status: 400 }))).toBe(false);
    expect(shouldRetry(0, new ApiError({ code: "rate_limited", status: 429 }))).toBe(false);
    expect(shouldRetry(0, new ApiError({ code: "internal_error", status: 500 }))).toBe(true);
    expect(shouldRetry(0, new ApiError({ code: "service_unavailable", status: 0 }))).toBe(true);
    expect(shouldRetry(2, new ApiError({ code: "internal_error", status: 500 }))).toBe(false);
  });

  it("wraps a network failure as a retryable ApiError", async () => {
    await expect(request(Promise.reject(new TypeError("offline")))).rejects.toMatchObject({
      name: "ApiError",
      code: "service_unavailable",
      status: 0,
    });
  });
});
