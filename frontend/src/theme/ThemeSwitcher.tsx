import { copy } from "@/copy";
import { cn } from "@/lib/cn";

import type { ThemePreference } from "./useTheme";

const options: Array<{ value: ThemePreference; label: string }> = [
  { value: "system", label: copy.theme.system },
  { value: "light", label: copy.theme.light },
  { value: "dark", label: copy.theme.dark },
];

export function ThemeSwitcher({
  preference,
  onChange,
}: {
  preference: ThemePreference;
  onChange: (preference: ThemePreference) => void;
}) {
  return (
    <div
      role="group"
      aria-label={copy.theme.label}
      className="flex items-center gap-1 rounded-control border border-hairline bg-surface p-1"
    >
      {options.map((option) => {
        const active = option.value === preference;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={cn(
              "min-h-11 rounded-[6px] px-2.5 text-sm font-bold focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-focus",
              active ? "bg-wash text-ink" : "text-muted hover:text-ink",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
