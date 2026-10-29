import "@fontsource/atkinson-hyperlegible/latin-400.css";
import "@fontsource/atkinson-hyperlegible/latin-700.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { QueryProvider } from "./api/QueryProvider";
import { App } from "./App";
import { ToastProvider } from "./components";
import { copy } from "./copy";
import "./theme/base.css";

document.title = copy.appName;

async function enableMocks(): Promise<void> {
  if (import.meta.env.VITE_USE_MOCKS !== "true") return;
  const { worker } = await import("./mocks/browser");
  try {
    await worker.start({
      onUnhandledRequest: "bypass",
      serviceWorker: { url: "/mockServiceWorker.js" },
    });
  } catch {
    // The preview still renders; API calls will fail without the worker.
  }
}

async function bootstrap(): Promise<void> {
  await enableMocks();
  const rootElement = document.getElementById("root");
  if (!rootElement) throw new Error("Root element is missing");

  createRoot(rootElement).render(
    <StrictMode>
      <QueryProvider>
        <ToastProvider>
          <App />
        </ToastProvider>
      </QueryProvider>
    </StrictMode>,
  );
}

void bootstrap();
