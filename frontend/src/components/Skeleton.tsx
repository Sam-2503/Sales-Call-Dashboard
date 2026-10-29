import { copy } from "@/copy";
import { cn } from "@/lib/cn";

export type SkeletonProps = {
  className?: string;
  label?: string;
};

export function Skeleton({ className, label }: SkeletonProps) {
  const accessibleLabel = label ?? copy.components.skeletonLabel;
  return (
    <div
      role="status"
      aria-label={accessibleLabel}
      className={cn("animate-pulse rounded-control bg-wash motion-reduce:animate-none", className)}
    >
      <span className="sr-only">{accessibleLabel}</span>
    </div>
  );
}
