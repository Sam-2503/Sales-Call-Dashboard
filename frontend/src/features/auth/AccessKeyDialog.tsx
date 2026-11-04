import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import { Button, Dialog } from "@/components";
import { copy } from "@/copy";

export type AccessKeyDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (value: string) => Promise<string | null> | string | null;
  trigger?: ReactNode;
};

export function AccessKeyDialog({ open, onOpenChange, onSubmit, trigger }: AccessKeyDialogProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setValue("");
    setError(null);
    setBusy(false);
  }, [open]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) {
      setError(copy.welcome.keyInvalid);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await onSubmit(trimmed);
      if (result) {
        setError(result);
        return;
      }
      onOpenChange(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      trigger={trigger}
      title={copy.welcome.keyTitle}
      description={copy.welcome.keyBody}
      footer={
        <>
          <Button variant="quiet" onClick={() => onOpenChange(false)} disabled={busy}>
            {copy.welcome.keyCancel}
          </Button>
          <Button type="submit" form="access-key-form" disabled={busy}>
            {busy ? copy.welcome.keyChecking : copy.welcome.keySubmit}
          </Button>
        </>
      }
    >
      <form id="access-key-form" onSubmit={(event) => void handleSubmit(event)}>
        <label htmlFor="access-key-input" className="text-sm font-bold">
          {copy.welcome.keyLabel}
        </label>
        <input
          id="access-key-input"
          type="password"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={copy.welcome.keyPlaceholder}
          autoComplete="off"
          spellCheck={false}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "access-key-error" : undefined}
          className="mt-2 min-h-11 w-full rounded-control border border-hairline bg-paper px-3 py-2 text-ink placeholder:text-muted focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus"
        />
        {error ? (
          <p id="access-key-error" role="alert" className="mt-2 text-sm text-status-missed">
            {error}
          </p>
        ) : null}
      </form>
    </Dialog>
  );
}
