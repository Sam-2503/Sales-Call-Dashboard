import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams, Link } from "react-router-dom";

import { client, request } from "@/api/client";
import { isApiError } from "@/api/errors";
import { useMeta } from "@/api/hooks";
import type { CallListResponse } from "@/api/hooks/types";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, ErrorState, Skeleton } from "@/components";
import { copy, errorMessage } from "@/copy";
import { useCreateDemoWorkspace, useCreateWorkspace } from "@/api/mutations";

import { AccessKeyDialog } from "@/features/auth/AccessKeyDialog";
import { useImportAccessKey } from "@/features/auth/useImportAccessKey";

function actionError(error: unknown): string {
  return isApiError(error) ? errorMessage(error.code) : copy.errors.unknown;
}

export function WelcomePage() {
  const accessKey = useAccessKey();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const meta = useMeta();
  const createWorkspace = useCreateWorkspace();
  const createDemo = useCreateDemoWorkspace();
  const importAccessKey = useImportAccessKey();
  const [restoreOpen, setRestoreOpen] = useState(searchParams.get("restore") === "1");
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get("restore") === "1" && !accessKey) setRestoreOpen(true);
  }, [accessKey, searchParams]);

  if (accessKey && !createWorkspace.isPending && !createDemo.isPending) {
    return <Navigate to="/calls" replace />;
  }

  function closeRestore(open: boolean) {
    setRestoreOpen(open);
    if (!open && searchParams.has("restore")) {
      const next = new URLSearchParams(searchParams);
      next.delete("restore");
      setSearchParams(next, { replace: true });
    }
  }

  async function startWorkspace() {
    setProblem(null);
    try {
      await createWorkspace.mutateAsync();
      navigate("/calls", { replace: true });
    } catch (error) {
      setProblem(actionError(error));
    }
  }

  async function startDemo() {
    setProblem(null);
    try {
      await createDemo.mutateAsync();
      const calls = await request<CallListResponse>(
        client.GET("/api/v1/calls", { params: { query: { limit: 1 } } }),
      );
      const first = calls.items[0];
      if (first) navigate(`/calls/${first.id}`, { replace: true });
      else navigate("/calls", { replace: true });
    } catch (error) {
      setProblem(actionError(error));
    }
  }

  async function handleAccessKey(value: string): Promise<string | null> {
    const result = await importAccessKey(value);
    if (!result) {
      queryClient.clear();
      navigate("/calls", { replace: true });
    }
    return result;
  }

  const busy = createWorkspace.isPending || createDemo.isPending;

  return (
    <div className="max-w-[65ch]">
      <h1>{copy.welcome.headline}</h1>
      <p className="mt-4 text-muted">{copy.welcome.intro}</p>

      {problem ? (
        <p role="alert" className="mt-5 text-status-missed">
          {problem}
        </p>
      ) : null}

      <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:flex-wrap">
        <Button onClick={() => void startWorkspace()} disabled={busy}>
          {createWorkspace.isPending ? copy.welcome.starting : copy.welcome.upload}
        </Button>
        {meta.data?.demo_available ? (
          <Button variant="secondary" onClick={() => void startDemo()} disabled={busy}>
            {createDemo.isPending ? copy.welcome.openingSample : copy.welcome.trySample}
          </Button>
        ) : null}
        <AccessKeyDialog
          open={restoreOpen}
          onOpenChange={closeRestore}
          onSubmit={handleAccessKey}
          trigger={
            <Button variant="quiet" disabled={busy}>
              {copy.welcome.haveKey}
            </Button>
          }
        />
      </div>

      {meta.isLoading ? (
        <div className="mt-8 space-y-2">
          <Skeleton className="h-5 w-3/4" label={copy.common.loading} />
          <Skeleton className="h-5 w-1/2" label={copy.common.loading} />
        </div>
      ) : meta.isError ? (
        <div className="mt-8">
          <ErrorState
            title={copy.welcome.metaErrorTitle}
            description={copy.welcome.metaErrorBody}
            action={<Button onClick={() => void meta.refetch()}>{copy.common.retry}</Button>}
          />
        </div>
      ) : meta.data ? (
        <div className="mt-10 border-t border-hairline pt-5">
          <p className="text-sm text-muted">
            {copy.welcome.privacyRetention(meta.data.retention_days)}
          </p>
          <p className="mt-2 text-sm text-muted">{copy.welcome.privacyKey}</p>
        </div>
      ) : null}

      <p className="mt-8 text-sm">
        <Link to="/how-it-works" className="font-bold">
          {copy.shell.footer}
        </Link>
      </p>
    </div>
  );
}
