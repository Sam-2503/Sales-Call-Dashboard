import { Link, useRouteError } from "react-router-dom";

import { Button, ErrorState } from "@/components";
import { copy } from "@/copy";

export function RouteErrorPage() {
  const error = useRouteError();
  void error;

  return (
    <div className="min-h-dvh bg-paper px-4 py-10 text-ink">
      <main className="mx-auto max-w-[760px]">
        <h1>{copy.routeError.title}</h1>
        <div className="mt-6">
          <ErrorState
            title={copy.routeError.title}
            description={copy.routeError.body}
            action={
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => window.location.reload()}>{copy.routeError.reload}</Button>
                <Button variant="quiet" asChild>
                  <Link to="/calls">{copy.notFound.action}</Link>
                </Button>
              </div>
            }
          />
        </div>
      </main>
    </div>
  );
}
