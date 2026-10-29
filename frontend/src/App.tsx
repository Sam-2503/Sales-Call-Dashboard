import { Check, MinusCircle, X } from "lucide-react";
import { useState, type ComponentType } from "react";

import {
  Button,
  CopyButton,
  Dialog,
  Disclosure,
  EmptyState,
  ErrorState,
  InfoTip,
  Popover,
  PopoverContent,
  PopoverTrigger,
  ScoreRing,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  useToast,
} from "@/components";
import { copy, technicalCopy } from "@/copy";
import { ThemeSwitcher } from "@/theme/ThemeSwitcher";
import { useTheme } from "@/theme/useTheme";

type StatusIconProps = { size?: number; className?: string };

function PartlyDoneIcon({ size = 18, className }: StatusIconProps) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M12 3a9 9 0 0 1 0 18Z" fill="currentColor" />
    </svg>
  );
}

const statusStyles = {
  done: { icon: Check, label: copy.status.done, className: "text-status-done" },
  partly: { icon: PartlyDoneIcon, label: copy.status.partly, className: "text-status-partly" },
  missed: { icon: X, label: copy.status.missed, className: "text-status-missed" },
  notApplicable: {
    icon: MinusCircle,
    label: copy.status.notApplicable,
    className: "text-muted",
  },
} satisfies Record<
  string,
  { icon: ComponentType<StatusIconProps>; label: string; className: string }
>;

function StatusLine({ tone }: { tone: keyof typeof statusStyles }) {
  const status = statusStyles[tone];
  const Icon = status.icon;
  return (
    <li className="flex items-center gap-2">
      <Icon size={18} className={status.className} />
      <span className={status.className}>{status.label}</span>
    </li>
  );
}

function ToastExample() {
  const { showToast } = useToast();
  return (
    <Button
      variant="secondary"
      onClick={() =>
        showToast({
          title: copy.preview.toastTitle,
          description: copy.preview.toastBody,
          tone: "success",
        })
      }
    >
      {copy.preview.toastAction}
    </Button>
  );
}

export function App() {
  const { preference, setPreference } = useTheme();
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <div className="min-h-dvh bg-paper text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-control focus:border focus:border-hairline focus:bg-surface focus:px-4 focus:py-3 focus:font-bold"
      >
        {copy.common.skipToContent}
      </a>

      <header className="border-b border-hairline">
        <div className="mx-auto flex min-h-16 max-w-[760px] flex-wrap items-center justify-between gap-3 px-4 py-2">
          <span className="text-[19px] font-bold tracking-tight">{copy.appName}</span>
          <ThemeSwitcher preference={preference} onChange={setPreference} />
        </div>
      </header>

      <main id="main" className="mx-auto max-w-[760px] px-4 pb-16 pt-10">
        <header className="max-w-[65ch]">
          <h1>{copy.preview.title}</h1>
          <p className="mt-4 text-muted">{copy.preview.intro}</p>
        </header>

        <section aria-labelledby="actions-heading" className="mt-10 border-t border-hairline pt-8">
          <h2 id="actions-heading">{copy.preview.sectionActions}</h2>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button>{copy.preview.primaryAction}</Button>
            <Button variant="secondary">{copy.preview.secondaryAction}</Button>
            <Button variant="quiet">{copy.preview.quietAction}</Button>
            <CopyButton value={copy.preview.copyText} />
            <ToastExample />
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Dialog
              open={deleteOpen}
              onOpenChange={setDeleteOpen}
              trigger={<Button variant="secondary">{copy.preview.dialogOpen}</Button>}
              title={copy.preview.dialogTitle}
              description={copy.preview.dialogBody}
              footer={
                <>
                  <Button variant="quiet" onClick={() => setDeleteOpen(false)}>
                    {copy.common.cancel}
                  </Button>
                  <Button onClick={() => setDeleteOpen(false)}>{copy.preview.dialogConfirm}</Button>
                </>
              }
            >
              <p>{copy.preview.dialogBody}</p>
            </Dialog>

            <Popover>
              <PopoverTrigger asChild>
                <Button variant="secondary">{copy.preview.popoverOpen}</Button>
              </PopoverTrigger>
              <PopoverContent label={copy.preview.popoverLabel}>
                <p className="text-sm">{copy.preview.popoverBody}</p>
              </PopoverContent>
            </Popover>

            <InfoTip label={copy.preview.exampleBody} />
          </div>
        </section>

        <section aria-labelledby="status-heading" className="mt-10 border-t border-hairline pt-8">
          <h2 id="status-heading">{copy.preview.sectionStatus}</h2>
          <div className="mt-5 flex flex-wrap items-start gap-8">
            <ScoreRing score={68} />
            <div>
              <h3>{copy.labels.checklist}</h3>
              <ul className="mt-2 space-y-2">
                <StatusLine tone="done" />
                <StatusLine tone="partly" />
                <StatusLine tone="missed" />
                <StatusLine tone="notApplicable" />
              </ul>
            </div>
            <div className="max-w-[32ch]">
              <h3>{copy.outcome.advanced}</h3>
              <p className="mt-2 text-sm text-muted">{copy.preview.exampleBody}</p>
            </div>
          </div>
        </section>

        <section aria-labelledby="tabs-heading" className="mt-10 border-t border-hairline pt-8">
          <h2 id="tabs-heading">{copy.preview.sectionSurfaces}</h2>
          <Tabs defaultValue="summary" className="mt-4">
            <TabsList aria-label={copy.preview.tabsLabel}>
              <TabsTrigger value="summary">{copy.preview.tabSummary}</TabsTrigger>
              <TabsTrigger value="moments">{copy.preview.tabMoments}</TabsTrigger>
              <TabsTrigger value="details">{copy.preview.tabDetails}</TabsTrigger>
              <TabsTrigger value="transcript">{copy.preview.tabTranscript}</TabsTrigger>
            </TabsList>
            <TabsContent value="summary">
              <h3>{copy.preview.exampleHeading}</h3>
              <p className="mt-2">{copy.preview.exampleBody}</p>
            </TabsContent>
            <TabsContent value="moments">
              <p>{copy.preview.exampleMoment}</p>
            </TabsContent>
            <TabsContent value="details">
              <p>{copy.preview.exampleBody}</p>
            </TabsContent>
            <TabsContent value="transcript">
              <p>{copy.preview.exampleQuote}</p>
            </TabsContent>
          </Tabs>
        </section>

        <section aria-labelledby="text-heading" className="mt-10 border-t border-hairline pt-8">
          <h2 id="text-heading">{copy.preview.sectionText}</h2>
          <div className="mt-5 space-y-4">
            <div className="speaker-mark-rep border-l-4 pl-3">
              <p className="text-sm font-bold">{copy.labels.you}</p>
              <p className="mt-1">
                <mark className="highlighter">{copy.preview.exampleQuote}</mark>
              </p>
            </div>
            <div className="speaker-mark-customer border-l-4 pl-3">
              <p className="text-sm font-bold">{copy.labels.customer}</p>
              <p className="mt-1 text-muted">{copy.preview.exampleBody}</p>
            </div>
          </div>
        </section>

        <section aria-labelledby="states-heading" className="mt-10 border-t border-hairline pt-8">
          <h2 id="states-heading">{copy.preview.sectionStates}</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <EmptyState title={copy.preview.emptyTitle} description={copy.preview.emptyBody} />
            <ErrorState
              title={copy.preview.errorTitle}
              description={copy.preview.errorBody}
              requestId={copy.preview.sampleRequestId}
            />
          </div>
          <div className="mt-5 space-y-2">
            <Skeleton className="h-6 w-2/3" label={copy.preview.skeletonLabel} />
            <Skeleton className="h-6 w-full" label={copy.preview.skeletonLabel} />
            <Skeleton className="h-6 w-4/5" label={copy.preview.skeletonLabel} />
          </div>
        </section>

        <section className="mt-10 border-t border-hairline pt-8">
          <Disclosure summary={technicalCopy.heading}>
            <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
              <dt className="text-muted">{technicalCopy.pipelineVersion}</dt>
              <dd className="tabular">{technicalCopy.examplePipelineVersion}</dd>
              <dt className="text-muted">{technicalCopy.checklistVersion}</dt>
              <dd className="tabular">{technicalCopy.exampleChecklistVersion}</dd>
              <dt className="text-muted">{technicalCopy.bookVersion}</dt>
              <dd>{technicalCopy.exampleBookVersion}</dd>
            </dl>
          </Disclosure>
        </section>
      </main>

      <footer className="border-t border-hairline">
        <div className="mx-auto max-w-[760px] px-4 py-6">
          <p className="max-w-[65ch] text-sm text-muted">{copy.feedback.honesty}</p>
        </div>
      </footer>
    </div>
  );
}
