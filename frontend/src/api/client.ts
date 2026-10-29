import createClient from "openapi-fetch";

import { errorMessage } from "@/copy";

import { ApiError } from "./errors";
import type { paths } from "./schema";
import { getAccessKey } from "./storage";

function apiRoot(): string {
  const configured = import.meta.env.VITE_API_BASE?.trim();
  const origin = typeof window === "undefined" ? "" : window.location.origin;
  if (!configured) return origin;

  try {
    const url = new URL(configured, origin || undefined);
    const path = url.pathname.replace(/\/api\/v1\/?$/, "").replace(/\/+$/, "");
    return `${url.origin}${path}`;
  } catch {
    return origin;
  }
}

export const API_ROOT = apiRoot();
export const API_BASE = `${API_ROOT}/api/v1`;

export const client = createClient<paths>({
  baseUrl: API_ROOT,
  credentials: "same-origin",
});

client.use({
  onRequest({ request }) {
    const accessKey = getAccessKey();
    if (accessKey) request.headers.set("Authorization", `Bearer ${accessKey}`);
    return request;
  },
});

export type ApiResult<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

export async function request<T>(operation: Promise<ApiResult<unknown>>): Promise<T> {
  let result: ApiResult<unknown>;
  try {
    result = await operation;
  } catch (cause) {
    throw new ApiError({
      code: "service_unavailable",
      message: errorMessage("service_unavailable"),
      status: 0,
      cause,
    });
  }

  if (result.error !== undefined || !result.response.ok) {
    throw await ApiError.fromResponse(result.response, result.error);
  }

  return result.data as T;
}

export function authHeaders(): Record<string, string> {
  const accessKey = getAccessKey();
  return accessKey ? { Authorization: `Bearer ${accessKey}` } : {};
}
