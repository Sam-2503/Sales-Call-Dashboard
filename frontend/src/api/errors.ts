import { errorMessage, retryAfterSeconds } from "@/copy";

import { clearAccessKey } from "./storage";

const CODE_BY_STATUS: Record<number, string> = {
  400: "validation_error",
  401: "unauthorized",
  403: "not_found",
  404: "not_found",
  409: "conflict",
  413: "file_too_large",
  415: "unsupported_media",
  422: "validation_error",
  429: "rate_limited",
  500: "internal_error",
  503: "service_unavailable",
};

export type ApiErrorInit = {
  code: string;
  message?: string;
  status: number;
  requestId?: string;
  retryAfterSeconds?: number;
  cause?: unknown;
};

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;
  readonly retryAfterSeconds?: number;

  constructor(init: ApiErrorInit) {
    super(init.message ?? errorMessage(init.code));
    this.name = "ApiError";
    this.code = init.code;
    this.status = init.status;
    this.requestId = init.requestId;
    this.retryAfterSeconds = init.retryAfterSeconds;
    if (init.cause !== undefined) this.cause = init.cause;
  }

  static async fromResponse(response: Response, body?: unknown): Promise<ApiError> {
    let payload = body;
    if (payload === undefined) {
      try {
        payload = await response.clone().json();
      } catch {
        payload = undefined;
      }
    }

    const envelope = isRecord(payload) && isRecord(payload.error) ? payload.error : undefined;
    const code =
      (typeof envelope?.code === "string" && envelope.code) ||
      CODE_BY_STATUS[response.status] ||
      "internal_error";
    const message =
      (typeof envelope?.message === "string" && envelope.message) || errorMessage(code);
    const requestId =
      (typeof envelope?.request_id === "string" && envelope.request_id) ||
      response.headers.get("x-request-id") ||
      undefined;
    const retryAfter = retryAfterSeconds(parseRetryAfter(response.headers.get("Retry-After")));

    if (response.status === 401) onUnauthorized();

    return new ApiError({
      code,
      message,
      status: response.status,
      requestId,
      retryAfterSeconds: retryAfter,
    });
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}

export function parseRetryAfter(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = Number(value);
  if (Number.isFinite(seconds)) return Math.max(0, Math.ceil(seconds));
  const date = Date.parse(value);
  if (Number.isNaN(date)) return undefined;
  return Math.max(0, Math.ceil((date - Date.now()) / 1000));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function routeToRestore(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  url.pathname = "/";
  url.search = "";
  url.searchParams.set("restore", "1");
  window.history.pushState({ restore: true }, "", url);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

let unauthorizedHandler: () => void = routeToRestore;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler ?? routeToRestore;
}

function onUnauthorized(): void {
  clearAccessKey();
  unauthorizedHandler();
}
