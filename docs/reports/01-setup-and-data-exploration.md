# Stage 01 report — Repo setup + data exploration

## What was done

1. **Repo setup**
   - Ran `git init` (there was no repo before) and added `.gitignore` for Python, Node, `data/raw/`, `.venv/` and OS/editor files.
   - Created `pipeline/requirements.txt` (pandas, numpy, scipy, pinned to the versions installed) and a local
     venv at `pipeline/.venv` (Python 3.11.9).
2. **Exploration script** `pipeline/explore.py`
   - Reads `male_players.csv` with `usecols` (~40 of 110 columns) and all of `male_teams.csv`. It takes about 5 s.
   - Writes `docs/reports/01-data-exploration.md` with tables for items a–k, a gap table (players missing
     from a single version) and an appendix listing clubs per version and league.
   - Everything below a marker comment in the report is preserved on re-run, which keeps the hand-written
     "Findings & risks" section. Re-running produces an identical file.
3. **Data report** `docs/reports/01-data-exploration.md`, ending with "Findings & risks" and a recommendation.

## Files

Created:
- `.gitignore`
- `pipeline/requirements.txt`
- `pipeline/explore.py`
- `docs/reports/01-data-exploration.md`
- `docs/reports/01-setup-and-data-exploration.md` (this file)

Created but not committed: `pipeline/.venv/` (gitignored).
Changed / deleted: none. `docs/PLAN.md` and `docs/DECISIONS.md` are untouched.

## How to run / verify

```bash
python -m venv pipeline/.venv
pipeline/.venv/Scripts/python -m pip install -r pipeline/requirements.txt   # Windows
pipeline/.venv/Scripts/python pipeline/explore.py                            # run from repo root
```

Then read `docs/reports/01-data-exploration.md`. For the plan's manual check, compare the section j sample
XIs, plus the FIFA 19 players flagged in the findings, against FUTBIN.

## Key results (details in the data report)

- One update per version (`fifa_update` = 2) confirmed. Dates are 18–26 Sept, **except FIFA 19 (2018-08-21)**.
- Top-5 clubs per version: 98 (FC 24: 96, because Ligue 1 had 18 clubs). **You must filter by `league_id`**,
  because `league_name` is the club's current league.
- XI of exactly 11 with one GK: **all clubs in 8 of 10 versions**. FIFA 16 has 19 clubs with 9–10 starters
  (late-summer 2015 transfers are missing from that snapshot). In FIFA 21, Roma and Spezia have no players.
- Face stats and GK stats (including `goalkeeping_speed`) have 0% nulls for every XI player.
- **`player_face_url` and `club_logo_url` do not exist** in this export. URLs can be derived from ids, but a
  `curl` probe of the SoFIFA CDN got a Cloudflare 403. Browser hotlinking is untested.
- Loans: `club_loaned_from`. Players are listed once, at the club they play for.
- Size: ~10.7k XI players in total; ~310 KB minified / ~53 KB gzipped per version.

## Open issues (need a planning decision)

1. How to handle the FIFA 16 holes. The data report recommends filling each hole with the best-fitting SUB,
   flagged in the JSON. The alternatives are dropping the 19 clubs or dropping FIFA 16.
2. FIFA 21 Roma / Spezia: the report recommends excluding them from that version.
3. Whether SoFIFA CDN images load in a real browser. If not, D6's fallback becomes the main path.
4. The launch XI includes real-world injury absences (e.g. FC 24 without De Bruyne, Courtois, Vini Jr.,
   Neuer). This is consistent with D2, but worth a conscious product decision.
5. FIFA 19's early snapshot date: FUTBIN spot checks should decide whether it is close enough to launch.
6. PLAN §4 estimates ~100 KB per version. The measured size is ~310 KB minified (~53 KB gzipped). This is not a
   problem, but the estimate in the plan is off.

## Assumptions not in the prompt

- I detected the leagues by (league name, team country) in FC 24, then tracked them by `league_id` in all
  versions. I checked this by hand for FIFA 15 EPL and Bundesliga.
- XI = players of the club with `club_position` not in {SUB, RES, null}, joined on
  (`fifa_version`, `club_team_id` = `team_id`). The club list comes from `male_teams.csv`, and I cross-checked it
  against the players file.
- For the stats null rates, "GK" in the all-players table means the first `player_positions` entry is GK. In the
  XI table it means `club_position` = GK. Both definitions agree for every XI player.
- The D-M-A formation counts wing-backs (LWB/RWB) as defenders and all DM/CM/AM/LM/RM as midfielders.
- The JSON size is measured on an illustrative object shaped like the PLAN §4 data model. It is not the real
  pipeline format.
- The comments on specific FUT ratings (FIFA 19 / FC 24) come from memory and are marked as unverified.
- I pinned the dependency versions in `requirements.txt` (pandas 3.0.6, numpy 2.4.6, scipy 1.17.1) for
  reproducibility. scipy is installed but not used yet (it is intended for stage 3).
- The git commit uses the existing global git identity on this machine.
