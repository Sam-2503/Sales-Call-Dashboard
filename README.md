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
