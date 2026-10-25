# Call Analyser

Evidence-backed GenAI analysis of sales calls against a rubric and indexed playbook.

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
network-free local indexing tests.

Stage 6c provides score-preserving retrieval and offline evaluation:

```bash
uv run call-analyser playbook query playbooks/<slug>/playbook.yaml "discovery questions"
uv run call-analyser playbook eval-retrieval playbooks/<slug>/playbook.yaml \
  --queries eval/retrieval_queries.yaml
```

Retrieval strips the stored embedding header, returns passage IDs and citation
metadata, and applies `PLAYBOOK_TOP_K`/`PLAYBOOK_MIN_SCORE` defaults. The
analysis path only embeds the query; it never adds or re-embeds documents.
