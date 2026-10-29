import { useEffect, useState } from "react";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "call-review.theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

function isPreference(value: string | null): value is ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return isPreference(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

function systemIsDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.(DARK_QUERY).matches === true;
}

function applyPreference(preference: ThemePreference) {
  const root = document.documentElement;
  if (preference === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", preference);
  }

  const dark = preference === "dark" || (preference === "system" && systemIsDark());
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", dark ? "#1A1A19" : "#FCFCFB");
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(readPreference);

  useEffect(() => {
    applyPreference(preference);
    try {
      localStorage.setItem(STORAGE_KEY, preference);
    } catch {
      // The theme still applies for this visit when storage is blocked.
    }
  }, [preference]);

  useEffect(() => {
    if (preference !== "system") return;
    const media = window.matchMedia?.(DARK_QUERY);
    if (!media) return;
    const onChange = () => applyPreference("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [preference]);

  return { preference, setPreference };
}
