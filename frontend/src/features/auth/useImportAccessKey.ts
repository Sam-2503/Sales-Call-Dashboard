import { useQueryClient } from "@tanstack/react-query";

import { client, request } from "@/api/client";
import { isApiError } from "@/api/errors";
import { clearAccessKey, importAccessKey } from "@/api/storage";
import type { WorkspaceInfo } from "@/api/hooks/types";
import { copy, errorMessage } from "@/copy";

export function useImportAccessKey() {
  const queryClient = useQueryClient();

  return async (value: string): Promise<string | null> => {
    if (!importAccessKey(value)) return copy.welcome.keyInvalid;

    try {
      await request<WorkspaceInfo>(client.GET("/api/v1/me"));
    } catch (error) {
      clearAccessKey();
      if (isApiError(error) && error.status === 401) return copy.welcome.keyInvalid;
      return errorMessage(isApiError(error) ? error.code : undefined);
    }

    queryClient.clear();
    return null;
  };
}
