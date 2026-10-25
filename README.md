# Call Analyser

Evidence-backed GenAI analysis of sales calls against a rubric and indexed playbook.

## Application architecture

The analysis core lives directly under `src/` so a FastAPI backend can import
the service boundary without an extra package layer:

```python
from pipeline import AnalyseInput, analyse_call
```

Uploaded recordings should be written to managed temporary storage by the API,
then passed to `analyse_call`. The returned `CallReport` is already a
schema-valid object suitable for a dashboard response or persistence layer.
The React frontend is intentionally outside this repository's analysis core.

## Development

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and `ffmpeg`/`ffprobe`.

```bash
cp .env.example .env
make install
make check
```

Stage 0 provides scaffolding, configuration and developer tooling. Imports have no side effects.

## Deterministic metrics

Stage 4 metrics operate on transcript timings and are therefore approximate when
`timing_resolution` is `segment_interpolated`; callers should not display
sub-second precision. They include talk-to-listen shares, words per minute,
configured filler counts, longest monologue, indicative customer-to-agent response
delays, and optional energy-based dead-air flags from a normalized audio file.
Interruptions are intentionally unavailable in v1 because sequential transcript
segments cannot establish overlapping speech honestly.

## Playbook inspection

Stage 6a supports network-free inspection of a playbook specification and PDF:

```bash
uv run call-analyser playbook inspect playbooks/<slug>/playbook.yaml
uv run call-analyser playbook inspect playbooks/<slug>/playbook.yaml --json
```

Extraction is deterministic, removes repeated headers and page numbers, detects
chapters, applies configured page offsets, and creates stable chapter-local
chunks. Indexing and embeddings are intentionally not performed by `inspect`.

Stage 6b adds explicit offline indexing:

```bash
uv run call-analyser playbook index playbooks/<slug>/playbook.yaml
uv run call-analyser playbook status playbooks/<slug>/playbook.yaml
```

The index writes a manifest beside the configured Chroma directory, resumes
interrupted batches by deterministic chunk ID, and refuses changed source PDFs
or settings unless `--rebuild --yes` is supplied. Set `FAKE_MODE=true` for
network-free local indexing tests. Set `QUERY_EMBED_CACHE_SIZE=0` to disable
the bounded LRU cache for repeated retrieval queries; document embeddings are
never cached.

Stage 6c provides score-preserving retrieval and offline evaluation:

```bash
uv run call-analyser playbook query playbooks/<slug>/playbook.yaml "discovery questions"
uv run call-analyser playbook eval-retrieval playbooks/<slug>/playbook.yaml \
  --queries eval/retrieval_queries.yaml
```

Retrieval strips the stored embedding header, returns passage IDs and citation
metadata, and applies `PLAYBOOK_TOP_K`/`PLAYBOOK_MIN_SCORE` defaults. The
analysis path only embeds the query; it never adds or re-embeds documents.

## Stage 10 end-to-end analysis

The assembled pipeline supports offline fake mode:

```bash
uv run call-analyser analyse recording.wav \
  --rubric rubrics/sales_v1.yaml \
  --fake \
  --no-grounding
```

Normal analysis requires a pre-indexed playbook when grounding is enabled.
The pipeline validates the rubric and index before ingesting audio, returns an
`insufficient_data` report for calls below configured thresholds, and emits
schema-valid JSON. `stream_analysis` exposes progress events for application
integrations.

## Stage 7 analysis stages

The Stage 7 chains `rubric_results`, `missed_moments`, and `customer_signals`
send the full rubric and timestamped transcript to structured-output models.
Their outputs contain only model-supplied turn IDs and quotes; timestamps and
public evidence objects are intentionally created by the deterministic
verification stage that follows. Transcript content is delimited as untrusted
data, and model references to unknown turn or rubric IDs are rejected.

## Evidence verification

Stage 8 treats every model quote as untrusted. The verifier normalizes and
fuzzy-matches it against the cited turn, searches configured neighboring turns
when necessary, checks the claimed speaker role, and replaces the model quote
and timestamps with exact transcript-derived values. Failed matches may be
repaired at most twice; unsupported findings are dropped and counted rather
than shown. Confidence buckets are deterministic and depend on repair attempt,
match score, and model confidence.

## Stage 9 grounding and scoring

Verified missed moments are ranked deterministically by severity, rubric weight,
and confidence before the configured cap is applied. Grounding retrieves
passages using the finding context, then allowlists model citations against the
actual retrieved passage IDs. Invalid citations are discarded, excerpts are
capped, and grounding can be disabled with `PLAYBOOK_GROUNDING=off` without
performing retrieval. Rubric scoring excludes `not_applicable` items and
reports critical missed items separately.

## Stage 11 offline evaluation

Saved reports can be evaluated without model or network calls. Define cases as
a YAML list with a report path and optional expected rubric statuses, missed
rubric item IDs, and overall score:

```bash
uv run call-analyser evaluate --cases eval/report_cases.yaml
```

The harness reports rubric status accuracy, missed-moment recall, evidence
validity, and mean absolute score error. Evaluation inputs and report fixtures
are intentionally kept separate from production analysis.

## Public contract and import safety

The report contract is maintained in `schemas/call_report.schema.json` and can
be regenerated with:

```bash
uv run call-analyser export-schema
```

Imports are side-effect free: no network calls, database access, indexing, or
PDF reads occur until the relevant command or function is invoked.
