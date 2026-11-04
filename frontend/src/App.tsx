import { RouterProvider } from "react-router-dom";

import { router } from "./routes";
import { AppErrorBoundary } from "./shell/AppErrorBoundary";

export function App() {
  return (
    <AppErrorBoundary>
      <RouterProvider router={router} />
    </AppErrorBoundary>
  );
}
