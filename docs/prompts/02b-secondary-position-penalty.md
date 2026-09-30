Stage 02b — Fix: secondary-position penalty. Read `docs/DECISIONS.md` D24–D26 and `docs/PLAN.md` §3 (both
updated in the planning session; commit them as-is) and `docs/reports/02-pipeline.md` (open issue 1).

Context: with no penalty, 13% of picks sit in a slot matching only a secondary position, and star wingers land
in central midfield via CAM (e.g. FIFA 22 PSG: Neymar at LCM). The planning session simulated penalties of
0/2/3/5 on your `best_xi.py` and chose 3 (D24).

1. `pipeline/best_xi.py`
   - Add `SECONDARY_PENALTY = 3`. A natural pick whose slot does NOT match the player's first listed position is
     valued at `overall - SECONDARY_PENALTY`. First-position natural picks are unchanged. Adjacent picks are
     unchanged (they already never get the first-position bonus).
   - Keep the existing tie-break bonuses and their guarantees. Update the module docstring.
2. Tests: add cases for
   - a wide-first player with CAM as secondary: he goes to LW/RW instead of CM when a natural CM exists within
     3 points, and still goes to CM when the gap is larger than 3;
   - a secondary pick still beating a much weaker primary pick (e.g. CB 85 at RB over RB 78).
   Existing tests must still pass (adjust expectations only where the new rule changes them, and say which).
3. Rebuild with `build.py`, run `validate.py` and the tests.
4. Update `docs/reports/02-pipeline.md` (regenerate the data sections with `report_02.py`) and add a short
   "02b" section at the end with:
   - secondary-position picks before/after (count and %), and the number of XI players whose first position is
     wide/attacking (LW, RW, LM, RM, LF, RF, ST, CF) sitting in LCM/CM/RCM, before/after;
   - average XI rating sum per version before/after;
   - the sample XIs again, plus FIFA 22 Paris Saint Germain (full) and FIFA 18 Liverpool.
   Expected (from the planning simulation): about 489 secondary picks (4.6%), 27 wide-first players in CM;
   FIFA 22 PSG with Neymar LW, Mbappé ST, Messi RW; FC 24 Real Madrid with F. Mendy LB, Carvajal RB, Joselu ST.
   If your numbers differ, explain why.

Commit at the end with a clear message.
