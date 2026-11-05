import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import {
  invalidateCall,
  invalidateReport,
  useAudioUrl,
  useCall,
  useFeedback,
  useReport,
} from "@/api/hooks";
import { useDeleteCall, useFindingFeedback, useReanalyseCall } from "@/api/mutations";
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
  const queryClient = useQueryClient();
  const call = useCall(callId);
  const report = useReport(callId);
  const audio = useAudioUrl(callId);
  const feedback = useFeedback(callId);
  const deleteCall = useDeleteCall();
  const reanalyse = useReanalyseCall();
  const progress = useJobEvents(call.data?.job?.id, { enabled: Boolean(call.data?.job?.id) });
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!callId || (progress.status !== "succeeded" && progress.status !== "failed")) return;
    void invalidateCall(queryClient, callId);
    if (progress.status === "succeeded") {
      void invalidateReport(queryClient, callId);
    }
  }, [callId, progress.status, queryClient]);

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
      ) : report.isLoading ? (
        <Skeleton className="mt-8 h-40 w-full" label={copy.callPage.loading} />
      ) : report.isError ? (
        <ErrorState title={copy.callPage.errorTitle} description={copy.callPage.errorBody} action={<Button onClick={() => void report.refetch()}>{copy.common.retry}</Button>} />
      ) : report.data?.status === "insufficient_data" ? (
        <p className="mt-8 max-w-[65ch]">{report.data.reason ?? copy.callPage.insufficient}</p>
      ) : report.data ? (
        <Review
          callId={callId}
          report={report.data}
          audioUrl={audio.data?.url}
          playing={playing}
          setPlaying={setPlaying}
          feedback={feedback.data ?? []}
          onDelete={() => {
            if (window.confirm(copy.callPage.deleteConfirm)) {
              deleteCall.mutate(callId, { onSuccess: () => window.history.back() });
            }
          }}
          onReanalyse={() => reanalyse.mutate(callId)}
          busy={deleteCall.isPending || reanalyse.isPending}
        />
      ) : (
        <p className="mt-8 max-w-[65ch]">{copy.callPage.reviewPending}</p>
      )}
    </div>
  );
}

function Review({
  callId,
  report,
  audioUrl,
  playing,
  setPlaying,
  feedback,
  onDelete,
  onReanalyse,
  busy,
}: {
  callId: string;
  report: NonNullable<ReturnType<typeof useReport>["data"]>;
  audioUrl?: string;
  playing: boolean;
  setPlaying: (value: boolean) => void;
  feedback: Array<{ finding_id: string; verdict: string }>;
  onDelete: () => void;
  onReanalyse: () => void;
  busy: boolean;
}) {
  const score = report.scorecard;
  const audioElement = useRef<HTMLAudioElement>(null);
  const feedbackMutation = useFindingFeedback();
  const [copied, setCopied] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const seek = (seconds: number) => {
    if (audioElement.current) {
      audioElement.current.currentTime = seconds;
      void audioElement.current.play();
    }
  };
  const copyMessage = async () => {
    if (!report.next_steps?.follow_up_message) return;
    try {
      await navigator.clipboard.writeText(report.next_steps.follow_up_message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };
  return (
    <div className="mt-8 space-y-8">
      <p className="text-sm text-muted">{copy.feedback.honesty}</p>
      {audioUrl ? (
        <div className="rounded-card border border-hairline bg-surface p-4">
          <audio ref={audioElement} controls src={audioUrl} className="w-full" onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)} onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} aria-label={copy.callPage.play} />
          <div className="mt-3 h-2 rounded-full bg-wash" aria-label={copy.feedback.approximateTimes}>
            <div className="h-full rounded-full bg-primary" style={{ width: duration ? `${(currentTime / duration) * 100}%` : "0%" }} />
          </div>
          <p className="mt-2 text-sm text-muted">{playing ? copy.callPage.pause : copy.callPage.play} · {copy.feedback.approximateTimes}</p>
        </div>
      ) : null}
      <section aria-labelledby="score-heading">
        <h2 id="score-heading">{copy.callPage.scoreHeading}</h2>
        <div className="mt-4 rounded-card border border-hairline bg-surface p-5">
          <p className="text-4xl font-bold">{score?.overall_score ?? copy.components.scoreUnavailable}</p>
          <p className="mt-1 text-muted">{copy.components.scoreLabel}</p>
          {report.customer_signals?.outcome ? <p className="mt-4"><strong>{copy.labels.outcome}:</strong> {copy.outcome[report.customer_signals.outcome]}</p> : null}
        </div>
      </section>
      {score?.category_scores && Object.keys(score.category_scores).length > 0 ? (
        <section aria-labelledby="categories-heading">
          <h2 id="categories-heading">{copy.callPage.categoryHeading}</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {Object.entries(score.category_scores).map(([name, value]) => (
              <div key={name} className="rounded-card border border-hairline bg-surface p-4">
                <p className="font-bold">{name.replaceAll("_", " ")}</p><p className="mt-1 text-2xl font-bold">{value}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {report.coaching ? (
        <section aria-labelledby="coaching-heading">
          <h2 id="coaching-heading">{copy.callPage.coachingHeading}</h2>
          {report.coaching.strength ? <p className="mt-4 rounded-card border border-hairline bg-surface p-4"><strong>{copy.callPage.strengthHeading}:</strong> {report.coaching.strength}</p> : null}
          <div className="mt-4 space-y-3">{report.coaching.top_fixes?.slice(0, 3).map((fix) => <article key={fix.finding_id} className="rounded-card border border-hairline bg-surface p-4"><p>{fix.explanation}</p><p className="mt-3 text-muted"><strong>{copy.labels.strongerLine}:</strong> {fix.practice_drill}</p></article>)}</div>
        </section>
      ) : null}
      <section aria-labelledby="findings-heading">
        <h2 id="findings-heading">{copy.callPage.findingsHeading}</h2>
        {report.missed_moments?.length ? <div className="mt-4 space-y-4">{report.missed_moments.slice(0, 3).map((finding) => {
          const current = feedback.find((item) => item.finding_id === finding.id)?.verdict;
          return <article key={finding.id} className="rounded-card border border-hairline bg-surface p-4"><p className="font-bold">{finding.category.replaceAll("_", " ")}</p><p className="mt-2">{finding.what_happened}</p>{finding.evidence ? <blockquote className="mt-3 border-l-4 border-highlighter pl-3 text-muted">“{finding.evidence.quote}” <button type="button" className="ml-2 font-bold underline" onClick={() => seek(finding.evidence?.start_s ?? 0)}>at {Math.round(finding.evidence.start_s)}s</button></blockquote> : null}{finding.better_alternative ? <p className="mt-3"><strong>{copy.labels.strongerLine}:</strong> {finding.better_alternative}</p> : null}<div className="mt-4 flex gap-2"><button type="button" className="rounded border border-hairline px-3 py-1 text-sm" aria-pressed={current === "helpful"} disabled={feedbackMutation.isPending} onClick={() => feedbackMutation.mutate({ callId, findingId: finding.id, kind: finding.category, verdict: "helpful" })}>{copy.callPage.helpful}</button><button type="button" className="rounded border border-hairline px-3 py-1 text-sm" aria-pressed={current === "disagree"} disabled={feedbackMutation.isPending} onClick={() => feedbackMutation.mutate({ callId, findingId: finding.id, kind: finding.category, verdict: "disagree" })}>{copy.callPage.disagree}</button></div></article>;
        })}</div> : <p className="mt-4 text-muted">{copy.callPage.noFindings}</p>}
      </section>
      {report.next_steps ? <section aria-labelledby="next-steps-heading"><h2 id="next-steps-heading">{copy.callPage.nextStepsHeading}</h2>{report.next_steps.follow_up_message ? <div className="mt-4 rounded-card border border-hairline bg-surface p-4"><p className="whitespace-pre-wrap">{report.next_steps.follow_up_message}</p><button type="button" className="mt-4 rounded bg-primary px-4 py-2 font-bold text-on-primary" onClick={() => void copyMessage()}>{copied ? copy.callPage.copied : copy.callPage.copyMessage}</button></div> : <p className="mt-4 text-muted">{copy.callPage.nextStepsUnavailable}</p>}<ul className="mt-4 list-disc space-y-2 pl-5">{report.next_steps.recommended_actions?.map((action) => <li key={action}>{action}</li>)}</ul></section> : null}
      {report.transcript?.turns?.length ? <section aria-labelledby="transcript-heading"><h2 id="transcript-heading">{copy.callPage.transcriptHeading}</h2><div className="mt-4 space-y-3">{report.transcript.turns.map((turn) => <p key={turn.id} className="rounded-card border border-hairline p-3"><strong>{turn.speaker}:</strong> {turn.text} <button type="button" className="ml-2 font-bold underline" onClick={() => seek(turn.start_s)}>{Math.round(turn.start_s)}s</button></p>)}</div></section> : null}
      <section className="flex flex-wrap gap-3 border-t border-hairline pt-6"><button type="button" className="rounded border border-hairline px-4 py-2 font-bold" disabled={busy} onClick={onReanalyse}>{copy.callPage.reanalyse}</button><button type="button" className="rounded border border-status-missed px-4 py-2 font-bold text-status-missed" disabled={busy} onClick={onDelete}>{copy.callPage.delete}</button></section>
    </div>
  );
}
