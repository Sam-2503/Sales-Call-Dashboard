import { useSyncExternalStore } from "react";

import { getAccessKey, subscribeAccessKey } from "./storage";

export function useAccessKey(): string | null {
  return useSyncExternalStore(subscribeAccessKey, getAccessKey, () => null);
}
