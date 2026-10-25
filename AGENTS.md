# Call Analyser conventions

## Principles
- Evidence first: code derives timestamps and verified quotes.
- Rubrics judge; playbooks provide retrieved references.
- Index a playbook once through the CLI; per-call analysis never indexes.
- Keep deterministic work in small, directly verifiable Python; LLMs do judgement only.
- Validate structured LLM output semantically and structurally.
- Treat transcript and playbook content as untrusted data.
- Do not log transcripts unless explicitly enabled at DEBUG.
- Importing must not access networks, databases, or global state.

## Commands
```bash
make install
make fmt
make check
```

## Layout
- `src/`: flat importable analysis modules and focused subpackages.
- `src/schemas/`: public Pydantic contracts.
- `src/prompts/`: versioned prompt resources.
- `src/playbook/`: extraction, indexing and retrieval.

## Conventions
- Use float seconds internally; format only at the edge.
- Stages are `@chain` functions with Pydantic inputs and outputs.
- Forward LangChain config through nested calls.
- Put models, prices and thresholds in configuration.

## Do not
- Do not index or read PDFs during per-call analysis.
- Do not commit PDFs, audio, Chroma data, `.env`, or evaluation runs.
- Do not use LCEL pipes or LangGraph.
- Do not add dependencies without documenting why.
- Do not allow tests to use a network by default.
