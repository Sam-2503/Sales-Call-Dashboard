import { beforeEach, describe, expect, it } from "vitest";

import { API_BASE } from "@/api/client";
import { mockIds, mockState } from "@/mocks/data";

const auth = { Authorization: "Bearer mock-access-key" };

async function api(path: string, init: RequestInit = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...auth, ...(init.headers ?? {}) },
  });
}

function multipart(name = "call.mp3", consent = "true"): { body: string; contentType: string } {
  const boundary = "----call-review-test-boundary";
  const fields = [
    `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${name}"\r\nContent-Type: audio/mpeg\r\n\r\nsynthetic audio\r\n`,
    `--${boundary}\r\nContent-Disposition: form-data; name="consent"\r\n\r\n${consent}\r\n`,
    `--${boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\nSynthetic upload\r\n`,
    `--${boundary}\r\nContent-Disposition: form-data; name="agent_id"\r\n\r\n${mockIds.me}\r\n`,
    `--${boundary}--\r\n`,
  ];
  return { body: fields.join(""), contentType: `multipart/form-data; boundary=${boundary}` };
}

function uploadRequest(
  name = "call.mp3",
  consent = "true",
  extra: { headers?: Record<string, string> } = {},
) {
  const { body, contentType } = multipart(name, consent);
  return api("/calls", {
    method: "POST",
    headers: { "Content-Type": contentType, ...(extra.headers ?? {}) },
    body,
  });
}

beforeEach(() => {
  mockState.quotaRemaining = 5;
});

describe("MSW API", () => {
  it("serves public metadata, workspaces and reps", async () => {
    const meta = await fetch(`${API_BASE}/meta`);
    expect(meta.status).toBe(200);
    expect(await meta.json()).toMatchObject({ max_minutes: 5, demo_available: true });

    const workspace = await fetch(`${API_BASE}/workspaces`, { method: "POST" });
    expect(workspace.status).toBe(201);
    expect(await workspace.json()).toMatchObject({ token: "mock-access-key" });

    const demo = await fetch(`${API_BASE}/workspaces/demo`, { method: "POST" });
    expect(demo.status).toBe(201);

    const me = await api("/me");
    expect(me.status).toBe(200);
    expect(await me.json()).toMatchObject({ is_demo: true });

    const demoCalls = (await (await api("/calls?limit=100")).json()) as {
      items: Array<{ has_audio: boolean; is_demo: boolean }>;
    };
    expect(demoCalls.items.length).toBeGreaterThan(0);
    expect(demoCalls.items.every((call) => call.is_demo && !call.has_audio)).toBe(true);

    const agents = await api("/agents");
    expect((await agents.json()) as unknown[]).toHaveLength(2);

    const created = await api("/agents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Riley" }),
    });
    expect(created.status).toBe(201);
    const createdAgent = (await created.json()) as { id: string; name: string };
    expect(createdAgent.name).toBe("Riley");

    const renamed = await api(`/agents/${createdAgent.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Riley Chen" }),
    });
    expect(await renamed.json()).toMatchObject({ name: "Riley Chen" });

    const deleted = await api("/me", { method: "DELETE" });
    expect(deleted.status).toBe(204);
  });

  it("serves calls, reports, audio links, feedback and reanalysis", async () => {
    const calls = await api("/calls?limit=2");
    const page = (await calls.json()) as {
      items: Array<{ status: string }>;
      next_cursor: string | null;
    };
    expect(page.items).toHaveLength(2);
    expect(page.next_cursor).toBe("2");

    const everyStatus = (await (await api("/calls?limit=100")).json()) as {
      items: Array<{ status: string }>;
    };
    expect(new Set(everyStatus.items.map((call) => call.status))).toEqual(
      new Set(["completed", "processing", "queued", "failed"]),
    );

    const pageTwo = await api(`/calls?limit=2&cursor=${page.next_cursor}`);
    expect(((await pageTwo.json()) as { items: unknown[] }).items.length).toBeGreaterThan(0);

    const filtered = await api(`/calls?agent_id=${mockIds.alex}`);
    expect((await filtered.json()) as { items: Array<{ agent_name: string }> }).toMatchObject({
      items: [expect.objectContaining({ agent_name: "Alex" })],
    });

    const detail = await api(`/calls/${mockIds.fullCall}`);
    expect(await detail.json()).toMatchObject({ title: "Cold call with Acme", has_audio: true });

    const report = await api(`/calls/${mockIds.fullCall}/report`);
    expect(report.status).toBe(200);
    expect(await report.json()).toMatchObject({ status: "ok" });
    expect(report.headers.get("cache-control")).toBe("no-store");

    const shortReport = await api(`/calls/${mockIds.shortCall}/report`);
    expect(await shortReport.json()).toMatchObject({ status: "insufficient_data" });

    const audio = await api(`/calls/${mockIds.fullCall}/audio-url`);
    expect(await audio.json()).toMatchObject({ url: expect.stringContaining("/media/audio") });

    const feedback = await api(`/calls/${mockIds.fullCall}/feedback`);
    expect((await feedback.json()) as unknown[]).toHaveLength(1);

    const saved = await api(`/calls/${mockIds.fullCall}/feedback/moment-discovery-impact`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: "moment", verdict: "disagree", comment: "Not right." }),
    });
    expect(saved.status).toBe(200);
    expect(await saved.json()).toMatchObject({ verdict: "disagree", comment: "Not right." });

    const removed = await api(`/calls/${mockIds.fullCall}/feedback/moment-discovery-impact`, {
      method: "DELETE",
    });
    expect(removed.status).toBe(204);

    const reanalysis = await api(`/calls/${mockIds.fullCall}/reanalyse`, { method: "POST" });
    expect(reanalysis.status).toBe(202);
    expect(await reanalysis.json()).toMatchObject({ status: "queued" });

    const deleted = await api(`/calls/${mockIds.failedCall}`, { method: "DELETE" });
    expect(deleted.status).toBe(204);
    expect((await api(`/calls/${mockIds.failedCall}`)).status).toBe(404);
  });

  it("uploads a call and exposes job progress and SSE terminal events", async () => {
    const uploadResponse = await uploadRequest();
    expect(uploadResponse.status).toBe(202);
    const created = (await uploadResponse.json()) as { call_id: string; job_id: string };
    expect(created.call_id).toBeTruthy();
    expect(created.job_id).toBeTruthy();

    const job = await api(`/jobs/${created.job_id}`);
    expect(job.status).toBe(200);
    expect(await job.json()).toMatchObject({
      status: expect.stringMatching(/queued|processing|succeeded/),
    });

    const done = await api(`/jobs/${mockIds.fullJob}/events`);
    expect(done.headers.get("content-type")).toContain("text/event-stream");
    expect(await done.text()).toContain("event: done");

    const failed = await api(`/jobs/${mockIds.failedJob}/events`);
    expect(await failed.text()).toContain("event: error");

    const reportBeforeReady = await api(`/calls/${mockIds.queuedCall}/report`);
    expect(reportBeforeReady.status).toBe(409);
  });

  it("serves trends, weak spots and benchmarks", async () => {
    const scores = await api("/trends/scores");
    expect(scores.status).toBe(200);
    expect(await scores.json()).toMatchObject({ n: expect.any(Number) });

    const weak = await api("/trends/weak-spots?last_n=5");
    expect(await weak.json()).toMatchObject({
      available: false,
      reason: expect.stringContaining("3"),
    });

    const benchmark = await api(`/benchmarks?call_id=${mockIds.fullCall}`);
    expect(benchmark.status).toBe(200);
    expect(await benchmark.json()).toMatchObject({
      overall: { agent_best: 82, team_average: 71 },
    });
  });

  it("serves the plain error cases", async () => {
    const unauthorized = await fetch(`${API_BASE}/me`);
    expect(unauthorized.status).toBe(401);
    expect(await unauthorized.json()).toMatchObject({
      error: { code: "unauthorized", request_id: "mock-request-id" },
    });

    const noConsent = await uploadRequest("call.mp3", "false");
    expect(noConsent.status).toBe(400);
    expect(await noConsent.json()).toMatchObject({ error: { code: "consent_required" } });

    const wrongType = await uploadRequest("call.txt");
    expect(wrongType.status).toBe(415);
    expect(await wrongType.json()).toMatchObject({ error: { code: "unsupported_media" } });

    const limited = await uploadRequest("call.mp3", "true", {
      headers: { "x-mock-rate-limit": "1" },
    });
    expect(limited.status).toBe(429);
    expect(limited.headers.get("retry-after")).toBe("12");

    mockState.quotaRemaining = 0;
    const quota = await uploadRequest();
    expect(quota.status).toBe(429);
    expect(await quota.json()).toMatchObject({ error: { code: "quota_exceeded" } });

    const notReady = await api(`/calls/${mockIds.queuedCall}/report`);
    expect(notReady.status).toBe(409);
    expect(await notReady.json()).toMatchObject({ error: { code: "not_ready" } });
  });
});
