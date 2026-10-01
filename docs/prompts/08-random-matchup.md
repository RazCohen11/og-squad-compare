Stage 08 — Random matchup mode (+ finish stage 07). Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`
(especially D43, D45–D49) and `docs/reports/07-deploy.md` first. `docs/PLAN.md`, `docs/DECISIONS.md` and this
prompt were updated in the planning session: commit them as-is.

Context: the site is live at https://razcohen11.github.io/og-squad-compare/ (GitHub user `RazCohen11`). The first
deploy failed because the `github-pages` environment only allowed `main`; `master` was added as a deployment
branch policy by hand, and the re-run succeeded.

0. Finish stage 07
   - Put the real URL in `README.md`. Add a note to `docs/reports/07-deploy.md` about the branch-policy fix
     above (so it is documented), and that the site is live.

1. Pipeline: teams index
   - `build.py` also writes `app/public/data/index.json`: one entry per team across all versions:
     `{ "v": 24, "id": 243, "name": "Real Madrid", "leagueId": 53, "xiAvg": 86.27 }` (xiAvg = mean `ovr` of the
     Best XI, 2 decimals, D45). Minified. `validate.py` checks it matches the team files exactly (same teams,
     same averages).

2. App: random matchup logic — pure TS in `app/src/game/random.ts`, with Vitest tests
   - Config constants in one place: `RANDOM_MIN_XI_AVG = 80` (D46), `RANDOM_MAX_AVG_DIFF = 1.0` (D47),
     `RANDOM_HISTORY = 10` (D48).
   - Pool = teams with `xiAvg >= RANDOM_MIN_XI_AVG`. Pick A uniformly from the pool; pick B uniformly from pool
     teams with `|xiAvg(A) − xiAvg(B)| <= RANDOM_MAX_AVG_DIFF`, excluding the same club in the same version
     (the same club in another version is allowed). Randomly swap A/B so the stronger team is not always A.
   - Avoid any pair (in either order) seen in the last `RANDOM_HISTORY` random matchups of this session
     (in memory only). If A has no valid B, re-pick A (bounded retries; fail with a clear error if impossible).
   - Inject the random source so tests are deterministic. Tests: threshold respected, difference respected,
     no same-club-same-version, history respected, swap happens, a tiny pool edge case.

3. UI (D49)
   - Setup screen: a prominent "🎲 Random matchup" button (above or next to the manual pickers — manual mode
     stays exactly as it is). It loads `index.json`, picks a matchup, loads the two version files and starts
     the game immediately. Show a loading state; handle errors like the existing loaders.
   - Game header for a random game: keep showing both teams with versions (players may not know who they got).
   - End screen of a random game: add "🎲 Another random matchup" next to "Play again" and "New teams".
   - Keyboard/focus behaviour must stay as in stage 06.

4. Quality, report, deploy
   - All checks pass (`npm run build`, `npm run lint`, `npm test`, pytest, `validate.py`).
   - Report `docs/reports/08-random-matchup.md`: what was done, files, open issues, assumptions; pool size per
     version, number of valid pairs, and 10 sample random matchups (seeded) with both averages.
   - Playwright: one random game end to end at 375 px (screenshots of setup with the button, and the end screen
     with "Another random matchup") in `docs/reports/08-screens/`.
   - Commit, then `git push` (this redeploys the site). Watch the run (`gh run watch`), then confirm the live site
     and `data/index.json` return HTTP 200.
