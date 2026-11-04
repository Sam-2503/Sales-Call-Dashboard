import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { isApiError } from "@/api/errors";
import { useAgents, useMeta } from "@/api/hooks";
import type { Agent } from "@/api/hooks/types";
import { useCreateAgent, useDeleteWorkspace, useUpdateAgent } from "@/api/mutations";
import { useAccessKey } from "@/api/useAccessKey";
import { Button, CopyButton, Dialog, ErrorState, Skeleton, useToast } from "@/components";
import { copy, errorMessage } from "@/copy";
import { ThemeSwitcher } from "@/theme/ThemeSwitcher";
import { useTheme } from "@/theme/useTheme";

import { AccessKeyDialog } from "@/features/auth/AccessKeyDialog";
import { useImportAccessKey } from "@/features/auth/useImportAccessKey";

function messageFor(error: unknown): string {
  return isApiError(error) ? errorMessage(error.code) : copy.errors.unknown;
}

export function SettingsPage() {
  const accessKey = useAccessKey();
  const navigate = useNavigate();
  const meta = useMeta();
  const agents = useAgents();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();
  const deleteWorkspace = useDeleteWorkspace();
  const importAccessKey = useImportAccessKey();
  const { showToast } = useToast();
  const { preference, setPreference } = useTheme();

  const [newRep, setNewRep] = useState("");
  const [repProblem, setRepProblem] = useState<string | null>(null);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [keyOpen, setKeyOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteProblem, setDeleteProblem] = useState<string | null>(null);

  if (!accessKey) return <Navigate to="/" replace />;

  async function addRep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newRep.trim();
    if (!name) return;
    setRepProblem(null);
    try {
      await createAgent.mutateAsync(name);
      setNewRep("");
      showToast({ title: copy.settings.repAdded, tone: "success" });
    } catch (error) {
      setRepProblem(messageFor(error));
    }
  }

  function openRename(agent: Agent) {
    setEditing(agent);
    setRenameValue(agent.name);
    setRepProblem(null);
  }

  async function renameRep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const name = renameValue.trim();
    if (!name) return;
    setRepProblem(null);
    try {
      await updateAgent.mutateAsync({ id: editing.id, name });
      setEditing(null);
      showToast({ title: copy.settings.repRenamed, tone: "success" });
    } catch (error) {
      setRepProblem(messageFor(error));
    }
  }

  async function changeKey(value: string): Promise<string | null> {
    const result = await importAccessKey(value);
    if (!result) {
      showToast({ title: copy.settings.keyChanged, tone: "success" });
      navigate("/calls", { replace: true });
    }
    return result;
  }

  async function deleteEverything() {
    setDeleteProblem(null);
    try {
      await deleteWorkspace.mutateAsync();
      showToast({ title: copy.settings.deleted, tone: "success" });
      navigate("/", { replace: true });
    } catch (error) {
      setDeleteProblem(messageFor(error));
    }
  }

  const reps = agents.data ?? [];

  return (
    <div>
      <h1>{copy.settings.title}</h1>
      <p className="mt-3 text-muted">{copy.settings.intro}</p>

      <section aria-labelledby="reps-heading" className="mt-10 border-t border-hairline pt-8">
        <h2 id="reps-heading">{copy.settings.repsHeading}</h2>
        <p className="mt-2 text-muted">{copy.settings.repsBody}</p>

        <form
          onSubmit={(event) => void addRep(event)}
          className="mt-5 flex flex-wrap items-end gap-3"
        >
          <div className="min-w-[12rem] flex-1">
            <label htmlFor="new-rep" className="text-sm font-bold">
              {copy.settings.repName}
            </label>
            <input
              id="new-rep"
              value={newRep}
              onChange={(event) => setNewRep(event.target.value)}
              className="mt-1 min-h-11 w-full rounded-control border border-hairline bg-surface px-3 py-2 text-ink focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus"
            />
          </div>
          <Button type="submit" disabled={createAgent.isPending || !newRep.trim()}>
            {createAgent.isPending ? copy.settings.adding : copy.settings.addSubmit}
          </Button>
        </form>

        {repProblem ? (
          <p role="alert" className="mt-3 text-sm text-status-missed">
            {repProblem}
          </p>
        ) : null}

        {agents.isLoading ? (
          <div className="mt-5 space-y-2">
            <Skeleton className="h-10 w-full" label={copy.settings.repsHeading} />
            <Skeleton className="h-10 w-2/3" label={copy.settings.repsHeading} />
          </div>
        ) : agents.isError ? (
          <div className="mt-5">
            <ErrorState
              title={copy.settings.repsErrorTitle}
              description={copy.settings.repsErrorBody}
              action={<Button onClick={() => void agents.refetch()}>{copy.common.retry}</Button>}
            />
          </div>
        ) : (
          <ul className="mt-5 divide-y divide-hairline border-y border-hairline">
            {reps.map((agent) => (
              <li key={agent.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <span>{agent.name}</span>
                <Button
                  variant="quiet"
                  size="sm"
                  onClick={() => openRename(agent)}
                  aria-label={`${copy.settings.renameRep}: ${agent.name}`}
                >
                  {copy.settings.rename}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="key-heading" className="mt-10 border-t border-hairline pt-8">
        <h2 id="key-heading">{copy.settings.accessHeading}</h2>
        <p className="mt-2 max-w-[65ch] text-muted">{copy.settings.accessBody}</p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <code className="rounded-control border border-hairline bg-wash px-3 py-2 text-sm tracking-widest">
            {copy.settings.maskedKey}
          </code>
          <CopyButton value={accessKey} label={copy.settings.copyKey} />
          <AccessKeyDialog
            open={keyOpen}
            onOpenChange={setKeyOpen}
            onSubmit={changeKey}
            trigger={<Button variant="quiet">{copy.settings.differentKey}</Button>}
          />
        </div>
      </section>

      <section aria-labelledby="theme-heading" className="mt-10 border-t border-hairline pt-8">
        <h2 id="theme-heading">{copy.settings.themeHeading}</h2>
        <div className="mt-4">
          <ThemeSwitcher preference={preference} onChange={setPreference} />
        </div>
      </section>

      <section aria-labelledby="privacy-heading" className="mt-10 border-t border-hairline pt-8">
        <h2 id="privacy-heading">{copy.settings.privacyHeading}</h2>
        {meta.isLoading ? (
          <Skeleton className="mt-3 h-5 w-3/4" label={copy.common.loading} />
        ) : meta.data ? (
          <div className="mt-3 space-y-2 text-muted">
            <p>{copy.settings.privacyRetention(meta.data.retention_days)}</p>
            <p>{copy.settings.privacyKey}</p>
            <p>{copy.settings.privacyDelete}</p>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="delete-heading" className="mt-10 border-t border-hairline pt-8">
        <h2 id="delete-heading">{copy.settings.deleteHeading}</h2>
        <p className="mt-2 max-w-[65ch] text-muted">{copy.settings.deleteBody}</p>
        <Button
          variant="secondary"
          className="mt-4 border-status-missed text-status-missed"
          onClick={() => {
            setDeleteProblem(null);
            setDeleteOpen(true);
          }}
        >
          {copy.settings.deleteButton}
        </Button>
      </section>

      <Dialog
        open={editing !== null}
        onOpenChange={(open) => {
          if (!open) setEditing(null);
        }}
        title={copy.settings.renameRep}
        description={copy.settings.repsBody}
        footer={
          <>
            <Button variant="quiet" onClick={() => setEditing(null)}>
              {copy.common.cancel}
            </Button>
            <Button type="submit" form="rename-rep-form" disabled={updateAgent.isPending}>
              {updateAgent.isPending ? copy.settings.saving : copy.settings.saveName}
            </Button>
          </>
        }
      >
        <form id="rename-rep-form" onSubmit={(event) => void renameRep(event)}>
          <label htmlFor="rename-rep" className="text-sm font-bold">
            {copy.settings.repName}
          </label>
          <input
            id="rename-rep"
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            className="mt-1 min-h-11 w-full rounded-control border border-hairline bg-paper px-3 py-2 text-ink focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus"
          />
        </form>
      </Dialog>

      <Dialog
        open={deleteOpen}
        onOpenChange={(open) => {
          if (!open) setDeleteOpen(false);
        }}
        title={copy.settings.deleteTitle}
        description={copy.settings.deleteConfirmBody}
        footer={
          <>
            <Button variant="quiet" onClick={() => setDeleteOpen(false)}>
              {copy.common.cancel}
            </Button>
            <Button
              variant="secondary"
              className="border-status-missed text-status-missed"
              onClick={() => void deleteEverything()}
              disabled={deleteWorkspace.isPending}
            >
              {deleteWorkspace.isPending ? copy.settings.deleting : copy.settings.deleteButton}
            </Button>
          </>
        }
      >
        {deleteProblem ? (
          <p role="alert" className="text-sm text-status-missed">
            {deleteProblem}
          </p>
        ) : null}
      </Dialog>
    </div>
  );
}
