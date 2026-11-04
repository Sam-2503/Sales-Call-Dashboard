import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { useAccessKey } from "@/api/useAccessKey";
import { copy } from "@/copy";

import { WelcomePage } from "@/features/welcome/WelcomePage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { AppShell } from "@/shell/AppShell";
import { RouteErrorPage } from "@/shell/RouteErrorPage";

function HomeRoute() {
  const accessKey = useAccessKey();
  return accessKey ? <Navigate to="/calls" replace /> : <WelcomePage />;
}

const CallsPage = lazy(() => import("@/features/calls/CallsPage").then((module) => ({ default: module.CallsPage })));
const CallPlaceholderPage = lazy(() => import("@/features/calls/CallPlaceholderPage").then((module) => ({ default: module.CallPlaceholderPage })));
const ProgressPage = lazy(() => import("@/features/progress/ProgressPage").then((module) => ({ default: module.ProgressPage })));
const SettingsPage = lazy(() => import("@/features/settings/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const HowItWorksPage = lazy(() => import("@/features/how-it-works/HowItWorksPage").then((module) => ({ default: module.HowItWorksPage })));

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<div className="p-6" role="status">{copy.common.loading}</div>}>{children}</Suspense>;
}

export const routes = [
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <HomeRoute /> },
      { path: "calls", element: <LazyPage><CallsPage /></LazyPage> },
      { path: "calls/:callId", element: <LazyPage><CallPlaceholderPage /></LazyPage> },
      { path: "progress", element: <LazyPage><ProgressPage /></LazyPage> },
      { path: "settings", element: <LazyPage><SettingsPage /></LazyPage> },
      { path: "how-it-works", element: <LazyPage><HowItWorksPage /></LazyPage> },
      { path: "*", element: <LazyPage><NotFoundPage /></LazyPage> },
    ],
  },
];

export const router = createBrowserRouter(routes);
