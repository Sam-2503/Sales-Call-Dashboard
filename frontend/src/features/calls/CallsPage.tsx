import { Link, Navigate } from "react-router-dom";

import { useAgents, useCalls, useMeta } from "@/api/hooks";
import { uploadCall } from "@/api/mutations";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, EmptyState, ErrorState, Skeleton } from "@/components";
import { copy } from "@/copy";
import { useState, type FormEvent } from "react";
import { isApiError } from "@/api/errors";
import { errorMessage } from "@/copy";
import { useNavigate } from "react-router-dom";

function statusLabel(status: string): string {
  const value = copy.status[status as keyof typeof copy.status];
  return typeof value === "string" ? value : copy.status.unavailable;
}

export function CallsPage() {
  const accessKey = useAccessKey();
  const calls = useCalls({ limit: 20 });
  const meta = useMeta();
  const agents = useAgents();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [rubricFile, setRubricFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [agentId, setAgentId] = useState("");
  const [consent, setConsent] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  if (!accessKey) return <Navigate to="/" replace />;

  const items = calls.data?.pages.flatMap((page) => page.items) ?? [];

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return setProblem(copy.calls.uploadMissingFile);
    if (!consent) return setProblem(copy.calls.uploadConsent);
    if (rubricFile && !/\.ya?ml$/i.test(rubricFile.name)) {
      return setProblem(copy.errors.invalidRubric);
    }
    setProblem(null);
    setUploading(true);
    try {
      const created = await uploadCall({
        file,
        rubricFile: rubricFile ?? undefined,
        consent,
        title,
        agentId: agentId || undefined,
      });
      await calls.refetch();
      navigate(`/calls/${created.call_id}`);
    } catch (error) {
      setProblem(isApiError(error) ? errorMessage(error.code) : copy.errors.serviceUnavailable);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h1>{copy.calls.title}</h1>
      <p className="mt-3 text-muted">{copy.calls.intro}</p>

      <section className="mt-8 rounded-card border border-hairline bg-surface p-5" aria-labelledby="upload-heading">
        <h2 id="upload-heading">{copy.calls.uploadHeading}</h2>
        <p className="mt-2 text-muted">{copy.calls.uploadBody}</p>
        {meta.data ? (
          <p className="mt-2 text-sm text-muted">
            {copy.calls.uploadLimits(meta.data.max_minutes, meta.data.max_upload_mb)}
          </p>
        ) : null}
        <form className="mt-5 space-y-4" onSubmit={(event) => void submitUpload(event)}>
          <div>
            <label htmlFor="call-file" className="text-sm font-bold">{copy.calls.file}</label>
            <input
              id="call-file"
              type="file"
              accept={meta.data?.allowed_audio_extensions.map((extension) => `.${extension}`).join(",")}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm"
            />
          </div>
          <div>
            <label htmlFor="rubric-file" className="text-sm font-bold">
              {copy.calls.guidelinesLabel}
            </label>
            <p className="mt-1 text-sm text-muted">
              {copy.calls.guidelinesHelp}
            </p>
            <input
              id="rubric-file"
              type="file"
              accept=".yaml,.yml"
              onChange={(event) => setRubricFile(event.target.files?.[0] ?? null)}
              className="mt-1 block w-full text-sm"
            />
            {rubricFile ? (
              <p className="mt-1 text-sm text-muted">
                {copy.calls.selectedGuidelines(rubricFile.name)}
              </p>
            ) : null}
          </div>
          <div>
            <label htmlFor="call-title" className="text-sm font-bold">{copy.calls.titleLabel}</label>
            <input
              id="call-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder={copy.calls.titlePlaceholder}
              className="mt-1 min-h-11 w-full rounded-control border border-hairline bg-paper px-3 py-2"
            />
          </div>
          {agents.data?.length ? (
            <div>
              <label htmlFor="call-rep" className="text-sm font-bold">{copy.calls.repLabel}</label>
              <select id="call-rep" value={agentId} onChange={(event) => setAgentId(event.target.value)} className="mt-1 min-h-11 w-full rounded-control border border-hairline bg-paper px-3 py-2">
                <option value="">{copy.calls.chooseRep}</option>
                {agents.data.map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}
              </select>
            </div>
          ) : null}
          <label className="flex items-start gap-3 text-sm">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 size-4" />
            <span>{copy.calls.consent}<span className="block text-muted">{copy.calls.consentHelp}</span></span>
          </label>
          {problem ? <p role="alert" className="text-sm text-status-missed">{problem}</p> : null}
          <Button type="submit" disabled={uploading}>{uploading ? copy.calls.uploading : copy.calls.submitUpload}</Button>
        </form>
      </section>

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
