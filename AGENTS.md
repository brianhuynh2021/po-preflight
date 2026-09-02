# AGENTS.md

Scope: the customer-facing frontend prototype in `apps/web` and backend integration contracts.

## Frontend Stack (non-obvious bits)

- **Next.js 16 on Vite via `vinext`** (not the classic Next dev server), bundled with the Cloudflare Vite plugin for Workers deployment. All `npm run dev/build/start` go through `vinext` with `WRANGLER_LOG_PATH` set.
- React 19 + React Server Components + App Router.
- Separate Route Groups: `app/(marketing)` for public marketing pages (`/`, `/pricing`, `/security`) and `app/(protected)` for operational app screens (`/overview`, `/orders`, `/catalog`, `/rules`, `/settings`, `/audit-log`, `/erp-sync`, `/agent-graph`, `/rag-playground`, `/audit-certificate`, `/staging`).
- Session-based authentication with `pf_session` cookie and `/login` gateway.
- Tailwind CSS 4 via PostCSS is installed, but the app uses **extensive custom CSS** in `app/globals.css` with CSS custom properties (theme tokens + status colors). Check globals.css before assuming Tailwind utilities.
- TypeScript strict, path alias `@/*` → `./*` (from `apps/web`).
- Node >= 22.13.

## Commands (from `apps/web`)

```bash
npm install
npm run dev        # vite dev server (uses vinext + wrangler)
npm run build      # vinext build
npm run start      # vinext start
npm run test       # builds first, then node --test tests/rendered-html.test.mjs
npm run lint       # ESLint 9 flat config (eslint.config.mjs)
```

- Tests use Node's built-in `node:test` + `node:assert` (no vitest/jest). The single spec imports the built worker from `dist/server/index.js`, so **`npm test` must build before running** (it does).
- Root `./scripts/test.sh` executes Python tests, secret scanning, AND full frontend verification (`tsc`, `lint`, `test`).

## Architecture & data

- `app/lib/types.ts` is the **domain source of truth** and mirrors the backend (`src/preflight/rules.py`, `models.py`) + `docs/FE_DATA_CONTRACT.md`. Keep it in step with the backend and the contract.
- `app/lib/derive.ts` holds derived/business logic (status derivation, decision rules, formatting) and each function documents which backend rule/contract section it mirrors. Keep the mirror correct:
  - Status is **derived** from findings (`deriveStatus`) — the three decided statuses are set by humans, never assigned by hand.
  - A **Blocked order can never be approved** and approving over warnings requires an exception note (min 10 chars) — logic is in `derive.ts`.
- Monetary values use `number` (not Decimal) on the frontend; use `Intl.NumberFormat` via the `money()` helper rather than manual formatting.

## Conventions

- UI is Vietnamese-language (labels, findings titles, decision notes in `derive.ts`/`types.ts`). This is intentional and NOT flagged by the repo's non-ASCII check (which only scans Python `src/`, `scripts/`, `tests/`).
- Status vocabulary (keep exact strings): `Ready`, `Review required`, `Blocked`, `Approved`, `Changes requested`, `Rejected`.
- Semantic colors are defined once in `app/lib/types.ts` (`STATUS_TONE`) — green=Ready/Approved, amber=Review, red=Blocked/Rejected. Reuse these; color never carries meaning alone (always pair with a label).
- Mirror backend behavior instead of re-deriving rules independently; flag any divergence to the FE data contract.
- The HTML-rendering test asserts on specific strings (e.g. PO ID `PO-10428`, customer `Northstar Retail`, `Review required`, action labels). Renaming seed data or UI copy can break `npm test` — run it after such changes.

## Git

- Main integration branch: `dev`; feature branches `feat/<name>`, fixes `fix/<name>`. Conventional commits (`feat:`, `fix:`, `docs:`, ...).

## Agent Development Policy

Superpowers is installed and available.

Use Superpowers skills when they provide meaningful value, but use engineering judgment
about process overhead.

For simple, low-risk changes such as:

- CSS/Tailwind changes
- simple JSX changes
- visual/layout changes
- renaming
- mechanical refactoring
- obvious configuration changes

do not invoke TDD.

For normal features:

- implement the feature
- run relevant tests
- fix failures
- verify the result

Use test-driven-development for:

- complex business logic
- complex state transitions
- authentication/authorization
- non-trivial data transformations
- complex hooks
- high-risk behavior
- regression bugs where a regression test is valuable

When a bug is discovered, prefer writing a regression test before fixing it.

Always perform appropriate verification before declaring the task complete.
