import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
};

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <section
      className={cn(
        "rounded-panel border border-dashed border-hairline bg-surface px-6 py-10 text-center",
        className,
      )}
    >
      <Inbox aria-hidden="true" className="mx-auto mb-3 text-muted" size={28} />
      <h2 className="text-[19px]">{title}</h2>
      {description ? <p className="mx-auto mt-2 text-muted">{description}</p> : null}
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </section>
  );
}
