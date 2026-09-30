Stage 02 — Data pipeline + Best XI in 4-3-3. Read `CLAUDE.md`, `docs/PLAN.md` (v3, especially §3),
`docs/DECISIONS.md` (especially D19–D23, which replace D2, D3's method, D6, D12 and D15) and
`docs/reports/01-data-exploration.md` first.

Goal: turn the raw CSVs into the static JSON the app will load. For every club, pick the best 11 players
of the whole squad into the 11 slots of a canonical 4-3-3. This stage replaces the old stages 02 and 03.
No app code.

0. Housekeeping
   - Add `.gitattributes` with `* text=auto eol=lf` and renormalise once (the stage 01 report currently shows
     as modified only because of CRLF line endings). All scripts write UTF-8 with `newline="\n"`.
   - `docs/PLAN.md`, `docs/DECISIONS.md` and this prompt were updated in the planning session: commit them as-is.

1. `pipeline/best_xi.py` — pure function module, no I/O:
   - Slots (in this order): GK, LB, LCB, RCB, RB, LCM, CM, RCM, LW, ST, RW.
   - Natural eligibility by generic position in `player_positions`:
     GK←GK; LB←LB,LWB; LCB,RCB←CB; RB←RB,RWB; LCM,CM,RCM←CM,CDM,CAM; LW←LW,LM,LF; RW←RW,RM,RF; ST←ST,CF.
   - Squad = every player of the club in that version (any `club_position`: starters, SUB, RES).
   - Assignment: optimal (scipy `linear_sum_assignment`) maximising the sum of `overall`.
     Tie-breaks, in order, via small epsilon terms in the cost (they must never outweigh 1 rating point in total):
     slot matches the player's FIRST listed position; the player was in EA's starting XI; lower `player_id`.
   - Fallback only when a slot has no naturally eligible player left: allow an "adjacent" position with a
     penalty of 5 rating points, marked `fit: "adjacent"`. Define the adjacency table in the module,
     documented (e.g. LB←RB,CB; CB←CDM,LB,RB; CM←LM,RM; LW←RW,CAM,ST; ST←LW,RW,CAM; GK has no fallback).
     If a slot is still unfillable, raise.
   - Unit tests in `pipeline/tests/test_best_xi.py` (pytest; add it to requirements): a normal squad, an
     injured-star case (a high-rated SUB must enter), a squad with no natural LB (adjacent fallback),
     a tie case (deterministic result), and an unfillable GK (raises).

2. `pipeline/build.py` — writes to `app/public/data/`:
   - `versions.json`: array, one entry per version:
     `{ "id": 24, "label": "EA SPORTS FC 24", "snapshotDate": "2023-09-22",
        "leagues": [{ "id": 13, "name": "Premier League" }, ...], "teamCount": 96 }`
     Labels: 15–23 → "FIFA 15" … "FIFA 23", 24 → "EA SPORTS FC 24". Fixed league display names:
     Premier League, La Liga, Serie A, Bundesliga, Ligue 1 (not from the stale `league_name` column).
   - `<version>/teams.json`:
     ```
     { "version": 24,
       "teams": [
         { "id": 10, "name": "Manchester City", "leagueId": 13, "ovr": 85, "eaFormation": "4-3-3",
           "xi": [
             { "slot": "GK", "id": ..., "name": "Ederson", "fullName": "...", "nation": "Brazil", "age": 29,
               "positions": ["GK"], "ovr": 88, "eaPos": "GK", "fit": "natural",
               "gk": { "div": .., "han": .., "kic": .., "ref": .., "spd": .., "pos": .. } },
             { "slot": "RCM", "id": ..., "name": "K. De Bruyne", ..., "positions": ["CM", "CAM"], "ovr": 91,
               "eaPos": "SUB", "fit": "natural",
               "stats": { "pac": .., "sho": .., "pas": .., "dri": .., "def": .., "phy": .. } }
           ] } ] }
     ```
     (Values above are illustrative only; take real values from the data.)
     - `xi` has exactly 11 entries in slot order. GK gets `gk` (goalkeeping_diving/handling/kicking/
       reflexes/speed/positioning), everyone else gets `stats` (pace/shooting/passing/dribbling/defending/physic).
     - `name` = `short_name`, `fullName` = `long_name` (D16). `eaPos` = the player's `club_position` in the
       data (e.g. "LCB", "SUB", "RES"). `eaFormation` = D-M-A string derived from EA's starting XI as in stage 01.
     - Teams sorted by league, then team `ovr` descending (`ovr` from `male_teams.csv`).
     - Minified, integers as integers, no image URLs (D18/D22).
   - Filtering: top-5 leagues by `league_id` (D17); join players on (`fifa_version`, `club_team_id` = `team_id`).
   - FIFA 21: exclude Roma and Spezia (D13) via a small config list; fail loudly if any other team has
     fewer than 11 players in its squad.

3. `pipeline/validate.py` — reads only the generated JSON, exits non-zero on any failure:
   - Every team: exactly 11 players, slots are exactly the 11 slot codes, no duplicate player id.
   - Every `fit: "natural"` player is eligible for his slot per the table; `ovr` 40–99; all stats present
     and integers.
   - No player appears in two teams in the same version.
   - Team counts per league per version match stage 01 (after D13).
   - Prints a summary table: version, teams, players, number of `adjacent` fits, number of XI players whose
     `eaPos` is SUB/RES.

4. Report `docs/reports/02-pipeline.md`:
   - What was done, files, how to run (tests, `build.py`, `validate.py`), open issues, assumptions.
   - How much the Best XI differs from EA's XI: average number of changed players per team per version,
     and the 10 biggest changes overall.
   - Every `adjacent` fit: version, team, slot, player, his positions.
   - Output file sizes per version (raw and gzip).
   - Print these XIs (slot, name, positions, ovr, eaPos) so I can check them by eye:
     FIFA 21 FC Barcelona, FIFA 22 Paris Saint-Germain, FC 24 Real Madrid, FC 24 Manchester City,
     FIFA 16 Manchester United.

Commit at the end with a clear message.
