# Frontend conventions

## Principles

- Plain language first. Every user-facing string lives in `src/copy.ts`.
- Read `backend/openapi.json` and the report schema before naming a field.
- Findings need a quote and a time. Never invent a benchmark or a target.
- Use semantic HTML and Radix primitives. Status always has an icon and a word.
- Treat transcript and quote text as text. Never inject HTML.
- No network in tests. No third-party requests at runtime.
- Keep the initial JavaScript under the `BUNDLE_BUDGET_KB` budget.

## Commands

`npm install`, `npm run dev`, `npm run check`, `npm run gen:api`.
`make frontend-check` runs the same check from the repository root.

## Layout

- `src/components/`: shared base components.
- `src/features/`: product screens, added stage by stage.
- `src/theme/`: design tokens and theme preference.
- `src/lib/`: small shared helpers.
- `scripts/`: API generation and build guards.
- `tests/`: Vitest, Testing Library, axe.

## Copy rules

Use the prompt mappings: checklist, moment to improve, what was said. Errors say
what happened and what to do. Technical terms belong only in `technicalCopy`.
Keep an action's name stable through its flow.

## Do not

- Do not edit `backend/` or `src/call_analyser/` from a frontend stage.
- Do not add a dependency without a one-line reason.
- Do not use `dangerouslySetInnerHTML`, `eval`, or inline event handlers in strings.
- Do not log report content, transcripts, or access keys.
- Do not put an access key in a URL or in `VITE_*`.
