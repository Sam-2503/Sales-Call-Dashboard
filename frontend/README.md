# Call review frontend

The React frontend for the Sales Call Analyser. It is built as a static bundle
and served by FastAPI at `/` from the same container as the API.

This checkout contains **Stage 0 only**: the Vite/React/TypeScript scaffold, the
design tokens and base styles, the shared component set, the copy skeleton, the
API type generation, and the build guards. Product screens, API hooks, mocks and
audio playback arrive in later stages. The current `/` page is a design-system
preview, not a sales workflow.

## Requirements

- Node 20.19 or newer; the root Dockerfile uses `node:20-alpine`.
- npm (the lockfile is committed and the container runs `npm ci`).

## Run it

```bash
cd frontend
npm ci
npm run dev
```

The dev server is at the URL Vite prints (usually `http://localhost:5173`) and
proxies `/api` to `http://localhost:8000` for the real backend.

```bash
npm run build      # typecheck and write dist/
npm run preview    # serve the built bundle
```

`VITE_API_BASE`, `VITE_USE_MOCKS` and `VITE_APP_NAME` are documented in
[`.env.example`](.env.example). `VITE_USE_MOCKS` is reserved for Stage 1; no
mock worker is wired yet. Never put a secret in a `VITE_*` variable.

## Checks

```bash
npm run check
```

This runs ESLint, strict TypeScript, Vitest, the production build, the initial
bundle budget, the copy guard and the external-URL guard. From the repository
root:

```bash
make frontend-check
```

- Bundle budget: `BUNDLE_BUDGET_KB`, default 200 KB gzipped.
- Copy guard: scans string values in `src/copy.ts` and excludes the marked
  `technicalCopy` block. Add a banned word and it exits non-zero.
- External guard: scans the built text files. Namespace strings and React's
  static error-decoder links are allowed; no asset, font, API or analytics URL
  from another origin is allowed.

## Design system

- Tokens: [`src/theme/tokens.css`](src/theme/tokens.css). Light is the default;
  dark is applied by `prefers-color-scheme` or `data-theme="dark"`.
- Base styles and Tailwind themes: [`src/theme/base.css`](src/theme/base.css).
- Font: Atkinson Hyperlegible, bundled with `@fontsource`; no font CDN.
- Components: [`src/components/`](src/components/), with one keyboard and axe
  test each in [`tests/components.test.tsx`](tests/components.test.tsx).
- The conversation strip, route shell, API layer, report sections and progress
  chart are deliberately not built in Stage 0.

## Stage 0 screenshots

Captured from the production build with headless Chromium at 360, 768 and
1280 px, plus a dark-mode view at 1280 px:

- [Light, 360 px](screenshots/stage0/light-360.png)
- [Light, 768 px](screenshots/stage0/light-768.png)
- [Light, 1280 px](screenshots/stage0/light-1280.png)
- [Dark, 1280 px](screenshots/stage0/dark-1280.png)

## Copy and API types

All product strings are in [`src/copy.ts`](src/copy.ts), grouped by screen.
Technical terms are allowed only in `technicalCopy`. Error codes map to
sentences, including limits and `Retry-After` values passed in by the caller.

Regenerate the committed schema from the backend contract:

```bash
npm run gen:api
```

This writes `src/api/schema.d.ts` from `backend/openapi.json` and appends the
`CallReport` alias. The API client, error envelope handling, token storage and
streaming hook are Stage 1 work.

## Synthetic fixtures

`fixtures/reports/full_report.json` and
`fixtures/reports/insufficient_data_report.json` are synthetic, labelled
examples generated from `schemas/call_report.schema.json` because the expected
fixture files were absent. They contain invented people and quotes. See
[`fixtures/reports/README.md`](../fixtures/reports/README.md).

## Limitations in this stage

- No backend calls, authentication, upload, playback, review screens or
  progress page exist yet.
- Playwright is not a project dependency. The screenshots were captured with a temporary headless Chromium; no Playwright test is configured yet.
- The preview is intentionally temporary and will be replaced by the route
  shell in Stage 2.
- The accessibility tests use jsdom. Colour contrast is asserted separately from
  the token values; jsdom does not calculate rendered contrast.
- Docker is unavailable in this checkout, so the container build was reviewed but
  not executed.
