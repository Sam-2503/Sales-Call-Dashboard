import { Navigate } from "react-router-dom";

import { useTrendsScores, useWeakSpots } from "@/api/hooks";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, ErrorState, Skeleton } from "@/components";
import { copy } from "@/copy";

export function ProgressPage() {
  const accessKey = useAccessKey();
  const scores = useTrendsScores();
  const weakSpots = useWeakSpots();

  if (!accessKey) return <Navigate to="/" replace />;
  if (scores.isLoading || weakSpots.isLoading) {
    return (
      <div>
        <h1>{copy.progressPage.title}</h1>
        <Skeleton className="mt-8 h-48 w-full" label={copy.progressPage.loading} />
      </div>
    );
  }
  if (scores.isError || weakSpots.isError) {
    return (
      <ErrorState
        title={copy.progressPage.errorTitle}
        description={copy.progressPage.errorBody}
        action={
          <Button
            onClick={() => {
              void scores.refetch();
              void weakSpots.refetch();
            }}
          >
            {copy.common.retry}
          </Button>
        }
      />
    );
  }

  const points = scores.data?.points.filter((point) => point.overall_score !== null) ?? [];
  const maximum = Math.max(...points.map((point) => point.overall_score ?? 0), 100);
  const minimum = Math.min(...points.map((point) => point.overall_score ?? 100), 0);

  return (
    <div className="max-w-[65ch]">
      <h1>{copy.progressPage.title}</h1>
      <p className="mt-3 text-muted">{copy.progressPage.intro}</p>
      {points.length === 0 ? (
        <p className="mt-8">{copy.progressPage.empty}</p>
      ) : (
        <section className="mt-8" aria-labelledby="score-history-heading">
          <h2 id="score-history-heading">{copy.progressPage.scoreHistory}</h2>
          <p className="mt-2 text-muted">{copy.progressPage.scoreHistoryBody}</p>
          <div className="mt-4 space-y-3">
            {points.map((point) => (
              <div key={point.call_id} className="rounded-card border border-hairline bg-surface p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-bold">{point.title ?? copy.calls.untitled}</span>
                  <span className="tabular text-2xl font-bold">{point.overall_score}</span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-wash">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${((point.overall_score ?? 0) / maximum) * 100}%` }}
                  />
                </div>
                <p className="mt-2 text-sm text-muted">
                  {minimum} to {maximum} is the range shown here.
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="mt-10" aria-labelledby="weak-spots-heading">
        <h2 id="weak-spots-heading">{copy.progressPage.weakSpots}</h2>
        {weakSpots.data?.available ? (
          <ul className="mt-4 space-y-3">
            {weakSpots.data.items.slice(0, 3).map((spot) => (
              <li key={spot.item_id} className="rounded-card border border-hairline bg-surface p-4">
                <p className="font-bold">{spot.title}</p>
                <p className="mt-1 text-muted">
                  {spot.missed_calls} of {spot.applicable_calls} calls missed this.
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 text-muted">
            {weakSpots.data?.reason ?? copy.progressPage.weakSpotsUnavailable}
          </p>
        )}
      </section>
    </div>
  );
}
