import { useMutation, useQueryClient } from "@tanstack/react-query";

import { client, request } from "@/api/client";
import { clearStoredData, setAccessKey } from "@/api/storage";

import { queryKeys } from "./hooks/keys";
import type { Agent, WorkspaceResponse } from "./hooks/types";

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
