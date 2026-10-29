import "@fontsource/atkinson-hyperlegible/latin-400.css";
import "@fontsource/atkinson-hyperlegible/latin-700.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { ToastProvider } from "./components";
import { copy } from "./copy";
import "./theme/base.css";

document.title = copy.appName;

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Root element is missing");

createRoot(rootElement).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>,
);
