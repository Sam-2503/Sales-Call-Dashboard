import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("access-key storage", () => {
  it("persists, exports, imports and clears the access key", async () => {
    const storage = await import("@/api/storage");
    expect(storage.storageAvailable).toBe(true);
    expect(storage.getAccessKey()).toBeNull();

    storage.setAccessKey("  access-key-123  ");
    expect(storage.getAccessKey()).toBe("access-key-123");
    expect(storage.exportAccessKey()).toBe("access-key-123");
    expect(localStorage.getItem("call-review.access-key")).toBe("access-key-123");

    storage.clearAccessKey();
    expect(storage.getAccessKey()).toBeNull();

    expect(storage.importAccessKey("access-key-987")).toBe(true);
    expect(storage.getAccessKey()).toBe("access-key-987");
    expect(storage.importAccessKey("short")).toBe(false);
    expect(storage.importAccessKey("has whitespace")).toBe(false);
  });

  it("notifies subscribers on change", async () => {
    const storage = await import("@/api/storage");
    const listener = vi.fn();
    const unsubscribe = storage.subscribeAccessKey(listener);
    storage.setAccessKey("access-key-123");
    expect(listener).toHaveBeenCalledTimes(1);
    storage.clearAccessKey();
    expect(listener).toHaveBeenCalledTimes(2);
    unsubscribe();
    storage.setAccessKey("access-key-456");
    expect(listener).toHaveBeenCalledTimes(2);
  });

  it("falls back to memory when browser storage is blocked", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });
    const storage = await import("@/api/storage");

    expect(storage.storageAvailable).toBe(false);
    expect(() => storage.setAccessKey("access-key-123")).not.toThrow();
    expect(storage.getAccessKey()).toBe("access-key-123");
    expect(() => storage.setPreference("lastRep", "me")).not.toThrow();
    expect(storage.getPreference("lastRep")).toBe("me");
    expect(() => storage.clearStoredData()).not.toThrow();
    expect(storage.getAccessKey()).toBeNull();
  });

  it("stores small preferences and clears them with the other data", async () => {
    const storage = await import("@/api/storage");
    storage.setPreference("theme", "dark");
    storage.setPreference("lastRep", "alex");
    expect(storage.getPreference("theme")).toBe("dark");
    expect(storage.getPreference("lastRep")).toBe("alex");
    storage.clearStoredData();
    expect(storage.getPreference("theme")).toBeNull();
    expect(storage.getAccessKey()).toBeNull();
  });

  it("exposes whether the app is embedded", async () => {
    const storage = await import("@/api/storage");
    expect(storage.isEmbedded()).toBe(false);

    const top = vi.spyOn(window, "top", "get").mockReturnValue({} as Window);
    expect(storage.isEmbedded()).toBe(true);
    top.mockRestore();
  });
});
