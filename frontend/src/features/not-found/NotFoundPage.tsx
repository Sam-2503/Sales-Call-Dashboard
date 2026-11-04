import { Link } from "react-router-dom";

import { Button } from "@/components";
import { copy } from "@/copy";

export function NotFoundPage() {
  return (
    <div className="max-w-[65ch]">
      <h1>{copy.notFound.title}</h1>
      <p className="mt-3 text-muted">{copy.notFound.body}</p>
      <Button asChild className="mt-6">
        <Link to="/calls">{copy.notFound.action}</Link>
      </Button>
    </div>
  );
}
