import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

import { copy } from "@/copy";
import { cn } from "@/lib/cn";

export type ErrorStateProps = {
  title?: string;
  description?: string;
  action?: ReactNode;
  requestId?: string;
  className?: string;
};

export function ErrorState({
  title = copy.components.errorTitle,
  description = copy.components.errorFallback,
  action,
  requestId,
  className,
}: ErrorStateProps) {
  return (
    <section
      role="alert"
      className={cn("rounded-panel border border-hairline bg-surface px-6 py-8", className)}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle aria-hidden="true" className="mt-1 shrink-0 text-status-missed" size={22} />
        <div>
          <h2 className="text-[19px]">{title}</h2>
          <p className="mt-2 text-muted">{description}</p>
          {requestId ? (
            <p className="mt-3 text-sm text-muted">
              {copy.components.supportReference}: <span className="tabular">{requestId}</span>
            </p>
          ) : null}
          {action ? <div className="mt-5">{action}</div> : null}
        </div>
      </div>
    </section>
  );
}
