import { Check, Copy, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { copy } from "@/copy";
import { cn } from "@/lib/cn";

import { Button, type ButtonProps } from "./Button";

type CopyState = "idle" | "copied" | "failed";

export type CopyButtonProps = {
  value: string;
  label?: string;
  variant?: ButtonProps["variant"];
  className?: string;
  onCopied?: () => void;
};

function fallbackCopy(value: string): boolean {
  const area = document.createElement("textarea");
  area.value = value;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.top = "0";
  area.style.left = "-9999px";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  try {
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    document.body.removeChild(area);
  }
}

async function copyText(value: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
    return fallbackCopy(value);
  } catch {
    return fallbackCopy(value);
  }
}

export function CopyButton({
  value,
  label,
  variant = "secondary",
  className,
  onCopied,
}: CopyButtonProps) {
  const [state, setState] = useState<CopyState>("idle");
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (resetTimer.current) clearTimeout(resetTimer.current);
    };
  }, []);

  async function handleCopy() {
    const copied = await copyText(value);

    setState(copied ? "copied" : "failed");
    if (copied) onCopied?.();
    if (resetTimer.current) clearTimeout(resetTimer.current);
    resetTimer.current = setTimeout(() => setState("idle"), 4000);
  }

  const visibleLabel =
    state === "copied"
      ? copy.common.copied
      : state === "failed"
        ? copy.common.copyFailed
        : (label ?? copy.common.copy);

  return (
    <>
      <Button
        variant={variant}
        className={cn(state === "failed" && "text-status-missed", className)}
        onClick={() => void handleCopy()}
      >
        {state === "copied" ? (
          <Check aria-hidden="true" size={18} />
        ) : state === "failed" ? (
          <X aria-hidden="true" size={18} />
        ) : (
          <Copy aria-hidden="true" size={18} />
        )}
        {visibleLabel}
      </Button>
      <span role="status" aria-live="polite" className="sr-only">
        {state === "copied" ? copy.common.copied : state === "failed" ? copy.common.copyFailed : ""}
      </span>
    </>
  );
}
