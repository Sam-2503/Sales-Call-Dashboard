import { copy } from "@/copy";
import { cn } from "@/lib/cn";

export type ScoreRingProps = {
  score: number | null | undefined;
  label?: string;
  size?: number;
  className?: string;
};

export function ScoreRing({
  score,
  label = copy.components.scoreLabel,
  size = 112,
  className,
}: ScoreRingProps) {
  if (score === null || score === undefined || !Number.isFinite(score)) {
    return (
      <div className={cn("inline-flex flex-col items-start gap-1", className)}>
        <span className="text-sm font-bold text-muted">{label}</span>
        <span className="text-lg text-muted">{copy.components.scoreUnavailable}</span>
      </div>
    );
  }

  const value = Math.max(0, Math.min(100, Math.round(score)));
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div
      role="img"
      aria-label={`${label}: ${value} out of 100`}
      className={cn("inline-flex flex-col items-center gap-1", className)}
    >
      <span className="relative inline-flex" style={{ width: size, height: size }}>
        <svg aria-hidden="true" viewBox="0 0 112 112" className="h-full w-full -rotate-90">
          <circle cx="56" cy="56" r={radius} fill="none" stroke="var(--hairline)" strokeWidth="4" />
          <circle
            cx="56"
            cy="56"
            r={radius}
            fill="none"
            stroke="var(--ink)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="tabular absolute inset-0 grid place-items-center text-[32px] font-bold leading-none">
          {value}
        </span>
      </span>
      <span className="text-sm font-bold text-muted">{label}</span>
    </div>
  );
}
