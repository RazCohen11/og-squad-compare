Stage 06 — Card design, flags, animations and polish. Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`
(especially D5, D22, D31, D37–D41) and `docs/reports/05-game-loop.md` first. `docs/PLAN.md`, `docs/DECISIONS.md`
and this prompt were updated in the planning session: commit them as-is.

Goal: make the game look and feel good. Game logic must not change (all existing tests keep passing).

1. Flags (D39) — pipeline + app
   - `pipeline/build.py`: add `nationCode` to every player: a lowercase ISO 3166-1 alpha-2 code matching the
     `flag-icons` package, with the UK home nations as `gb-eng`, `gb-sct`, `gb-wls`, `gb-nir` (and e.g. `xk`
     for Kosovo). Keep the mapping as an explicit table in `pipeline/nations.py`. The build must fail loudly
     if any XI player's nation is unmapped. Rebuild all versions; `validate.py` must check `nationCode` exists.
   - App: add `flag-icons` (bundled locally, no CDN) and show the flag wherever the nation is shown. Keep the
     nation name as text/tooltip for accessibility.

2. Player card (one component, states: hidden / revealed / mini) — original design (D5), not a copy of EA's
   - Tiers by `ovr` (D37): bronze ≤ 64, silver 65–74, gold ≥ 75. Each tier has its own palette (e.g. gradients),
     used only when revealed.
   - **Hidden** (D38): a neutral frame with no tier colour. Shows: an initials avatar (no photos, D22), name,
     positions, flag + nation, club + short version label, age, and "?" where the rating will be.
     The rating and stats must still not be in the DOM (D31).
   - **Revealed**: tier-coloured card with big `ovr`, the slot position, initials avatar, name, flag,
     club + version, and the six stats in two columns (PAC SHO PAS DRI DEF PHY, or DIV HAN KIC REF SPD POS for
     GKs). Keep the existing correct/wrong/"Higher"/"Your pick"/"Tie" indicators, restyled to fit.
   - **Mini** (pitch slot): tier colour, `ovr`, and a readable name — fix the current truncation ("Crist…"):
     use a shorter display form (e.g. surname, or `short_name` without the initial) and allow two lines /
     smaller font. Keep the team colour marker and the "TIE" marker.
   - Must look right at 375 px and on desktop, in the guess panel and on the end screen.

3. Animations (respect `prefers-reduced-motion`: skip or shorten them all)
   - Reveal: a card flip (hidden → revealed), ~400 ms.
   - After Next: the winner card shrinks and flies from the guess panel into its slot on the pitch, then
     becomes the mini card (~500 ms). The next round's cards appear after that.
   - End screen: a short, subtle entrance for the score. Nothing heavy.

4. Smaller UX fixes from stage 05
   - Phone "peek": during a round, a small button to temporarily collapse the guess panel and see the pitch,
     and to bring it back.
   - Back mid-game asks for confirmation (D41) with an in-app dialog; no confirmation on the setup or end screen.
   - Keyboard focus must not leak between rounds (keep the stage 05 fix working with the new animations).

5. Quality and report
   - `npm run build`, `npm run lint`, `npm test`, `pytest`, `validate.py` all pass.
   - Report `docs/reports/06-card-design.md` (what was done, files, how to run, open issues, assumptions).
     Include a Playwright full-game run like stage 05 and screenshots in `docs/reports/06-screens/` at 375 px:
     a hidden round, a revealed round with one gold and one silver (or bronze) card, a GK round revealed,
     a tie round, the back-confirmation dialog, the peek state, and the end screen; plus revealed round and end
     screen at 1280 px. Pick matchups that produce these (e.g. an older low-rated club for silver/bronze).

Commit at the end with a clear message.
