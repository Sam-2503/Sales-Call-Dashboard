import { Link, Navigate } from "react-router-dom";

import { useAccessKey } from "@/api/useAccessKey";
import { Button } from "@/components";
import { copy } from "@/copy";

export function ProgressPage() {
  const accessKey = useAccessKey();
  if (!accessKey) return <Navigate to="/" replace />;

  return (
    <div className="max-w-[65ch]">
      <h1>{copy.progressPage.title}</h1>
      <p className="mt-3 text-muted">{copy.progressPage.intro}</p>
      <p className="mt-8">{copy.progressPage.empty}</p>
      <Button variant="secondary" asChild className="mt-5">
        <Link to="/calls">{copy.nav.calls}</Link>
      </Button>
    </div>
  );
}
