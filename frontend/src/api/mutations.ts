import { useMutation, useQueryClient } from "@tanstack/react-query";

import { API_BASE, authHeaders, client, request } from "@/api/client";
import { ApiError } from "@/api/errors";
import { clearStoredData, setAccessKey } from "@/api/storage";

import { queryKeys } from "./hooks/keys";
import type { Agent, CallUploadResponse, WorkspaceResponse } from "./hooks/types";

export async function uploadCall(input: {
  file: File;
  consent: boolean;
  title?: string;
  agentId?: string;
}): Promise<CallUploadResponse> {
  const body = new FormData();
  body.append("file", input.file);
  body.append("consent", String(input.consent));
  if (input.title?.trim()) body.append("title", input.title.trim());
  if (input.agentId) body.append("agent_id", input.agentId);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/calls`, {
      method: "POST",
      headers: authHeaders(),
      body,
    });
  } catch (cause) {
    throw new Error("Upload could not reach the service.", { cause });
  }
  if (!response.ok) throw await ApiError.fromResponse(response);
  return (await response.json()) as CallUploadResponse;
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => request<WorkspaceResponse>(client.POST("/api/v1/workspaces")),
    onSuccess: (data) => {
      setAccessKey(data.token);
      queryClient.clear();
    },
  });
}

export function useCreateDemoWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => request<WorkspaceResponse>(client.POST("/api/v1/workspaces/demo")),
    onSuccess: (data) => {
      setAccessKey(data.token);
      queryClient.clear();
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => request<void>(client.DELETE("/api/v1/me")),
    onSuccess: () => {
      clearStoredData();
      queryClient.clear();
    },
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      request<Agent>(
        client.POST("/api/v1/agents", {
          body: { name },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.agents }),
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      request<Agent>(
        client.PATCH("/api/v1/agents/{agent_id}", {
          params: { path: { agent_id: id } },
          body: { name },
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.agents }),
  });
}
