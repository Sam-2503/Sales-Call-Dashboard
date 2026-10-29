import { Info } from "lucide-react";

import { copy } from "@/copy";
import { cn } from "@/lib/cn";

import { Tooltip } from "./Tooltip";

export type InfoTipProps = {
  label: string;
  className?: string;
};

export function InfoTip({ label, className }: InfoTipProps) {
  return (
    <Tooltip label={label}>
      <button
        type="button"
        aria-label={copy.components.infoLabel}
        className={cn(
          "inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-control text-muted",
          "hover:bg-wash hover:text-ink focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus",
          className,
        )}
      >
        <Info aria-hidden="true" size={18} />
      </button>
    </Tooltip>
  );
}
