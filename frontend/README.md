# Call review frontend

The React frontend for the Sales Call Analyser. It is built as a static bundle
and served by FastAPI at `/` from the same container as the API.

This checkout contains **Stages 0 and 1**:

- Stage 0: Vite/React/TypeScript scaffold, design tokens, base components,
  copy skeleton and build guards.
- Stage 1: typed API client, access-key storage, TanStack Query resource hooks,
  SSE job progress with polling fallback, generated-type drift checking, and
  MSW handlers for every endpoint in the frontend contract.

The `/` page is still the temporary design-system preview. Product screens,
routing, upload, playback and report views arrive in later stages.

## Requirements

- Node 20.19 or newer; the root Dockerfile uses `node:20-alpine`.
- npm (the lockfile is committed and the container runs `npm ci`).

## Run it

```bash
cd frontend
npm ci
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000`.

### Run without a backend

```bash
VITE_USE_MOCKS=true npm run dev
```

This starts MSW's browser worker before rendering. The mock keeps state in the
tab: calls can be uploaded, jobs move through stages, reports are served from
synthetic fixtures, and feedback is saved until reload. Restarting the server
resets the samples.

MSW uses `public/mockServiceWorker.js`. If you upgrade MSW, regenerate it with:

```bash
npx msw init public --save
```

### Configuration

`VITE_API_BASE` is optional. Leave it empty for this origin. If the API is on
another origin or path prefix, set it to the part **before** `/api/v1`
(for example `http://localhost:8000`). The generated paths already include
`/api/v1`, so the client does not append it twice.

`VITE_USE_MOCKS=true` enables the browser mock. `VITE_APP_NAME` changes the
neutral working name in one place. Never put a secret in a `VITE_*` variable.

## Checks

```bash
npm run check
```

This runs ESLint, strict TypeScript, Vitest with MSW, the production build, the
API type drift check, the initial bundle budget, the copy guard and the external
URL guard. From the repository root:

```bash
make frontend-check
```

Useful individual commands:

```bash
npm run gen:api       # regenerate src/api/schema.d.ts from backend/openapi.json
npm run check:api     # fail if the committed types drift
npm run sync:fixtures # refresh the mock copies of the shared report fixtures
npm run lint
npm run typecheck
npm test
npm run build
```

- Bundle budget: `BUNDLE_BUDGET_KB`, default 200 KB gzipped.
- Copy guard: scans string values in `src/copy.ts` and excludes the marked
  `technicalCopy` block.
- External guard: scans the built text files. Namespace strings and React's
  static error-decoder links are allowed; no asset, font, API or analytics URL
  from another origin is allowed.

## API layer

- [`src/api/client.ts`](src/api/client.ts) creates the typed `openapi-fetch`
  client, adds the bearer access key, resolves the API origin, and turns
  `{data,error,response}` into a value or an `ApiError`.
- [`src/api/errors.ts`](src/api/errors.ts) parses the error envelope, maps
  `Retry-After` seconds and HTTP dates, and handles `401` in one place: it
  clears the access key and routes to `/?restore=1` without putting the key in
  the URL.
- [`src/api/storage.ts`](src/api/storage.ts) wraps `localStorage` in
  try/catch, falls back to memory when storage is blocked, exposes
  `storageAvailable`, supports access-key import/export and detects when the app
  is embedded in a cross-site iframe.
- [`src/api/hooks/`](src/api/hooks/) contains `useMeta`, `useMe`, `useAgents`,
  `useCalls`, `useCall`, `useReport`, `useJob`, `useRubric`, `usePlaybook`,
  `useFeedback`, `useTrendsScores`, `useWeakSpots` and `useBenchmarks`.
  `useCalls` uses cursor-based infinite pages and refetches every three seconds
  only while a call is queued or processing. Reports are immutable in the cache;
  use `invalidateReport` and `invalidateCall` when a reanalysis job finishes.
  4xx errors are not retried.
- [`src/api/sse.ts`](src/api/sse.ts) uses `fetch-event-source` so the bearer
  header is sent. It handles `Last-Event-ID` replay, stops on `done` or `error`,
  maps package stage names to the five plain steps, keeps the previous step for
  unknown stages, and falls back to `GET /jobs/{id}` every two seconds after
  repeated stream failures.

## Mocks and fixtures

- [`src/mocks/handlers.ts`](src/mocks/handlers.ts) covers workspaces, `/me`,
  meta, rubric, playbook, reps, upload, calls, reports, deletion, reanalysis,
  audio URLs, jobs, SSE events, feedback and trends/benchmarks.
- The mock includes calls in every status, a complete report, an
  `insufficient_data` report, a queued call, a failed job, a demo workspace with
  no audio, and trends with `available: false`.
- [`sync-fixtures.mjs`](scripts/sync-fixtures.mjs) copies the shared synthetic
  report fixtures into `src/mocks/fixtures/`; a test fails if they drift.
- The fixtures are synthetic. See
  [`fixtures/reports/README.md`](../fixtures/reports/README.md).

## Design system

- Tokens: [`src/theme/tokens.css`](src/theme/tokens.css). Light is the default;
  dark is applied by `prefers-color-scheme` or `data-theme="dark"`.
- Base styles and Tailwind themes: [`src/theme/base.css`](src/theme/base.css).
- Font: Atkinson Hyperlegible, bundled with `@fontsource`; no font CDN.
- Components: [`src/components/`](src/components/), with keyboard and axe tests
  in [`tests/components.test.tsx`](tests/components.test.tsx).
- Copy: [`src/copy.ts`](src/copy.ts). Technical terms are allowed only in the
  `technicalCopy` block.

## Stage 0 screenshots

Captured from the Stage 0 production build with headless Chromium at 360, 768
and 1280 px, plus a dark-mode view at 1280 px:

- [Light, 360 px](screenshots/stage0/light-360.png)
- [Light, 768 px](screenshots/stage0/light-768.png)
- [Light, 1280 px](screenshots/stage0/light-1280.png)
- [Dark, 1280 px](screenshots/stage0/dark-1280.png)

## Limitations in this stage

- No routing, welcome/settings screens, upload form, call list, playback or
  report screens exist yet.
- The preview is temporary and will be replaced by the route shell in Stage 2.
- The accessibility tests use jsdom. Colour contrast is asserted separately from
  the token values; jsdom does not calculate rendered contrast.
- Playwright is not a project dependency. The Stage 0 screenshots were captured
  with a temporary headless Chromium.
- Docker is unavailable in this checkout, so the container build was reviewed
  but not executed.
