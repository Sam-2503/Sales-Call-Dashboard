# Call Analyser

Evidence-backed GenAI analysis of uploaded sales-call recordings.

## Architecture

This repository contains the analysis core. A FastAPI backend owns uploads,
authentication, job state, and persistence. A React frontend consumes the
schema-valid `CallReport` returned by the analysis service.

The analysis core is exposed as a regular package for backend integration:

```python
from call_analyser.pipeline import AnalyseInput, analyse_call
```

The backend writes an uploaded recording to managed temporary storage, invokes
`analyse_call`, and serializes the returned report for the dashboard.

## Development

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and `ffmpeg`/`ffprobe`.

```bash
make install
make check
```

## Analysis flow

1. Validate and normalize the uploaded audio.
2. Transcribe it with the configured Gemini adapter.
3. Derive deterministic audio and conversation metrics.
4. Evaluate the transcript against the configured rubric.
5. Verify model evidence against exact transcript turns.
6. Retrieve optional playbook guidance from a pre-indexed playbook.
7. Score findings and return a schema-valid `CallReport`.

Playbook indexing is an administrative operation and is never performed during
per-call analysis. Query embeddings use a bounded LRU cache controlled by
`QUERY_EMBED_CACHE_SIZE`; document embeddings are never cached.

## Contracts

The public report contract is maintained in
[`schemas/call_report.schema.json`](schemas/call_report.schema.json).
All transcript and playbook content is treated as untrusted data, and imports
do not access networks, databases, indexes, or PDFs.
