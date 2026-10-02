"""Per-source loaders. Each returns the same common frames, so build.py does not care where data came from.

Common player frame (SoFIFA column names, one row per player of a top-5 club in that version):
    player_id, short_name, long_name, nationality_name, age, club_team_id, player_positions ("CM, CAM"),
    overall, club_position (EA team sheet code or None), pace, shooting, passing, dribbling, defending, physic,
    goalkeeping_diving, goalkeeping_handling, goalkeeping_kicking, goalkeeping_reflexes, goalkeeping_speed,
    goalkeeping_positioning
Common team frame: team_id, team_name, league_id, overall (NaN when the source has no team rating).

VERSIONS (bottom of this file) says which loader serves which version.
"""

import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Callable

import pandas as pd

from clubs_ea import EA_CLUBS
from name_overrides import NAME_OVERRIDES

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# Top-5 leagues by version-accurate league_id (D17), in display order, with fixed display names
LEAGUES: list[tuple[int, str]] = [
    (13, "Premier League"),
    (53, "La Liga"),
    (31, "Serie A"),
    (19, "Bundesliga"),
    (16, "Ligue 1"),
]
LEAGUE_IDS = [lid for lid, _ in LEAGUES]

# League names of the top 5 in EA's ratings data (FC 25, FC 27) -> our league ids
EA_LEAGUES: dict[str, int] = {
    "Premier League": 13,
    "LALIGA EA SPORTS": 53,
    "Serie A Enilive": 31,
    "Bundesliga": 19,
    "Ligue 1 McDonald's": 16,
}

# Teams excluded per version (D13): team_id -> name, for readability
EXCLUDED_TEAMS: dict[int, dict[int, str]] = {
    21: {52: "Roma", 110741: "Spezia"},
}

FACE_COLS = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
GK_COLS = [
    "goalkeeping_diving", "goalkeeping_handling", "goalkeeping_kicking",
    "goalkeeping_reflexes", "goalkeeping_speed", "goalkeeping_positioning",
]
PLAYER_COLUMNS = [
    "player_id", "short_name", "long_name", "nationality_name", "age", "club_team_id", "player_positions",
    "overall", "club_position", *FACE_COLS, *GK_COLS,
]

# In EA's ratings data a goalkeeper's six card slots hold the GK stats in card order (verified in stage 10:
# PAC/SHO/PAS/DRI/PHY equal the file's own GK diving/handling/kicking/reflexes/positioning columns for 100% of
# GKs, and the DEF slot correlates 0.96 with SoFIFA's goalkeeping_speed for the same keepers).
EA_GK_SLOTS = {
    "goalkeeping_diving": 0,  # PAC slot
    "goalkeeping_handling": 1,  # SHO slot
    "goalkeeping_kicking": 2,  # PAS slot
    "goalkeeping_reflexes": 3,  # DRI slot
    "goalkeeping_speed": 4,  # DEF slot
    "goalkeeping_positioning": 5,  # PHY slot
}


@dataclass(frozen=True)
class VersionData:
    players: pd.DataFrame
    teams: pd.DataFrame
    snapshot_date: str


@dataclass(frozen=True)
class VersionSource:
    loader: Callable[[int], VersionData]
    description: str


# ---------------------------------------------------------------------- names (EA sources)
_JR = re.compile(r"\bJr\.?$")


def ea_short_name(display: str, first: str | None = None, last: str | None = None,
                  known_short: str | None = None) -> str:
    """Short display name for EA data, in the style of SoFIFA's short_name (D16).

    - EA's common name (`known_short`) is used when there is one.
    - A single-word name ("Rodri") or a name ending in "Jr." ("Vini Jr.") is kept.
    - Otherwise "F. Lastname": the first name's initial plus the last name ("Kylian Mbappé" -> "K. Mbappé").
    """
    if known_short and known_short.strip():
        return known_short.strip()
    display = display.strip()
    if " " not in display or _JR.search(display):
        return display
    if first and last:
        return f"{first.strip()[0]}. {last.strip()}"
    first_word, rest = display.split(" ", 1)
    return f"{first_word[0]}. {rest}"


def apply_name_overrides(version: int, players: pd.DataFrame) -> pd.DataFrame:
    """Replace rule-made short names with the manual fixes for this version (D59); fail on a stale entry."""
    wanted = {pid: name for (v, pid), name in NAME_OVERRIDES.items() if v == version}
    missing = sorted(set(wanted) - set(players.player_id))
    if missing:
        raise SystemExit(f"Version {version}: name overrides for unknown player ids {missing} (pipeline/name_overrides.py)")
    players = players.copy()
    players["short_name"] = [wanted.get(p, n) for p, n in zip(players.player_id, players.short_name)]
    return players


def _ea_frame(raw: pd.DataFrame, *, pid, short_name, long_name, nation, age, club, league, positions, overall,
              card_slots: list[str], is_gk) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Common frames from EA-format columns. `card_slots` are the six card columns in PAC..PHY order."""
    league_id = league.map(EA_LEAGUES)
    top = league_id.notna()
    clubs = club[top]
    unmapped = sorted(set(clubs) - set(EA_CLUBS))
    if unmapped:
        raise SystemExit(f"Top-5 clubs missing from pipeline/clubs_ea.py: {', '.join(unmapped)}")
    players = pd.DataFrame({
        "player_id": pid[top].astype(int),
        "short_name": short_name[top],
        "long_name": long_name[top],
        "nationality_name": nation[top],
        "age": age[top],
        "club_team_id": clubs.map(lambda c: EA_CLUBS[c][0]).astype(int),
        "player_positions": positions[top],
        "overall": overall[top],
        "club_position": None,
    })
    gk = is_gk[top]
    for i, col in enumerate(FACE_COLS):
        players[col] = raw.loc[top, card_slots[i]].where(~gk)
    for col, slot in EA_GK_SLOTS.items():
        players[col] = raw.loc[top, card_slots[slot]].where(gk)
    teams = (
        pd.DataFrame({"team_id": players.club_team_id, "league_id": league_id[top].astype(int)})
        .drop_duplicates("team_id")
        .assign(team_name=lambda t: t.team_id.map({tid: name for tid, name in EA_CLUBS.values()}), overall=float("nan"))
    )
    return players.reset_index(drop=True), teams.reset_index(drop=True)


# ---------------------------------------------------------------------- SoFIFA FIFA 15 - FC 24 (Kaggle, stefanoleone992)
SOFIFA_15_24 = RAW / "FIFA 15-24"


@lru_cache(maxsize=1)
def _sofifa_15_24() -> tuple[pd.DataFrame, pd.DataFrame]:
    players = pd.read_csv(
        SOFIFA_15_24 / "male_players.csv",
        usecols=["fifa_version", *[c for c in PLAYER_COLUMNS]],
        low_memory=False,
    )
    teams = pd.read_csv(
        SOFIFA_15_24 / "male_teams.csv",
        usecols=["team_id", "fifa_version", "team_name", "league_id", "overall", "update_as_of"],
        low_memory=False,
    )
    players["fifa_version"] = players["fifa_version"].astype(int)
    teams["fifa_version"] = teams["fifa_version"].astype(int)
    players = players[players.club_team_id.notna()].copy()
    players["club_team_id"] = players["club_team_id"].astype(int)
    teams = teams[teams.league_id.isin(LEAGUE_IDS)].copy()
    teams["league_id"] = teams["league_id"].astype(int)
    return players, teams


def known_team_names() -> dict[int, str]:
    """Display name of every top-5 team in FIFA 15 - FC 24: its name in the latest version it appears in."""
    _, teams = _sofifa_15_24()
    latest = teams.sort_values("fifa_version").drop_duplicates("team_id", keep="last")
    return dict(zip(latest.team_id.astype(int), latest.team_name))


def load_sofifa_15_24(version: int) -> VersionData:
    players, teams = _sofifa_15_24()
    tv = teams[teams.fifa_version == version]
    excluded = set(EXCLUDED_TEAMS.get(version, {}))
    tv = tv[~tv.team_id.isin(excluded)]
    snapshot = sorted(tv.update_as_of.unique())
    if len(snapshot) != 1:
        raise SystemExit(f"Version {version}: expected one snapshot date, got {snapshot}")
    pv = players[(players.fifa_version == version) & players.club_team_id.isin(set(tv.team_id))]
    return VersionData(
        players=pv[PLAYER_COLUMNS].reset_index(drop=True),
        teams=tv[["team_id", "team_name", "league_id", "overall"]].reset_index(drop=True),
        snapshot_date=snapshot[0],
    )


# ---------------------------------------------------------------------- SoFIFA FC 26 (Kaggle, rovnez)
FC26_CSV = RAW / "FC 26" / "FC26_20250921.csv"


def load_sofifa_fc26(version: int) -> VersionData:
    raw = pd.read_csv(FC26_CSV, low_memory=False)
    top = raw[raw.league_id.isin(LEAGUE_IDS) & (raw.league_level == 1) & raw.club_team_id.notna()].copy()
    top["club_team_id"] = top.club_team_id.astype(int)
    top["league_id"] = top.league_id.astype(int)
    snapshot = sorted(str(d) for d in raw.fifa_update_date.unique())
    if len(snapshot) != 1:
        raise SystemExit(f"Version {version}: expected one snapshot date, got {snapshot}")
    teams = (
        top.drop_duplicates("club_team_id")
        .rename(columns={"club_team_id": "team_id", "club_name": "team_name"})[["team_id", "team_name", "league_id"]]
        .assign(overall=float("nan"))
    )
    # Keep the club names we already show (this export renamed e.g. "Milan" to "AC Milan"), as for EA names (D54)
    known = known_team_names()
    teams["team_name"] = [known.get(int(t), n) for t, n in zip(teams.team_id, teams.team_name)]
    return VersionData(players=top[PLAYER_COLUMNS].reset_index(drop=True), teams=teams.reset_index(drop=True),
                       snapshot_date=snapshot[0])


# ---------------------------------------------------------------------- EA ratings: FC 25 (Kaggle, nyagami)
FC25_CSV = RAW / "FC 25" / "male_players.csv"
# The file has no date column; the Kaggle archive entries are dated 2024-09-26 (stage 09)
FC25_SNAPSHOT = "2024-09-26"


def _positions(primary: pd.Series, alternates: pd.Series, sep: str) -> pd.Series:
    return pd.Series(
        [", ".join([p] + ([a.strip() for a in alt.split(sep) if a.strip()] if isinstance(alt, str) else []))
         for p, alt in zip(primary, alternates)],
        index=primary.index,
    )


def load_ea_fc25(version: int) -> VersionData:
    raw = pd.read_csv(FC25_CSV)
    pid = raw.url.str.extract(r"/(\d+)$")[0].astype(int)
    # EA's common names from the FC 27 data count as known short forms ("Lamine Yamal", "Bruno Fernandes")
    common = _fc27_common_names()
    short = pd.Series([ea_short_name(n, known_short=common.get(p) if common.get(p) == n else None)
                       for n, p in zip(raw.Name, pid)], index=raw.index)
    players, teams = _ea_frame(
        raw, pid=pid, short_name=short, long_name=raw.Name, nation=raw.Nation, age=raw.Age, club=raw.Team,
        league=raw.League, positions=_positions(raw.Position, raw["Alternative positions"], ","), overall=raw.OVR,
        card_slots=["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"], is_gk=raw.Position == "GK",
    )
    return VersionData(players=apply_name_overrides(version, players), teams=teams, snapshot_date=FC25_SNAPSHOT)


# ---------------------------------------------------------------------- EA ratings: FC 27 (Kaggle, mikedpad)
FC27_CSV = RAW / "FC 27" / "players.csv"


@lru_cache(maxsize=1)
def _fc27_raw() -> pd.DataFrame:
    raw = pd.read_csv(FC27_CSV)
    return raw[raw.gender == "Men's Football"].reset_index(drop=True)


def _fc27_common_names() -> dict[int, str]:
    raw = _fc27_raw()
    return {int(p): c for p, c in zip(raw.player_id, raw.common_name) if isinstance(c, str) and c.strip()}


def age_on(birthdate: str, on: str) -> int:
    b, d = date.fromisoformat(birthdate), date.fromisoformat(on)
    return d.year - b.year - ((d.month, d.day) < (b.month, b.day))


def load_ea_fc27(version: int) -> VersionData:
    raw = _fc27_raw()
    snapshot = sorted(str(d) for d in raw.snapshot_date.unique())
    if len(snapshot) != 1:
        raise SystemExit(f"Version {version}: expected one snapshot date, got {snapshot}")
    first = raw.first_name.fillna("")
    last = raw.last_name.fillna("")
    full = (first + " " + last).str.strip()
    short = pd.Series([ea_short_name(n, first=f or None, last=l or None,
                                     known_short=c if isinstance(c, str) else None)
                       for n, f, l, c in zip(full, first, last, raw.common_name)], index=raw.index)
    age = pd.Series([age_on(b, snapshot[0]) if isinstance(b, str) else None for b in raw.birthdate], index=raw.index)
    players, teams = _ea_frame(
        raw, pid=raw.player_id, short_name=short, long_name=full, nation=raw.nationality, age=age, club=raw.club,
        league=raw.league, positions=_positions(raw.position, raw.alternate_positions, " "), overall=raw.overall_rating,
        card_slots=["pace", "shooting", "passing", "dribbling", "defending", "physicality"], is_gk=raw.position == "GK",
    )
    return VersionData(players=apply_name_overrides(version, players), teams=teams, snapshot_date=snapshot[0])


# ---------------------------------------------------------------------- version table
VERSIONS: dict[int, VersionSource] = {
    **{v: VersionSource(load_sofifa_15_24, "SoFIFA via Kaggle (stefanoleone992), FIFA 15 - FC 24") for v in range(15, 25)},
    25: VersionSource(load_ea_fc25, "EA ratings site via Kaggle (nyagami)"),
    26: VersionSource(load_sofifa_fc26, "SoFIFA via Kaggle (rovnez)"),
    27: VersionSource(load_ea_fc27, "EA ratings API via Kaggle (mikedpad), pre-release snapshot"),
}
