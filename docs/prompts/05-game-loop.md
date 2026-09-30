Stage 05 — Game loop + per-team version. Read `CLAUDE.md` (updated), `docs/PLAN.md`, `docs/DECISIONS.md`
(especially D7, D8, D30–D36) and `docs/reports/04-app-skeleton.md` first. `CLAUDE.md`, `docs/PLAN.md`,
`docs/DECISIONS.md` and this prompt were updated in the planning session: commit them as-is.

Goal: a fully playable game. Card visuals stay simple (text-only) — the real card design, flags and animations
are stage 06. Keep the card a single component with `hidden` / `revealed` states so stage 06 can restyle it.

1. Setup screen: per-team version (D30)
   - Replace the single version picker with one version picker per team: "Team A: version + club",
     "Team B: version + club". Both default to the newest version.
   - Changing a team's version clears only that team's club.
   - The same club is allowed in two different versions (Barcelona FIFA 15 vs Barcelona FIFA 17); only the same
     club in the same version is blocked.
   - Everywhere a team is named in the game, show its version too (e.g. "FC Barcelona · FIFA 15").
   - Loading two different version files must work (the loaders already cache per version).

2. Game logic — pure TypeScript in `app/src/game/` (reducer or equivalent), no React inside:
   - Rounds follow the slot order from D8 (GK, LB, LCB, RCB, RB, LCM, CM, RCM, LW, ST, RW). Round i compares
     Team A's player in slot i with Team B's player in slot i.
   - Guess options: "A is higher", "B is higher", "Equal" (D7). Correct answer from `ovr`.
   - After a guess: phase "revealed". The slot winner is the higher `ovr`; on a tie it is Team A's player,
     flagged as a tie (D32). "Next" moves to the next round (D36); after round 11 → phase "finished".
   - State tracks per round: guess, correct answer, correct/wrong, winner side. Derived: correct count, wrong
     count (main score, D33), and slots won by A / B / ties (secondary score).
   - "Play again" restarts with the same two teams; "New teams" returns to setup keeping both version picks.
   - Vitest tests for the logic: correct/wrong for all three options, tie placement, round order, finishing
     after 11 rounds, score derivation, restart.

3. Game screen
   - Top: the main score, prominent: ✓ correct and ✗ wrong, plus "Round n / 11" and the current slot. The
     secondary team tally (A slots – B slots) is smaller. Header shows both teams with versions and Back.
   - Each team gets a subtle colour (e.g. blue for A, red for B) used for small markers only.
   - Guessing (D35): on phones, the two hidden cards appear large as an overlay over a dimmed pitch; on
     desktop, next to the pitch as now. Tapping a card = guessing that team; an "Equal" button sits between or
     below the cards. Keyboard: Left/1 = A, Right/2 = B, E/= = Equal, Enter/Space = Next.
   - Hidden card (D31): name, positions, nation (text for now), club + version, age. The rating and stats must
     NOT be rendered in the DOM before the reveal.
   - Revealed: both cards show `ovr` and the six stats (or the six GK stats); mark the correct answer, show
     whether the guess was right, show "Tie" when equal. Then "Next".
   - After Next, the slot on the pitch shows a mini card of the winner: name, `ovr`, team colour marker
     (and "Tie" marker when relevant). Filled slots stay filled for the rest of the game.

4. End screen (D34)
   - Big "X / 11 correct", the secondary tally, the combined XI on the pitch (all 11 filled), and a compact list
     of the 11 rounds: slot, both players with `ovr`, guess, ✓/✗.
   - Buttons "Play again" and "New teams".

5. Quality
   - Still fits a 375 px phone with no horizontal scroll; the overlay must be usable one-handed (cards and the
     Equal button reachable, text readable).
   - `npm run build`, `npm run lint`, `npm test` pass.
   - Report `docs/reports/05-game-loop.md` (what was done, files, how to run, open issues, assumptions).
     Using Playwright like in stage 04, play one full game automatically (FC Barcelona FIFA 15 vs Real Madrid
     FIFA 17) and save screenshots at 375 px of: setup with two different versions, a hidden round, a revealed
     round, a tie round if one exists in any quick-to-find matchup, and the end screen; plus the end screen at
     1280 px. Put them in `docs/reports/05-screens/`.

Commit at the end with a clear message.
