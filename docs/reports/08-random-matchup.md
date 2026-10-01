# Stage 08 report — Random matchup mode (+ finishing stage 07)

## What was done

0. **Finishing stage 07**
   - The planning docs (`docs/PLAN.md`, `docs/DECISIONS.md` D43, D45–D49, this prompt) were committed as-is in
     `8c6fd8a`.
   - `README.md` now links to the live site: https://razcohen11.github.io/og-squad-compare/
   - `docs/reports/07-deploy.md` has an update note at the top. It says the site is live, and documents the
     branch-policy fix: the `github-pages` environment only allowed `main`, so `master` was added under
     Settings → Environments → github-pages → Deployment branches and tags, and the re-run succeeded.
   - Before starting, I confirmed that the live site and `data/versions.json` return HTTP 200 and that the last
     workflow run succeeded on attempt 3. I read the run status from the public GitHub REST API.
1. **Pipeline: teams index (D45)**
   - `build.py` also writes `app/public/data/index.json`, minified, about 64 KB. It has one entry per team across
     all versions (976 entries): `{"v":24,"id":243,"name":"Real Madrid","leagueId":53,"xiAvg":86.27}`.
     `xiAvg` is the mean `ovr` of the Best XI, rounded to 2 decimals (`xi_average()`).
   - `validate.py` rebuilds the expected index from the team files on its own, then compares entry by entry. It
     fails on a wrong value, a missing team, an unknown team or a duplicate. I checked this by changing one
     average and deleting one entry: it reported both errors and exited 1. The team files themselves are unchanged.
2. **Random matchup logic** (`app/src/game/random.ts`, pure TypeScript)
   - The tuning knobs sit together at the top: `RANDOM_MIN_XI_AVG = 80` (D46), `RANDOM_MAX_AVG_DIFF = 1.0` (D47)
     and `RANDOM_HISTORY = 10` (D48).
   - **Pool:** teams with `xiAvg >= 80`.
   - **Team A** is picked uniformly from the pool.
   - **Team B** is picked uniformly from A's opponents. An opponent must be within 1.0 of A's average, must not
     be the same club in the same version (`teamKey` = version + id, so the same club in another version is
     allowed), and must not form a pair from the recent history.
   - **Sides** are swapped at random, so the stronger team is not always A.
   - **History:** the order-independent pair keys of the last 10 random matchups, kept in memory for the
     session (`rememberMatchup`).
   - **Retries:** if A has no valid opponent, A is re-picked, up to 50 times. After that the code searches all
     teams that still have an opponent, and only if none is left does it throw `RandomMatchupError` with a clear
     message.
   - **Testability:** the random source is injectable. `seededRandom()` (mulberry32) is used by the tests and by
     the samples below.
   - **Tests** (`random.test.ts`, 11 tests):
     - the config values;
     - the threshold and the 1.0 difference over 500 seeded picks from the real index;
     - no same club in the same version, while the same club across versions does come up;
     - the swap happens: the stronger team was A and B more than 100 times each in 400 picks;
     - the history over 200 picks, checked in both orders;
     - a tiny pool where the history leaves exactly one pair, then none (a clear error);
     - a pool too small or with no pair in range;
     - float tolerance at exactly 1.0 (81.27 vs 80.27);
     - determinism per seed;
     - `rememberMatchup` keeps the last 10.
3. **UI (D49)**
   - **Setup:**
     - A prominent "🎲 Random matchup" button above the manual pickers, with the hint "Two strong teams of a
       similar level, from any game." and an "or pick your own" divider. The manual mode is unchanged.
     - The button loads `index.json` (cached like the other loaders), picks a matchup, loads both version files,
       and starts the game at once.
     - While it works, the button reads "Picking a matchup…" and is disabled. Errors show inline with "Try again",
       like the existing loaders.
   - **Game header:** unchanged. It already shows both teams with their versions, which matters because players
     may not know who they got.
   - **End screen of a random game:** a full-width "🎲 Another random matchup" button under "Play again" and
     "New teams". It only appears for random games.
   - **Keyboard and focus:** unchanged from stage 06. The game screen code was not touched apart from passing
     the new props through.
   - **Fresh game every start:** `App.tsx` now gives each started game a sequence number in its key. Another
     random matchup, or a manual Start, therefore always begins a new game, even with the same teams.

## Pool and pairs

Pool size per version (`xiAvg >= 80`), from the generated `index.json`:

| version | teams | pool |
|---|---|---|
| FIFA 15 | 98 | 14 |
| FIFA 16 | 98 | 20 |
| FIFA 17 | 98 | 25 |
| FIFA 18 | 98 | 24 |
| FIFA 19 | 98 | 26 |
| FIFA 20 | 98 | 25 |
| FIFA 21 | 96 | 25 |
| FIFA 22 | 98 | 28 |
| FIFA 23 | 98 | 28 |
| EA SPORTS FC 24 | 96 | 26 |
| **total** | **976** | **241** |

- **Valid unordered pairs: 7,924.** 7,202 of them are across versions, and 432 are the same club in two
  different versions, such as Real Madrid FIFA 18 vs FIFA 19.
- **Every pool team has at least 12 valid opponents.** The median is 64 and the maximum is 112, so the
  "re-pick A" path is never needed with the real data.
- These numbers match the planning estimate in D46 and D47 (241 teams, 14–28 per version, about 7,900 pairs).

10 sample random matchups (seed 2026, with history), produced by the real `random.ts` run under Node:

| # | Team A | XI avg | Team B | XI avg | diff |
|---|---|---|---|---|---|
| 1 | Juventus · FIFA 19 | 86.36 | Manchester City · FIFA 20 | 86.45 | 0.09 |
| 2 | Juventus · FIFA 21 | 85.09 | Manchester City · FIFA 17 | 84.91 | 0.18 |
| 3 | Leicester City · FIFA 22 | 82.00 | Bayer 04 Leverkusen · FIFA 23 | 81.36 | 0.64 |
| 4 | Sevilla · FIFA 16 | 80.27 | Roma · FIFA 15 | 80.36 | 0.09 |
| 5 | Valencia · FIFA 19 | 81.82 | Roma · FIFA 16 | 80.91 | 0.91 |
| 6 | Roma · FIFA 19 | 82.45 | Borussia Dortmund · FIFA 18 | 83.36 | 0.91 |
| 7 | Chelsea · FIFA 21 | 83.64 | Chelsea · FIFA 15 | 83.45 | 0.19 |
| 8 | Liverpool · FIFA 22 | 86.73 | Real Madrid · FIFA 18 | 87.73 | 1.00 |
| 9 | Athletic Club · FC 24 | 80.09 | Real Sociedad · FIFA 22 | 81.09 | 1.00 |
| 10 | Real Madrid · FIFA 18 | 87.73 | Real Madrid · FIFA 19 | 87.82 | 0.09 |

Rows 8 and 9 sit exactly on the 1.00 limit. These are the cases the float tolerance is for.

## Files

Created:
- `app/src/game/random.ts` and `random.test.ts`
- `app/public/data/index.json` (generated)
- `docs/reports/08-random-matchup.md` and `docs/reports/08-screens/*.png`

Changed:
- `pipeline/build.py`: `xi_average()` and writing `index.json`.
- `pipeline/validate.py`: the `index.json` check.
- `app/src/data/types.ts`: `IndexEntry`.
- `app/src/data/loaders.ts`: `loadIndex()`, cached, failures not cached.
- `app/src/App.tsx`: `startRandom`, session history, mode, and a game sequence number in the key.
- `app/src/components/SetupScreen.tsx` and `.module.css`: random button, hint, error, divider.
- `app/src/components/GameScreen.tsx`: passes `onAnotherRandom` and `randomBusy` through.
- `app/src/components/EndScreen.tsx` and `.module.css`: the "Another random matchup" button.
- `README.md`: the live URL.
- `docs/reports/07-deploy.md`: the live and branch-policy note.

Deleted: none.

## How to run / verify

```bash
pipeline/.venv/Scripts/python pipeline/build.py       # also writes app/public/data/index.json
pipeline/.venv/Scripts/python pipeline/validate.py    # includes the index check
pipeline/.venv/Scripts/python -m pytest pipeline/tests -q
cd app && npm test && npm run lint && npm run build   # 48 tests
```

Results: `pytest` 19 passed, `validate.py` OK (index.json: 976 teams), `npm test` 48 passed, `npm run lint` 0
warnings, `npm run build` OK.

**Playwright** (`playwright-core` with Edge, a scratch script, 375×667, against `npm run preview`): **21/21
checks passed**.
- The setup screen shows the random button, and the manual pickers are still there.
- "Random matchup" started Real Betis · FIFA 23 vs Liverpool · FIFA 16 at once, with both versions in the header.
- 11 rounds were played, and focus never leaked to Equal.
- The end screen has "Play again", "New teams" and "Another random matchup", with no horizontal scroll.
- "Another random matchup" started a different pair (Lazio · FIFA 23 vs Olympique de Marseille · FIFA 19) at 0–0.
- Back, then "Leave game", then a manual Start played a full manual game, whose end screen has **no** random
  button.
- There were no failed requests and no console errors.

Screenshots: [setup with the button](08-screens/setup-random-button-375.png) and
[end screen with "Another random matchup"](08-screens/end-random-375.png).

## Deployment

Commit `3247eee` was pushed to `master`.

- `gh` is still not installed here, so instead of `gh run watch` I followed the workflow with the public GitHub
  REST API, polling every 15 s.
- Run [36875556520](https://github.com/RazCohen11/og-squad-compare/actions/runs/36875556520) finished with
  **success** in about one minute.
- Live checks: https://razcohen11.github.io/og-squad-compare/ → 200, `data/index.json` → 200 and
  `data/versions.json` → 200.
- **Live Playwright run:** the same random-game script played against the live URL passed **21/21**. Its games were
  Sevilla · FIFA 22 vs Manchester United · FIFA 20, then Atlético Madrid · FIFA 17 vs Chelsea · FIFA 17, with no
  failed requests and no console errors.
- This report commit is pushed afterwards, which triggers one more deploy with documentation changes only.

## Open issues

1. **Back from a random game pre-fills the manual pickers** with the random teams and versions. This is harmless
   and handy if you want to replay with one change. "New teams" still clears the clubs as before.
2. **The history is session-only (D48).** Reloading the page forgets it, so a pair can repeat right after a
   reload.
3. **Not every pool team is equally likely.** A is uniform over the pool, but B depends on how many opponents A
   has. Teams in crowded rating bands (82–85) therefore show up as B more often than isolated top teams such as
   Real Madrid 18/19. This follows D48 as written.
4. **`gh` is still missing locally.** Watching runs relies on the public API, which works because the repo is
   public.

## Assumptions not in the prompt

- `xiAvg` uses Python `round(x, 2)`, and `validate.py` recomputes it the same way. Its check is independent of
  `build.py`.
- "Within 1.0" includes exactly 1.0. A tolerance of 1e-9 absorbs float error in the difference. The ≥ 80 threshold
  uses the same tolerance.
- The history records a pair only once both team files have loaded, so a failed load does not use up a pair.
- "Another random matchup" is a full-width third button below the existing two. It only appears in random games.
- On an error from "Another random matchup", the app returns to the setup screen and shows the error by the
  random button.
- The 🎲 emoji is shown as text and hidden from screen readers. The button names are "Random matchup" and
  "Another random matchup".
