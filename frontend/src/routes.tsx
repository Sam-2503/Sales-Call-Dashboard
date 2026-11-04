import { createBrowserRouter, Navigate } from "react-router-dom";

import { useAccessKey } from "@/api/useAccessKey";

import { CallPlaceholderPage } from "@/features/calls/CallPlaceholderPage";
import { CallsPage } from "@/features/calls/CallsPage";
import { HowItWorksPage } from "@/features/how-it-works/HowItWorksPage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { ProgressPage } from "@/features/progress/ProgressPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { WelcomePage } from "@/features/welcome/WelcomePage";
import { AppShell } from "@/shell/AppShell";
import { RouteErrorPage } from "@/shell/RouteErrorPage";

function HomeRoute() {
  const accessKey = useAccessKey();
  return accessKey ? <Navigate to="/calls" replace /> : <WelcomePage />;
}

export const routes = [
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <HomeRoute /> },
      { path: "calls", element: <CallsPage /> },
      { path: "calls/:callId", element: <CallPlaceholderPage /> },
      { path: "progress", element: <ProgressPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "how-it-works", element: <HowItWorksPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
