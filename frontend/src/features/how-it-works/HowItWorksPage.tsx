import { Link } from "react-router-dom";

import { useMeta, usePlaybook, useRubric } from "@/api/hooks";
import { Button, Disclosure, ErrorState, Skeleton } from "@/components";
import { copy, technicalCopy } from "@/copy";

export function HowItWorksPage() {
  const meta = useMeta();
  const playbook = usePlaybook();
  const rubric = useRubric();

  if (meta.isLoading) {
    return (
      <div className="space-y-3">
        <h1>{copy.howItWorks.title}</h1>
        <Skeleton className="h-5 w-3/4" label={copy.common.loading} />
        <Skeleton className="h-5 w-2/3" label={copy.common.loading} />
        <Skeleton className="h-5 w-1/2" label={copy.common.loading} />
      </div>
    );
  }

  if (meta.isError || !meta.data) {
    return (
      <div>
        <h1>{copy.howItWorks.title}</h1>
        <div className="mt-6">
          <ErrorState
            title={copy.howItWorks.errorTitle}
            description={copy.howItWorks.errorBody}
            action={<Button onClick={() => void meta.refetch()}>{copy.common.retry}</Button>}
          />
        </div>
      </div>
    );
  }

  const book = playbook.data?.available ? playbook.data : null;

  return (
    <div className="max-w-[65ch]">
      <h1>{copy.howItWorks.title}</h1>
      <p className="mt-3 text-muted">{copy.howItWorks.intro}</p>

      <section className="mt-10 border-t border-hairline pt-8">
        <h2>{copy.howItWorks.looksHeading}</h2>
        <p className="mt-3">{copy.howItWorks.looksBody}</p>
        {rubric.data ? (
          <div className="mt-4">
            <h3 className="text-base">{copy.howItWorks.categoriesLabel}</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
              {rubric.data.categories.map((category) => (
                <li key={category.id}>{category.name}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section className="mt-8 border-t border-hairline pt-8">
        <h2>{copy.howItWorks.quotesHeading}</h2>
        <p className="mt-3">{copy.howItWorks.quotesBody}</p>
      </section>

      <section className="mt-8 border-t border-hairline pt-8">
        <h2>{copy.howItWorks.adviceHeading}</h2>
        <p className="mt-3">{copy.howItWorks.adviceBody}</p>
        {book?.title ? (
          <p className="mt-2">
            {copy.labels.fromBook} <em>{book.title}</em>.
          </p>
        ) : (
          <p className="mt-2 text-muted">{copy.howItWorks.adviceNoBook}</p>
        )}
      </section>

      <p className="mt-8 border-t border-hairline pt-5 text-sm text-muted">
        {copy.feedback.honesty}
      </p>

      <div className="mt-8 border-t border-hairline pt-5">
        <Disclosure summary={technicalCopy.heading}>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
            <dt className="text-muted">{technicalCopy.pipelineVersion}</dt>
            <dd className="tabular">{meta.data.pipeline_version}</dd>
            <dt className="text-muted">{technicalCopy.checklistVersion}</dt>
            <dd>
              {meta.data.rubric.id}, {meta.data.rubric.version}
            </dd>
            <dt className="text-muted">{technicalCopy.analysisModel}</dt>
            <dd>{meta.data.models.analysis}</dd>
            <dt className="text-muted">{technicalCopy.fastModel}</dt>
            <dd>{meta.data.models.fast}</dd>
            <dt className="text-muted">{technicalCopy.transcriptionModel}</dt>
            <dd>{meta.data.models.transcribe}</dd>
            <dt className="text-muted">{technicalCopy.embeddingModel}</dt>
            <dd>{meta.data.models.embedding}</dd>
            <dt className="text-muted">{technicalCopy.bookTitle}</dt>
            <dd>{book?.title ?? technicalCopy.notAvailable}</dd>
          </dl>
        </Disclosure>
      </div>

      <p className="mt-8 text-sm">
        <Link to="/" className="font-bold">
          {copy.appName}
        </Link>
      </p>
    </div>
  );
}
