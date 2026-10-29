import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { clearStoredData } from "@/api/storage";
import { resetMockState } from "@/mocks/data";
import { server } from "@/mocks/server";

server.listen({ onUnhandledRequest: "error" });
window.fetch = globalThis.fetch;

afterEach(() => {
  cleanup();
  localStorage.clear();
  clearStoredData();
  document.documentElement.removeAttribute("data-theme");
  server.resetHandlers();
  resetMockState();
});

beforeAll(() => {
  if (!globalThis.ReadableStream) {
    // Node 18+ provides this; jsdom does not always expose it.
    globalThis.ReadableStream = ReadableStream;
  }
});

afterAll(() => {
  server.close();
});

if (!window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

if (!window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn();
}

if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
}

if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = vi.fn();
}

if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = vi.fn();
}
