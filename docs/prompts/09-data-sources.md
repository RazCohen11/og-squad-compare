Stage 09 — Evaluate data sources for the other Ultimate Team years. Read `CLAUDE.md`, `docs/PLAN.md` (§3, §7),
`docs/DECISIONS.md` (D2, D17, D19–D23, D50–D52), `docs/BACKLOG.md` (B1, B2) and `docs/reports/01-data-exploration.md`
first. `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/BACKLOG.md` and this prompt were updated in the planning session:
commit them as-is.

Goal: decide, per game version, whether we can add it and from which source. This is an evaluation stage like
stage 01: NO changes to the app, the pipeline output or the live site. Do NOT scrape any website (D51); only use
files already downloaded and public repositories.

What we need per version (same as today): every player of every top-5-league club at the game's launch, with
club + league (to filter top 5), nationality, positions (ideally the full list, first = primary), overall (launch
base card, D23/D52), the six face stats (or six GK stats), a stable player id if possible, and a name.

Sources to evaluate:

A. Newer games — downloaded by the user from Kaggle (check what is actually in each folder):
   - `data/raw/FC 25/`  — "EA SPORTS FC 25 DATABASE, RATINGS AND STATS" (nyagami), dated ~14 Sep 2024
   - `data/raw/FC 26/`  — "FC 26 (FIFA 26) Player Data" (rovnez), dated ~22 Sep 2025
   - `data/raw/FC 27/`  — "EA SPORTS FC 27 Player Ratings" (mikedpad)
   If a folder is missing, skip it and say so.

B. Older games — public GitHub repo `https://github.com/kafagy/fifa-FUT-Data` (MIT licence; a 2018 scrape of
   Futhead FUT cards for FIFA 10–20). Clone it into `data/raw/kafagy-fut/` (gitignored). Columns are
   NAME, CLUB, LEAGUE, POSITION, TIER, RATING, PACE…PHYSICAL — all card versions mixed together (base + specials),
   no card-type column, no nationality, no player id, a single position. A first look from the planning session:
   FIFA 10 has only 1,340 gold cards; FIFA 11–14 have ~9–15k cards; the lowest-rated card per (name, club) looks like
   the base card (e.g. FIFA 14 Cristiano Ronaldo: 98/97/95/94/93/92 → base 92).

For each source / version, write to `docs/reports/09-data-sources.md`:
1. Files, columns (with examples), row counts, men/women split if mixed.
2. Evidence of the snapshot date (launch vs later in the season) and spot checks of 10 well-known players against
   ratings you are confident were the launch base ratings; mark anything uncertain as such.
3. Top-5 leagues: how to identify them, clubs per league, and whether every club has a full squad (at least 11
   players with a GK and enough players for each 4-3-3 slot per PLAN §3). Run our existing `pipeline/best_xi.py` on
   each club and report failures and `adjacent` counts.
4. Ids: can players be matched to our existing `player_id`s (FIFA 15–FC 24)? Report the match rate on players
   who also appear in FC 24 (for 25–27) or FIFA 15 (for 10–14). Same for clubs (our `team_id`s).
5. For source B specifically: a proposed rule to extract base cards (and how to detect special cards and
   winter-transfer cards), how nationality could be filled (e.g. name match to FIFA 15 data) and its coverage,
   and an honest verdict on FIFA 10 (incomplete) and on data quality per version.
6. Gaps vs our current JSON format (e.g. single position, missing nationality → flags, missing stats).
7. A final table: version | recommended source | include now / include with caveats / not feasible | effort |
   main risks. Plus your recommendation for the order of integration.

Also check, without downloading anything: is there any FIFA 09 Ultimate Team data in the sources above? (Expected:
no.) Mention other sources you know of only as notes, clearly marked "not evaluated".

Commit at the end (data stays gitignored). Do not push (no app change, nothing to deploy).
