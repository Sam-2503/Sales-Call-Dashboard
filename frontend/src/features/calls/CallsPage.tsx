import { Link, Navigate } from "react-router-dom";

import { useCalls } from "@/api/hooks";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, EmptyState, ErrorState, Skeleton } from "@/components";
import { copy } from "@/copy";

function statusLabel(status: string): string {
  const value = copy.status[status as keyof typeof copy.status];
  return typeof value === "string" ? value : copy.status.unavailable;
}

export function CallsPage() {
  const accessKey = useAccessKey();
  const calls = useCalls({ limit: 20 });

  if (!accessKey) return <Navigate to="/" replace />;

  const items = calls.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <div>
      <h1>{copy.calls.title}</h1>
      <p className="mt-3 text-muted">{copy.calls.intro}</p>

      {calls.isLoading ? (
        <div className="mt-8 space-y-3">
          <Skeleton className="h-12 w-full" label={copy.calls.loading} />
          <Skeleton className="h-12 w-full" label={copy.calls.loading} />
        </div>
      ) : calls.isError ? (
        <div className="mt-8">
          <ErrorState
            title={copy.calls.errorTitle}
            description={copy.calls.errorBody}
            action={<Button onClick={() => void calls.refetch()}>{copy.common.retry}</Button>}
          />
        </div>
      ) : items.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title={copy.calls.emptyTitle}
            description={copy.calls.emptyBody}
            action={
              <Button variant="quiet" asChild>
                <Link to="/how-it-works">{copy.shell.footer}</Link>
              </Button>
            }
          />
        </div>
      ) : (
        <div className="mt-8">
          <p className="text-sm text-muted">{copy.calls.count(items.length)}</p>
          <ul className="mt-2 divide-y divide-hairline border-y border-hairline">
            {items.map((call) => (
              <li key={call.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div>
                  <Link to={`/calls/${call.id}`} className="font-bold">
                    {call.title ?? copy.calls.untitled}
                  </Link>
                  <p className="mt-1 text-sm text-muted">{statusLabel(call.status)}</p>
                </div>
                <Link to={`/calls/${call.id}`} className="text-sm font-bold">
                  {copy.calls.open}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
