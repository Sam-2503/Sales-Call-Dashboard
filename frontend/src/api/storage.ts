const ACCESS_KEY = "call-review.access-key";
const PREFERENCES_KEY = "call-review.preferences";
const PROBE_VALUE = "call-review-probe";

type Listener = () => void;

const listeners = new Set<Listener>();
const memory = {
  accessKey: null as string | null,
  preferences: {} as Record<string, string>,
};

function canUseStorage(): boolean {
  if (typeof window === "undefined") return false;
  try {
    localStorage.setItem(PROBE_VALUE, "1");
    localStorage.removeItem(PROBE_VALUE);
    return true;
  } catch {
    return false;
  }
}

export let storageAvailable = canUseStorage();

function markUnavailable() {
  storageAvailable = false;
}

function notify() {
  for (const listener of listeners) listener();
}

function readPreferences(): Record<string, string> {
  if (storageAvailable) {
    try {
      const raw = localStorage.getItem(PREFERENCES_KEY);
      if (raw) {
        const value: unknown = JSON.parse(raw);
        if (value && typeof value === "object" && !Array.isArray(value)) {
          return Object.fromEntries(
            Object.entries(value).filter(
              (entry): entry is [string, string] => typeof entry[1] === "string",
            ),
          );
        }
      }
    } catch {
      markUnavailable();
    }
  }
  return { ...memory.preferences };
}

export function getAccessKey(): string | null {
  if (storageAvailable) {
    try {
      const stored = localStorage.getItem(ACCESS_KEY);
      if (stored) return stored;
    } catch {
      markUnavailable();
    }
  }
  return memory.accessKey;
}

export function setAccessKey(value: string): void {
  const next = value.trim();
  memory.accessKey = next.length > 0 ? next : null;
  if (storageAvailable) {
    try {
      if (next.length > 0) localStorage.setItem(ACCESS_KEY, next);
      else localStorage.removeItem(ACCESS_KEY);
    } catch {
      markUnavailable();
    }
  }
  notify();
}

export function clearAccessKey(): void {
  memory.accessKey = null;
  if (storageAvailable) {
    try {
      localStorage.removeItem(ACCESS_KEY);
    } catch {
      markUnavailable();
    }
  }
  notify();
}

export function exportAccessKey(): string | null {
  return getAccessKey();
}

export function importAccessKey(value: string): boolean {
  const next = value.trim();
  if (next.length < 8 || /\s/.test(next)) return false;
  setAccessKey(next);
  return true;
}

export function getPreference(key: string): string | null {
  return readPreferences()[key] ?? null;
}

export function setPreference(key: string, value: string): void {
  const preferences = readPreferences();
  preferences[key] = value;
  if (storageAvailable) {
    try {
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
    } catch {
      markUnavailable();
    }
  }
  memory.preferences = preferences;
}

export function clearStoredData(): void {
  memory.preferences = {};
  clearAccessKey();
  if (storageAvailable) {
    try {
      localStorage.removeItem(PREFERENCES_KEY);
    } catch {
      markUnavailable();
    }
  }
}

export function subscribeAccessKey(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function isEmbedded(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.top !== window.self;
  } catch {
    return true;
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === ACCESS_KEY) notify();
  });
}
