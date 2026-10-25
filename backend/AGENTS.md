# Backend guidance

- Keep HTTP, persistence, authentication, storage, and jobs here.
- Keep analysis behavior in the `call_analyser` package.
- Scope every future database query to its workspace.
- Never log request bodies, tokens, query strings, transcripts, or audio-derived text.
- Do not make network or database connections while importing modules.
- Run `make check` from this directory before committing backend changes.
