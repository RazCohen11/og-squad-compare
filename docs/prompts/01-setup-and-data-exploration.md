Stage 01 — Repo setup + data exploration. Read `CLAUDE.md`, `docs/PLAN.md` and `docs/DECISIONS.md` first.

Goal: validate that the Kaggle dataset can give us, for every game version FIFA 15 – FC 24,
the launch-roster starting XI of every club in the top 5 leagues. No app code in this stage.

Data location: `data/raw/FIFA 15-24/` (note the space in the folder name). Use `male_players.csv` (~96 MB)
and `male_teams.csv`. Ignore the female_* and coaches files and the .zip.
Known already: this export has ONE update per version (`fifa_update` = 2.0, dated at launch, e.g. 2014-09-18
for FIFA 15). We treat that snapshot as the launch roster.

1. Repo setup
   - `git init` (if not already), add `.gitignore` (Python, Node, `data/raw/`, `.venv/`).
   - Create `pipeline/` with a `requirements.txt` (pandas, numpy, scipy) and a local venv.

2. Exploration script `pipeline/explore.py` (read CSVs in chunks or with `usecols` — the file is large).
   Produce `docs/reports/01-data-exploration.md` answering, with tables:
   a. Columns available in `male_players.csv` and `male_teams.csv` (names + example values).
   b. For each `fifa_version`: confirm the single `fifa_update` value, its `update_as_of` date and row count.
   c. Number of clubs per league for the 5 leagues
      (English Premier League, Spain Primera División / La Liga, Italian Serie A, German 1. Bundesliga,
      French Ligue 1 — detect the exact league names in the data and list them).
   d. Per version: how many of those clubs have exactly 11 players whose `club_position` is not SUB/RES/null.
      List every club that does NOT have exactly 11, with the count and the positions found.
   e. All distinct `club_position` values across the data, with frequency.
   f. Derived formation per club (count of defenders / midfielders / attackers from the XI positions);
      frequency table of formations per version.
   g. Stats availability: pace/shooting/passing/dribbling/defending/physic for outfield players and
      goalkeeping_* columns (incl. goalkeeping_speed) for GKs — null rates per version.
   h. `player_face_url` and `club_logo_url`: null rates, 3 example URLs.
   i. Loans: is there any column indicating loan (e.g. `club_loaned_from`)? Are loaned players listed at the
      club they play for?
   j. A sample for manual verification: for FIFA 19 and FC 24 launch, print the XI (name, club_position,
      overall) of Real Madrid, Liverpool, Bayern München, Juventus, Paris Saint-Germain.
   k. Rough size estimate: total starting-XI players across the 10 versions, and estimated JSON size
      per version if we keep ~15 fields per player.

3. End the report with a short "Findings & risks" section: anything that breaks the assumptions in
   `docs/PLAN.md` (sections 1–3), and your recommendation.

Do not build the pipeline output or the app yet. Commit at the end with a clear message.
