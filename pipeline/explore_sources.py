"""Stage 09: evaluate data sources for the other Ultimate Team years (FIFA 10-14, FC 25-27).

Reads only files already on disk (no scraping, D51) and writes the data sections of
docs/reports/09-data-sources.md. Everything below MANUAL_MARKER in an existing report is kept.

Sources:
    data/raw/FC 25/male_players.csv          (Kaggle, nyagami; EA ratings site)
    data/raw/FC 26/FC26_20250921.csv         (Kaggle, rovnez; SoFIFA format)
    data/raw/FC 27/players.csv               (Kaggle, mikedpad; EA ratings API)
    data/raw/kafagy-fut/FIFA10..20.csv       (GitHub kafagy/fifa-FUT-Data; Futhead scrape)
    data/raw/kafagy-fut/FutBinCards19.csv    (same repo; FutBin FIFA 19 with card type, used to test rules)
Reference: data/raw/FIFA 15-24/male_players.csv (our current SoFIFA source).

Run from the repository root:
    pipeline/.venv/Scripts/python pipeline/explore_sources.py
"""

import json
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from best_xi import Player, UnfillableSlotError, best_xi
from explore import md_table, pct
from nations import NATION_CODES

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
REF_PLAYERS = RAW / "FIFA 15-24" / "male_players.csv"
KAFAGY = RAW / "kafagy-fut"
REPORT = ROOT / "docs" / "reports" / "09-data-sources.md"
MANUAL_MARKER = "<!-- MANUAL SECTION BELOW: preserved when explore_sources.py is re-run -->"

LEAGUE_KEYS = ["EPL", "LaLiga", "SerieA", "Bundesliga", "Ligue1"]
REF_LEAGUE_IDS = {13: "EPL", 53: "LaLiga", 31: "SerieA", 19: "Bundesliga", 16: "Ligue1"}

# League names of the top 5 in the EA ratings data (FC 25, FC 27)
EA_LEAGUES = {
    "Premier League": "EPL",
    "LALIGA EA SPORTS": "LaLiga",
    "Serie A Enilive": "SerieA",
    "Bundesliga": "Bundesliga",
    "Ligue 1 McDonald's": "Ligue1",
}

# League names of the top 5 in the Futhead data, per version (checked by hand against each file's league list)
_FH_OLD = {"Barclays PL": "EPL", "Liga BBVA": "LaLiga", "Serie A": "SerieA", "Bundesliga": "Bundesliga", "Ligue 1": "Ligue1"}
_FH_17 = {"Premier League": "EPL", "LaLiga Santander": "LaLiga", "Calcio A": "SerieA", "Bundesliga": "Bundesliga", "Ligue 1": "Ligue1"}
_FH_19 = {
    "England Premier League": "EPL",
    "Spain Primera Division": "LaLiga",
    "Italy Serie A": "SerieA",
    "Germany 1. Bundesliga": "Bundesliga",
    "France Ligue 1": "Ligue1",
}
FUTHEAD_LEAGUES = {
    10: {**_FH_OLD, "Barclays Premier League": "EPL"},
    11: {**_FH_OLD, "Barclays Premier League": "EPL"},
    12: {**_FH_OLD, "La Liga BBVA": "LaLiga"},
    13: {**_FH_OLD, "La Liga BBVA": "LaLiga"},
    14: _FH_OLD,
    15: _FH_OLD,
    16: _FH_OLD,
    17: _FH_17,
    18: _FH_17,
    19: _FH_19,
    20: _FH_19,
}
FUTBIN19_LEAGUES = {
    "Premier League": "EPL",
    "LaLiga Santander": "LaLiga",
    "Serie A TIM": "SerieA",
    "Bundesliga": "Bundesliga",
    "Ligue 1 Conforama": "Ligue1",
}

# Spot checks: (version, name regex, expected launch base rating, confidence)
SPOT_CHECKS = {
    "FC 25": [
        ("Kylian Mbapp", 91, "confident"), ("Rodri$", 91, "confident"), ("Erling Haaland", 91, "confident"),
        ("Jude Bellingham", 90, "confident"), ("Vini Jr", 90, "confident"), ("Harry Kane", 90, "confident"),
        ("Kevin De Bruyne", 90, "confident"), ("Mohamed Salah", 89, "likely"), ("Virgil van Dijk", 89, "likely"),
        ("Lamine Yamal", 81, "likely"),
    ],
    "FC 26": [
        ("Mbapp", 91, "uncertain"), ("Salah", 91, "uncertain"), ("Dembélé", 90, "uncertain"),
        ("Haaland", 90, "uncertain"), ("Kane", 89, "uncertain"), ("Yamal", 89, "uncertain"),
        ("Vini", 89, "uncertain"), ("Pedri", 89, "uncertain"), ("van Dijk", 90, "uncertain"),
        ("Courtois", 89, "uncertain"),
    ],
    "FC 27": [
        ("Mbapp", None, "after my knowledge cutoff"), ("Haaland", None, "after my knowledge cutoff"),
        ("Courtois", None, "after my knowledge cutoff"), ("Kane", None, "after my knowledge cutoff"),
        ("Dembélé", None, "after my knowledge cutoff"), ("^Rodri$", None, "after my knowledge cutoff"),
        ("Yamal", None, "after my knowledge cutoff"), ("Salah", None, "after my knowledge cutoff"),
        ("Bellingham", None, "after my knowledge cutoff"), ("van Dijk", None, "after my knowledge cutoff"),
    ],
    # Futhead base cards; FIFA 12-14 Messi / Ronaldo are well known, others less certain
    10: [("Lionel Messi", 90, "likely"), ("Cristiano Ronaldo", 89, "likely"), ("Kak", 89, "uncertain"),
         ("Xavi", 88, "uncertain"), ("Steven Gerrard", 88, "uncertain")],
    11: [("Lionel Messi", 90, "likely"), ("Cristiano Ronaldo", 89, "likely"), ("Xavi", 89, "uncertain"),
         ("Wayne Rooney", 88, "uncertain"), ("Iniesta", 89, "uncertain")],
    12: [("Lionel Messi", 94, "confident"), ("Cristiano Ronaldo", 92, "confident"), ("Xavi", 91, "uncertain"),
         ("Wayne Rooney", 88, "uncertain"), ("Iniesta", 90, "uncertain")],
    13: [("Lionel Messi", 94, "confident"), ("Cristiano Ronaldo", 92, "confident"), ("^Iniesta$", 90, "uncertain"),
         ("Xavi", 89, "uncertain"), ("^Falcao$", 88, "uncertain")],
    14: [("Lionel Messi", 94, "confident"), ("Cristiano Ronaldo", 92, "confident"), ("Franck Rib", 90, "likely"),
         ("Zlatan Ibrahimovi", 90, "likely"), ("Gareth Bale", 87, "uncertain")],
}


# ---------------------------------------------------------------------- helpers
def norm(text) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces."""
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z ]", " ", t.lower().replace("ø", "o").replace("ß", "ss").replace("ł", "l"))
    return re.sub(r"\s+", " ", t).strip()


def run_best_xi(squads: dict) -> tuple[int, int, int, list[str]]:
    """Run best_xi on {club: [Player]}. Returns (ok clubs, failed clubs, adjacent fits, failure notes)."""
    ok = failed = adjacent = 0
    notes = []
    for club, squad in squads.items():
        try:
            picks = best_xi(squad)
            ok += 1
            adjacent += sum(p.fit == "adjacent" for p in picks)
        except UnfillableSlotError as e:
            failed += 1
            notes.append(f"{club} ({len(squad)} players): {e}")
        except ValueError as e:
            failed += 1
            notes.append(f"{club}: {e}")
    return ok, failed, adjacent, notes


def club_table(df: pd.DataFrame) -> pd.DataFrame:
    """Clubs per top-5 league and squad sizes. Expects columns league, club, is_gk."""
    rows = []
    for key in LEAGUE_KEYS:
        d = df[df.league == key]
        sizes = d.groupby("club").size()
        gks = d[d.is_gk].groupby("club").size().reindex(sizes.index, fill_value=0)
        rows.append({
            "league": key, "clubs": len(sizes), "players": len(d),
            "min squad": int(sizes.min()) if len(sizes) else 0, "max squad": int(sizes.max()) if len(sizes) else 0,
            "clubs < 11": int((sizes < 11).sum()), "clubs without GK": int((gks == 0).sum()),
        })
    return pd.DataFrame(rows)


def ref_name_keys(row) -> set[str]:
    """Name keys of a SoFIFA player, used to match sources without ids."""
    long_n, short_n = norm(row.long_name), norm(row.short_name)
    keys = {long_n, short_n}
    long_t = long_n.split()
    short_t = [t for t in short_n.split() if len(t) > 1]
    if long_t and short_t:
        keys.add(f"{long_t[0]} {' '.join(short_t)}")
        keys.add(f"{long_t[0]} {long_t[-1]}")
    keys.discard("")
    return keys


def build_name_index(ref: pd.DataFrame) -> dict[str, set[int]]:
    index: dict[str, set[int]] = defaultdict(set)
    for row in ref.drop_duplicates("player_id").itertuples(index=False):
        for k in ref_name_keys(row):
            index[k].add(int(row.player_id))
    return index


def match_name(name: str, index: dict[str, set[int]]) -> int | None:
    ids = index.get(norm(name), set())
    return next(iter(ids)) if len(ids) == 1 else None


def file_columns(df: pd.DataFrame, limit: int = 60) -> pd.DataFrame:
    rows = []
    for c in df.columns[:limit]:
        non_null = df[c].dropna()
        ex = str(non_null.iloc[0]) if len(non_null) else "(empty)"
        rows.append({"column": c, "example": ex[:60] + ("…" if len(ex) > 60 else "")})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------- loaders to one common shape
# Common columns: pid, name, club, club_id, league, nation, positions (tuple), ovr, is_gk, s1..s6 (face or GK stats)
FACE = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]


def load_fc25() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "FC 25" / "male_players.csv")
    d = pd.DataFrame({
        "pid": raw.url.str.extract(r"/(\d+)$")[0].astype(int),
        "name": raw.Name,
        "club": raw.Team,
        "club_id": None,
        "league": raw.League.map(EA_LEAGUES),
        "nation": raw.Nation,
        "positions": [
            tuple([p] + ([x.strip() for x in str(alt).split(",")] if isinstance(alt, str) else []))
            for p, alt in zip(raw.Position, raw["Alternative positions"])
        ],
        "ovr": raw.OVR,
        "age": raw.Age,
    })
    d["is_gk"] = raw.Position == "GK"
    for i, (f, g) in enumerate(zip(["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"],
                                   ["GK Diving", "GK Handling", "GK Kicking", "GK Reflexes", "PAC", "GK Positioning"])):
        d[f"s{i + 1}"] = raw[g].where(d.is_gk, raw[f])
    return raw, d


def load_fc26() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "FC 26" / "FC26_20250921.csv", low_memory=False)
    top = raw.league_id.map(REF_LEAGUE_IDS).where(raw.league_level == 1)
    d = pd.DataFrame({
        "pid": raw.player_id,
        "name": raw.short_name,
        "club": raw.club_name,
        "club_id": raw.club_team_id,
        "league": top,
        "nation": raw.nationality_name,
        "positions": [tuple(p.strip() for p in str(x).split(",")) for x in raw.player_positions],
        "ovr": raw.overall,
        "age": raw.age,
    })
    d["is_gk"] = d.positions.str[0] == "GK"
    gk = ["goalkeeping_diving", "goalkeeping_handling", "goalkeeping_kicking", "goalkeeping_reflexes",
          "goalkeeping_speed", "goalkeeping_positioning"]
    for i, (f, g) in enumerate(zip(FACE, gk)):
        d[f"s{i + 1}"] = raw[g].where(d.is_gk, raw[f])
    return raw, d


def load_fc27() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "FC 27" / "players.csv")
    men = raw[raw.gender == "Men's Football"].copy()
    name = men.common_name.where(men.common_name.notna(), men.first_name.fillna("") + " " + men.last_name.fillna(""))
    d = pd.DataFrame({
        "pid": men.player_id,
        "name": name.str.strip(),
        "club": men.club,
        "club_id": None,
        "league": men.league.map(EA_LEAGUES),
        "nation": men.nationality,
        "positions": [
            tuple([p] + (str(alt).split() if isinstance(alt, str) else []))
            for p, alt in zip(men.position, men.alternate_positions)
        ],
        "ovr": men.overall_rating,
        "age": None,
    })
    d["is_gk"] = men.position == "GK"
    gk = ["goalkeeping_diving", "goalkeeping_handling", "goalkeeping_kicking", "goalkeeping_reflexes",
          "pace", "goalkeeping_positioning"]
    for i, (f, g) in enumerate(zip(["pace", "shooting", "passing", "dribbling", "defending", "physicality"], gk)):
        d[f"s{i + 1}"] = men[g].where(d.is_gk, men[f])
    return raw, d.reset_index(drop=True)


def futhead(version: int) -> pd.DataFrame:
    d = pd.read_csv(KAFAGY / f"FIFA{version}.csv")
    d["league"] = d.LEAGUE.map(FUTHEAD_LEAGUES[version])
    return d


def base_cards(cards: pd.DataFrame, name_col="NAME", club_col="CLUB", rating_col="RATING") -> pd.DataFrame:
    """Proposed base-card rule for card lists without a card-type column.

    1. Drop exact duplicate rows.
    2. Per (name, club): keep the lowest-rated card (special cards are always rated higher than the base).
    3. Per name: if the same name has groups at several clubs, keep only the group(s) whose lowest card equals the
       name's overall lowest card. A club where the player only has higher cards is a special card that was issued at
       another club (typically a winter transfer, or an in-form after the move).
    """
    c = cards.drop_duplicates().copy()
    c["_stat_sum"] = c[["PACE", "SHOOTING", "PASSING", "DRIBBLING", "DEFENDING", "PHYSICAL"]].sum(axis=1) \
        if "PACE" in c.columns else 0
    c = c.sort_values([rating_col, "_stat_sum"]).groupby([name_col, club_col], as_index=False).head(1)
    name_min = c.groupby(name_col)[rating_col].transform("min")
    c["special_only_club"] = c[rating_col] > name_min
    return c


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    out: list[str] = []
    w = out.append

    print("Loading reference (FIFA 15-24)…")
    ref = pd.read_csv(REF_PLAYERS, usecols=[
        "player_id", "fifa_version", "short_name", "long_name", "overall", "club_team_id", "club_name", "league_id",
        "league_level", "nationality_name", "player_positions", *FACE,
    ], low_memory=False)
    ref["fifa_version"] = ref.fifa_version.astype(int)
    ref_ids = set(ref.player_id)
    ref_by_id_latest = ref.sort_values("fifa_version").drop_duplicates("player_id", keep="last").set_index("player_id")
    fc24 = ref[ref.fifa_version == 24]
    fc24_top = fc24[fc24.league_id.isin(REF_LEAGUE_IDS) & (fc24.league_level == 1)]
    xi24 = json.loads((ROOT / "app" / "public" / "data" / "24" / "teams.json").read_text(encoding="utf-8"))
    xi24_ids = {p["id"] for t in xi24["teams"] for p in t["xi"]}
    ref_team_ids = set(ref.club_team_id.dropna().astype(int))

    w("# Stage 09 — Data sources for the other Ultimate Team years")
    w("")
    w("Generated by `pipeline/explore_sources.py` from files already on disk (no scraping, D51). Hand-written findings,")
    w("the per-version verdict and the recommendation are in the manual section at the end.")
    w("")

    # ================================================================== A. Newer games
    w("## A. Newer games: FC 25, FC 26, FC 27")
    w("")
    zips = {
        "FC 25": RAW / "FC 25" / "raw data FC 25.zip",
        "FC 26": RAW / "FC 26" / "raw data FC 26.zip",
        "FC 27": RAW / "FC 27" / "raw data FC 27.zip",
    }
    loaders = {"FC 25": load_fc25, "FC 26": load_fc26, "FC 27": load_fc27}
    summary_rows = []
    # EA club name -> our team_id, learned from FC 25 (EA names are reused in later EA data)
    ea_club_alias: dict[str, int] = {}
    # FC 26 player id -> SoFIFA team id, used to place clubs that are new in FC 27
    fc26_club_by_pid: dict[int, int] = {}
    for label, loader in loaders.items():
        print(f"{label}…")
        raw, d = loader()
        top = d[d.league.notna()].copy()
        w(f"### {label}")
        w("")

        # 1. Files, columns, rows
        folder = zips[label].parent
        files = sorted(p.name for p in folder.iterdir())
        w(f"**1. Files.** `data/raw/{label}/`: {', '.join(f'`{f}`' for f in files)}.")
        with zipfile.ZipFile(zips[label]) as z:
            w("Zip entries: " + ", ".join(f"`{i.filename}` ({i.file_size:,} B, {i.date_time[0]}-{i.date_time[1]:02d}-{i.date_time[2]:02d})"
                                          for i in z.infolist()) + ".")
        w("")
        if label == "FC 25":
            fem = pd.read_csv(folder / "female_players.csv")
            allp = pd.read_csv(folder / "all_players.csv")
            w(f"Rows: `male_players.csv` {len(raw):,}, `female_players.csv` {len(fem):,}, `all_players.csv` "
              f"{len(allp):,} (= men + women). The evaluation uses the men's file.")
        elif label == "FC 26":
            w(f"Rows: {len(raw):,}. No gender column; every league is a men's league (SoFIFA men's database).")
        else:
            men_n = int((raw.gender == "Men's Football").sum())
            women_n = int((raw.gender == "Women's Football").sum())
            w(f"Rows: {len(raw):,} ({men_n:,} men, {women_n:,} women, column `gender`). The evaluation uses the men.")
        w("")
        w(f"<details><summary>{len(raw.columns)} columns with examples</summary>")
        w("")
        w(md_table(file_columns(raw, limit=len(raw.columns))))
        w("")
        w("</details>")
        w("")

        # 2. Snapshot and spot checks
        if label == "FC 25":
            snap = ("No date column. Ratings come from the EA ratings site (URL per player); the zip entries are dated "
                    "2024-09-26, the day before the full release (2024-09-27).")
        elif label == "FC 26":
            snap = (f"`fifa_update` = {sorted(int(x) for x in raw.fifa_update.unique())}, `fifa_update_date` = "
                    f"{sorted(str(x) for x in raw.fifa_update_date.unique())} (FC 26 early access opened 2025-09-19; "
                    "full release 2025-09-26).")
        else:
            snap = (f"`snapshot_date` = {sorted(str(x) for x in raw.snapshot_date.unique())}, `edition` = "
                    f"{sorted(str(x) for x in raw.edition.unique())}.")
        w(f"**2. Snapshot.** {snap}")
        w("")
        rows = []
        for pattern, expected, conf in SPOT_CHECKS[label]:
            hit = d[d.name.str.contains(pattern, regex=True, na=False)].sort_values("ovr", ascending=False).head(1)
            got = int(hit.ovr.iloc[0]) if len(hit) else None
            rows.append({
                "player": hit.name.iloc[0] if len(hit) else pattern, "club": hit.club.iloc[0] if len(hit) else "",
                "rating in data": got if got is not None else "not found",
                "expected": expected if expected is not None else "—", "confidence": conf,
                "match": "" if expected is None or got is None else ("✓" if got == expected else "✗"),
            })
        w(md_table(pd.DataFrame(rows)))
        w("")

        # 3. Top-5 leagues and squads
        w(f"**3. Top-5 leagues.** " + (
            "By `league` name: " + ", ".join(f"`{k}` → {v}" for k, v in EA_LEAGUES.items()) + "."
            if label != "FC 26" else "By SoFIFA `league_id` (13, 53, 31, 19, 16) with `league_level` 1, as today (D17)."))
        w("")
        w(md_table(club_table(top)))
        w("")
        squads = {
            f"{league}/{club}": [
                Player(id=int(p.pid), overall=int(p.ovr), positions=tuple(p.positions), ea_pos=None)
                for p in g.itertuples(index=False)
            ]
            for (league, club), g in top.groupby(["league", "club"])
        }
        ok, failed, adjacent, notes = run_best_xi(squads)
        w(f"`best_xi.py` on every club: **{ok} ok, {failed} failed**, {adjacent} `adjacent` fits in total."
          + ("" if not notes else " Failures: " + "; ".join(notes[:10]) + "."))
        w("")
        pos_lists = top.positions.str.len()
        w(f"Positions per player (top 5): mean {pos_lists.mean():.2f}, max {pos_lists.max()}; "
          f"stats present: {pct(top[[f's{i}' for i in range(1, 7)]].notna().all(axis=1).mean())}; "
          f"nation present: {pct(top.nation.notna().mean())}.")
        known = top.nation.isin(NATION_CODES)
        unknown = Counter(top.nation[~known])
        w(f"Nation names already in our flag table (`pipeline/nations.py`): {pct(known.mean())} of top-5 players"
          + ("." if not unknown else "; missing: " + ", ".join(f"{n} ({c})" for n, c in unknown.most_common(15)) + "."))
        gk_speed = "own column" if label == "FC 26" else "taken from the GK's `PAC`/`pace` (EA shows a GK's speed there)"
        w(f"GK speed: {gk_speed}.")
        w("")

        # 4. Ids
        in_ref = top.pid.isin(ref_ids)
        consistent = []
        for p in top[in_ref].itertuples(index=False):
            r = ref_by_id_latest.loc[p.pid]
            src_tokens = set(norm(p.name).split())
            ref_tokens = set(norm(r.long_name).split()) | set(norm(r.short_name).split())
            consistent.append(bool(src_tokens & ref_tokens))
        xi_found = len(xi24_ids & set(d.pid)) / len(xi24_ids)
        w(f"**4. Ids.** Top-5 players whose id exists in our FIFA 15–FC 24 data: {pct(in_ref.mean())} "
          f"({int(in_ref.sum()):,} of {len(top):,}); of those, the name agrees with our record for "
          f"{pct(sum(consistent) / max(len(consistent), 1))}. Our FC 24 Best-XI players (1,056) found in this file by id "
          f"(any league): {pct(xi_found)}.")
        if label == "FC 26":
            fc26_club_by_pid.update({int(p): int(c) for p, c in zip(d.pid, d.club_id) if pd.notna(c)})
            clubs = top.drop_duplicates("club_id")
            w(f"Clubs: `club_team_id` is SoFIFA's team id; {pct(clubs.club_id.isin(ref_team_ids).mean())} of the "
              f"{len(clubs)} top-5 clubs exist in our data (any version, any league).")
        else:
            # Club id by majority vote: the FC 24 club of most of the club's players (ids are shared)
            ref24_club = fc24.set_index("player_id").club_team_id
            team_names = ref.dropna(subset=["club_team_id"]).drop_duplicates("club_team_id", keep="last") \
                .set_index("club_team_id").club_name
            rows = []
            for club, g in top.groupby("club"):
                votes = Counter(int(ref24_club[p]) for p in g.pid if p in ref24_club.index and pd.notna(ref24_club[p]))
                if votes:
                    tid, n = votes.most_common(1)[0]
                    rows.append({"club": club, "team_id": tid, "our name": team_names.get(tid, "?"),
                                 "share": n / len(g), "same name": norm(club) == norm(team_names.get(tid, ""))})
                else:
                    rows.append({"club": club, "team_id": None, "our name": "", "share": 0.0, "same name": False})
            cm = pd.DataFrame(rows)
            if label == "FC 25":
                ea_club_alias.update({r.club: int(r.team_id) for r in cm[cm.share >= 0.4].itertuples()})
            else:
                aliased = cm.club.isin(ea_club_alias)
                w(f"Clubs through the FC 25 name mapping (same EA club names): {int(aliased.sum())} of {len(cm)}.")
                cm = cm[~aliased]
            strong = cm[cm.share >= 0.4]
            w(f"Clubs have no id here. Mapping by majority vote (the FC 24 club of most of the club's players): "
              f"{len(strong)} of {len(cm)} {'top-5 clubs' if label == 'FC 25' else 'remaining clubs'} map with "
              f"≥ 40% of their squad; "
              f"{int(strong['same name'].sum())} of those also have exactly the same name as in our data.")
            diff = strong[~strong["same name"]]
            if len(diff):
                w("Name differences among the mapped clubs (EA name → our name): "
                  + "; ".join(f"{r.club} → {r['our name']}" for _, r in diff.head(25).iterrows()) + ".")
            weak = cm[cm.share < 0.4]
            if label != "FC 25" and len(weak):
                # One season apart: vote against the FC 26 team ids instead (FC 26 covers all leagues)
                fc26_frame = load_fc26()[1]
                names26 = dict(zip(fc26_frame.club_id, fc26_frame.club))
                rows26 = []
                for club in weak.club:
                    g = top[top.club == club]
                    votes = Counter(fc26_club_by_pid[p] for p in g.pid if p in fc26_club_by_pid)
                    tid, n = votes.most_common(1)[0] if votes else (None, 0)
                    rows26.append((club, tid, names26.get(tid, "?"), n / len(g)))
                placed = [r for r in rows26 if r[3] >= 0.4]
                w(f"The remaining {len(rows26)} clubs (new to the top 5 after FC 25) by majority vote against FC 26 team "
                  f"ids: {len(placed)} map with ≥ 40% of their squad, e.g. "
                  + "; ".join(f"{c} → {n} ({pct(sh)})" for c, _, n, sh in placed[:8]) + ".")
                weak = weak[~weak.club.isin([r[0] for r in placed])]
            if len(weak):
                w("Weak or no majority (needs a manual alias): "
                  + "; ".join(f"{r.club} ({pct(r.share)})" for _, r in weak.iterrows()) + ".")
        w("")
        summary_rows.append({"version": label, "top-5 clubs": top.club.nunique(), "players": len(top),
                             "best_xi ok": ok, "failed": failed, "adjacent": adjacent,
                             "ids known": pct(in_ref.mean())})

    w("Summary of the newer sources:")
    w("")
    w(md_table(pd.DataFrame(summary_rows)))
    w("")

    # ================================================================== B. Older games (Futhead via kafagy)
    w("## B. Older games: Futhead scrape (kafagy/fifa-FUT-Data)")
    w("")
    w("Repository cloned to `data/raw/kafagy-fut/` (gitignored), MIT licence. The CSVs were produced by `futhead.py`")
    w("(Futhead list pages for gold, silver and bronze). Git history of the data files:")
    w("")
    w("- 2018-04-14 \"Adding player data for all fifa versions\", 2018-08-13 fix for \"Only first 10k players taken\",")
    w("  2018-08-14 \"Adding the full FUTHEAD data for fifa 10-18\", 2018-09-18 FIFA 19, 2019-11-25 FIFA 20.")
    w("")
    rows = []
    for v in range(10, 21):
        d = futhead(v)
        rows.append({
            "file": f"FIFA{v}.csv", "rows": len(d), "gold": int((d.TIER == "Gold").sum()),
            "silver": int((d.TIER == "Silver").sum()), "bronze": int((d.TIER == "Bronze").sum()),
            "exact duplicates": int(d.duplicated().sum()), "LOADDATE": ", ".join(sorted(d.LOADDATE.str[:10].unique())),
            "rating range": f"{d.RATING.min()}–{d.RATING.max()}", "positions": d.POSITION.nunique(),
            "GK cards": int((d.POSITION == "GK").sum()),
        })
    w(md_table(pd.DataFrame(rows)))
    w("")
    sample = futhead(14).head(3)
    w("Columns: `NAME, CLUB, LEAGUE, POSITION, TIER, RATING, PACE, SHOOTING, PASSING, DRIBBLING, DEFENDING, PHYSICAL, "
      "LOADDATE`. Example rows (FIFA 14):")
    w("")
    w(md_table(sample))
    w("")
    w("**There is not a single goalkeeper card in any file** (column `GK cards`): the scraped list pages had no GKs.")
    w("No men/women split is needed (men only). No nationality, no player id, no age, one position per card,")
    w("and no card-type column: base and special cards are mixed (e.g. FIFA 14 has a whole `World Cup` league).")
    w("")

    # ---- Rule validation on FutBin FIFA 19 (has a card-type column)
    w("### B1. Testing the base-card rule where the card type is known (FutBin FIFA 19)")
    w("")
    fb = pd.read_csv(KAFAGY / "FutBinCards19.csv")
    fb_top = fb[fb.League.isin(FUTBIN19_LEAGUES)].rename(columns={
        "Name": "NAME", "Club": "CLUB", "Rating": "RATING", "Pace": "PACE", "Shooting": "SHOOTING",
        "Passing": "PASSING", "Dribbling": "DRIBBLING", "Defending": "DEFENDING", "Phyiscality": "PHYSICAL"})
    picked = base_cards(fb_top.drop(columns=["ID", "Price", "Popularity", "PlayerPic"]))
    # The picked rows keep their own card type, so precision is read from it directly
    n_normal = int((fb_top.drop_duplicates().Revision == "Normal").sum())
    rule1 = picked
    rule2 = picked[~picked.special_only_club]
    for label, sel in [("lowest card per (name, club)", rule1), ("+ drop clubs where the name only has higher cards", rule2)]:
        hits = int((sel.Revision == "Normal").sum())
        w(f"- Rule \"{label}\": {len(sel):,} cards picked; {pct(hits / len(sel))} are `Normal` (base) cards "
          f"(precision); {pct(hits / n_normal)} of the {n_normal:,} `Normal` cards in the top 5 are picked (recall).")
    wrong = rule2[rule2.Revision != "Normal"]
    w(f"  Remaining non-base picks by card type: {dict(Counter(wrong.Revision.fillna('?')).most_common(8))}.")
    w("")

    # ---- Validation against our SoFIFA launch data for FIFA 15-19
    w("### B2. Futhead base cards vs our SoFIFA launch data (FIFA 15–19, same players)")
    w("")
    w("Base cards (rule 2) of the top-5 leagues are matched to our SoFIFA rows of the same version by name")
    w("(full name, short name, or first + last name; only unique matches count). Then rating, the six stats and")
    w("the primary position are compared.")
    w("")
    rows = []
    for v in range(15, 20):
        fh = futhead(v)
        b = base_cards(fh[fh.league.notna()])
        b = b[~b.special_only_club]
        refv = ref[ref.fifa_version == v]
        idx = build_name_index(refv)
        b["pid"] = [match_name(n, idx) for n in b.NAME]
        m = b[b.pid.notna()].merge(refv.drop_duplicates("player_id"), left_on="pid", right_on="player_id", how="left")
        same_rating = (m.RATING == m.overall).mean()
        within1 = ((m.RATING - m.overall).abs() <= 1).mean()
        outfield = m[m.POSITION != "GK"]
        l1 = abs(outfield[["PACE", "SHOOTING", "PASSING", "DRIBBLING", "DEFENDING", "PHYSICAL"]].values
                 - outfield[FACE].values).sum(axis=1)
        diff = m.RATING - m.overall
        pos_equal = (m.POSITION == m.player_positions.str.split(",").str[0].str.strip()).mean()
        rows.append({
            "version": f"FIFA {v}", "base cards (top 5)": len(b), "matched by name": pct(len(m) / len(b)),
            "same rating": pct(same_rating), "rating ±1": pct(within1),
            "rule lower / higher": f"{pct((diff < 0).mean())} / {pct((diff > 0).mean())}",
            "6 stats within 6 pts total": pct((l1 <= 6).mean()), "6 stats off by > 20": pct((l1 > 20).mean()),
            "same primary position": pct(pos_equal),
        })
    w(md_table(pd.DataFrame(rows)))
    w("")

    # ---- FIFA 10-14 per version
    w("### B3. FIFA 10–14 per version")
    w("")
    ref15 = ref[ref.fifa_version == 15]
    idx15 = build_name_index(ref15)
    idx_all = build_name_index(ref)
    per_version = []
    for v in range(10, 15):
        print(f"FIFA {v}…")
        fh = futhead(v)
        top = fh[fh.league.notna()]
        b = base_cards(top)
        moved = b[b.special_only_club]
        b = b[~b.special_only_club].copy()
        multi_club = b.groupby("NAME").CLUB.nunique()
        w(f"#### FIFA {v}")
        w("")
        w(f"Top-5 league names: {', '.join(f'`{k}`' for k in FUTHEAD_LEAGUES[v] if k in set(fh.LEAGUE))}. "
          f"Cards in the top 5: {len(top):,} → base cards after the rule: {len(b):,} "
          f"(dropped {len(top.drop_duplicates()) - len(b) - len(moved):,} higher cards at the same club, "
          f"{len(moved):,} special-only club groups). Names still at 2+ clubs: {int((multi_club > 1).sum())} "
          f"(same base rating at each club: a transfer or loan during the season; the launch club cannot be told apart).")
        w("")
        b["is_gk"] = b.POSITION == "GK"
        b["club"] = b.CLUB
        w(md_table(club_table(b)))
        w("")
        squads = {
            f"{lg}/{club}": [Player(id=i, overall=int(r.RATING), positions=(r.POSITION,), ea_pos=None)
                             for i, r in enumerate(g.itertuples(index=False))]
            for (lg, club), g in b.groupby(["league", "CLUB"])
        }
        ok, failed, adjacent, notes = run_best_xi(squads)
        w(f"`best_xi.py` with the single card position: **{ok} ok, {failed} failed**, {adjacent} `adjacent` fits."
          + ("" if not notes else " Failures: " + "; ".join(notes[:4]) + ("; …" if len(notes) > 4 else "") + "."))
        # The same run with a placeholder GK shows whether the outfield part would be complete
        with_gk = {k: sq + [Player(id=-1, overall=1, positions=("GK",), ea_pos=None)] for k, sq in squads.items()}
        ok_o, failed_o, adjacent_o, notes_o = run_best_xi(with_gk)
        w(f"With a placeholder GK added (outfield only): **{ok_o} ok, {failed_o} failed**, {adjacent_o} `adjacent` fits."
          + ("" if not notes_o else " Failures: " + "; ".join(notes_o[:6]) + ("; …" if len(notes_o) > 6 else "") + "."))
        w("")
        b["pid15"] = [match_name(n, idx15) for n in b.NAME]
        b["pid_any"] = [match_name(n, idx_all) for n in b.NAME]
        nat = b.pid_any.map(ref_by_id_latest.nationality_name)
        w(f"Name match to FIFA 15 (ids): {pct(b.pid15.notna().mean())}; to any of FIFA 15–FC 24 (nationality fill): "
          f"{pct(nat.notna().mean())} of base cards.")
        w("")
        rows = []
        for pattern, expected, conf in SPOT_CHECKS[v]:
            hit = b[b.NAME.str.contains(pattern, regex=True, na=False)].sort_values("RATING", ascending=False).head(1)
            got = int(hit.RATING.iloc[0]) if len(hit) else None
            rows.append({"player": hit.NAME.iloc[0] if len(hit) else pattern,
                         "club": hit.CLUB.iloc[0] if len(hit) else "", "base rating (rule)": got or "not found",
                         "expected": expected, "confidence": conf,
                         "match": "" if got is None else ("✓" if got == expected else "✗")})
        w(md_table(pd.DataFrame(rows)))
        w("")
        per_version.append({"version": f"FIFA {v}", "clubs": b.CLUB.nunique(), "base cards": len(b),
                            "best_xi ok": ok, "ok with placeholder GK": ok_o, "adjacent (placeholder GK)": adjacent_o,
                            "FIFA 15 match": pct(b.pid15.notna().mean()), "nationality": pct(nat.notna().mean())})
    w("Summary FIFA 10–14:")
    w("")
    w(md_table(pd.DataFrame(per_version)))
    w("")

    # ---- FIFA 09
    w("## C. FIFA 09")
    w("")
    w("None of the sources contain FIFA 09 Ultimate Team: the Futhead files start at `FIFA10.csv`, and the three")
    w("Kaggle sets are FC 25, FC 26 and FC 27 only.")
    w("")

    # ---------------------------------------------------------------- Write report
    manual = f"{MANUAL_MARKER}\n\n## Findings, verdict and recommendation\n\n(To be written.)\n"
    if REPORT.exists():
        existing = REPORT.read_text(encoding="utf-8")
        if MANUAL_MARKER in existing:
            manual = existing[existing.index(MANUAL_MARKER):]
    REPORT.write_text("\n".join(out) + "\n" + manual, encoding="utf-8", newline="\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
