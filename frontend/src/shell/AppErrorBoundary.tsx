import { Component, type ReactNode } from "react";

import { Button, ErrorState } from "@/components";
import { copy } from "@/copy";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="min-h-dvh bg-paper px-4 py-10 text-ink">
        <main className="mx-auto max-w-[760px]">
          <h1>{copy.shell.errorTitle}</h1>
          <div className="mt-6">
            <ErrorState
              title={copy.shell.errorTitle}
              description={copy.shell.errorBody}
              action={<Button onClick={() => window.location.reload()}>{copy.shell.reload}</Button>}
            />
          </div>
        </main>
      </div>
    );
  }
}
