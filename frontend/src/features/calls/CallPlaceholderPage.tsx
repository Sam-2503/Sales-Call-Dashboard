import { Link, Navigate, useParams } from "react-router-dom";

import { useCall } from "@/api/hooks";
import { useJobEvents } from "@/api/sse";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, ErrorState, Skeleton } from "@/components";
import { copy } from "@/copy";

function statusLabel(status: string): string {
  const value = copy.status[status as keyof typeof copy.status];
  return typeof value === "string" ? value : copy.status.unavailable;
}

export function CallPlaceholderPage() {
  const { callId } = useParams();
  const accessKey = useAccessKey();
  const call = useCall(callId);
  const progress = useJobEvents(call.data?.job?.id, { enabled: Boolean(call.data?.job?.id) });

  if (!accessKey) return <Navigate to="/" replace />;
  if (!callId) return <Navigate to="/calls" replace />;

  if (call.isLoading) {
    return (
      <div>
        <Skeleton className="h-9 w-2/3" label={copy.callPage.loading} />
        <Skeleton className="mt-4 h-5 w-1/2" label={copy.callPage.loading} />
      </div>
    );
  }

  if (call.isError || !call.data) {
    return (
      <div>
        <ErrorState
          title={copy.callPage.errorTitle}
          description={copy.callPage.errorBody}
          action={<Button onClick={() => void call.refetch()}>{copy.common.retry}</Button>}
        />
        <p className="mt-5 text-sm">
          <Link to="/calls" className="font-bold">
            {copy.callPage.back}
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <p className="text-sm">
        <Link to="/calls" className="font-bold">
          {copy.callPage.back}
        </Link>
      </p>
      <h1 className="mt-4">{call.data.title ?? copy.calls.untitled}</h1>
      <p className="mt-2 text-muted">{statusLabel(call.data.status)}</p>
      {call.data.job?.id && call.data.status !== "completed" ? (
        <section className="mt-8 max-w-[40rem] rounded-card border border-hairline bg-surface p-5" aria-live="polite">
          <p className="font-bold">{progress.status === "queued" ? copy.progress.queued : progress.step}</p>
          <p className="mt-2 text-sm text-muted">{copy.progress.percent(progress.percent)}</p>
          <div className="mt-4 h-3 overflow-hidden rounded-full bg-wash" role="progressbar" aria-valuenow={progress.percent} aria-valuemin={0} aria-valuemax={100} aria-label={copy.progress.percent(progress.percent)}>
            <div className="h-full bg-primary transition-[width]" style={{ width: `${progress.percent}%` }} />
          </div>
          {progress.error ? <p role="alert" className="mt-4 text-status-missed">{progress.error.message}</p> : null}
          <p className="mt-4 text-sm text-muted">{copy.progress.canLeave}</p>
        </section>
      ) : (
        <p className="mt-8 max-w-[65ch]">{copy.callPage.reviewPending}</p>
      )}
    </div>
  );
}
