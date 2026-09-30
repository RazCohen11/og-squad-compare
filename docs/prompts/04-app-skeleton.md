Stage 04 — App skeleton. Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md` (especially D7–D9, D22, D26–D29)
and the JSON format in `docs/prompts/02-pipeline.md` §2 first. `docs/PLAN.md`, `docs/DECISIONS.md` and this
prompt were updated in the planning session: commit them as-is.

Goal: a running web app in `app/` where the user picks a game version and two clubs and sees an empty 4-3-3
pitch with 11 slots. No guessing logic and no player cards yet (stages 05 and 06).

1. Setup
   - Scaffold Vite + React + TypeScript in `app/` (strict TS). Plain CSS (CSS modules or one stylesheet per
     component); no UI library, no Tailwind, no router (D27). `vite.config.ts` uses `base: './'`.
   - Keep the existing `app/public/data/` untouched.
   - Add Vitest (D28) with one small test so the setup is proven.
   - npm scripts: `dev`, `build` (type-check + build), `preview`, `test`, `lint`.
   - Check the Node version on this machine first and state it in the report.

2. Data layer (`app/src/data/`)
   - TypeScript types that mirror `versions.json` and `<v>/teams.json` exactly (slot union type, `stats` vs `gk`).
   - Loaders that fetch relative to `import.meta.env.BASE_URL`, cache per version, and surface a readable error
     state if a fetch fails.

3. Screens (simple state machine in `App.tsx`)
   - **Setup screen:**
     - Version picker (labels from `versions.json`, newest first, default = newest).
     - Two club pickers, "Team A" and "Team B". Each is a searchable list grouped by league (league order and
       names from `versions.json`), showing club name. Picking the same club twice is not allowed.
     - Changing the version clears the club picks.
     - "Start" button, enabled only when two different clubs are picked.
   - **Game screen (skeleton only):**
     - Header: version label and "Team A vs Team B", plus a "Back" button to the setup screen.
     - A vertical pitch (D29): GK at the bottom, then LB/LCB/RCB/RB, LCM/CM/RCM, LW/ST/RW at the top, laid out
       left-to-right as the slot names say. Draw the pitch with CSS (green, simple lines), no images.
     - 11 empty slots, each an outlined card-shaped placeholder labelled with its slot code.
     - Highlight the slot for the first round (GK, per D8) as "current".
     - An empty area for the two guess cards (a placeholder box is fine) and a round indicator "1 / 11".
   - Loading and error states for data fetches.

4. Layout and quality
   - Mobile first: must look right at 375 px wide with no horizontal scroll; also fine on a desktop width.
     The pitch plus 11 slots must fit on one phone screen without scrolling the pitch itself.
   - English UI (D9). Accessible basics: real `<button>`/`<label>` elements, visible focus.
   - `npm run build`, `npm run lint` and `npm test` must pass.

5. Report `docs/reports/04-app-skeleton.md`: what was done, files, how to run (`cd app`, `npm install`,
   `npm run dev`), open issues, assumptions. If you can take screenshots (e.g. Playwright against
   `npm run preview`), save the setup screen and the game screen at 375 px and 1280 px to
   `docs/reports/04-screens/` and reference them; if not, say so.

Commit at the end with a clear message (make sure `node_modules/` and `dist/` are not committed).
