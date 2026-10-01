"""Build the static app data from the raw Kaggle CSVs.

Writes:
    app/public/data/versions.json
    app/public/data/<version>/teams.json

Run from the repository root:
    pipeline/.venv/Scripts/python pipeline/build.py      (Windows)
    pipeline/.venv/bin/python pipeline/build.py          (macOS / Linux)
"""

import json
import sys
from pathlib import Path

import pandas as pd

from best_xi import NON_XI_EA_POSITIONS, SLOTS, Player, best_xi
from nations import nation_code

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "FIFA 15-24"
PLAYERS_CSV = RAW_DIR / "male_players.csv"
TEAMS_CSV = RAW_DIR / "male_teams.csv"
OUT_DIR = ROOT / "app" / "public" / "data"

# Top-5 leagues by version-accurate league_id (D17), in display order, with fixed display names
LEAGUES: list[tuple[int, str]] = [
    (13, "Premier League"),
    (53, "La Liga"),
    (31, "Serie A"),
    (19, "Bundesliga"),
    (16, "Ligue 1"),
]

# Teams excluded per version (D13): team_id -> name, for readability
EXCLUDED_TEAMS: dict[int, dict[int, str]] = {
    21: {52: "Roma", 110741: "Spezia"},
}

FACE_STATS = {"pac": "pace", "sho": "shooting", "pas": "passing", "dri": "dribbling", "def": "defending", "phy": "physic"}
GK_STATS = {
    "div": "goalkeeping_diving", "han": "goalkeeping_handling", "kic": "goalkeeping_kicking",
    "ref": "goalkeeping_reflexes", "spd": "goalkeeping_speed", "pos": "goalkeeping_positioning",
}

PLAYER_COLS = [
    "player_id", "fifa_version", "short_name", "long_name", "player_positions", "overall", "age",
    "club_team_id", "club_position", "nationality_name", *FACE_STATS.values(), *GK_STATS.values(),
]
TEAM_COLS = ["team_id", "fifa_version", "team_name", "league_id", "overall", "update_as_of"]

# Position groups for the D-M-A string of EA's starting XI (same as stage 01)
DEFENDERS = {"LWB", "LB", "LCB", "CB", "RCB", "RB", "RWB"}
MIDFIELDERS = {"LDM", "CDM", "RDM", "LM", "LCM", "CM", "RCM", "RM", "LAM", "CAM", "RAM"}
ATTACKERS = {"LW", "LF", "CF", "RF", "RW", "LS", "ST", "RS"}


def version_label(version: int) -> str:
    return "EA SPORTS FC 24" if version == 24 else f"FIFA {version}"


def parse_positions(value: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in str(value).split(",") if p.strip())


def ea_formation(ea_positions: list[str]) -> str:
    d = sum(p in DEFENDERS for p in ea_positions)
    m = sum(p in MIDFIELDERS for p in ea_positions)
    a = sum(p in ATTACKERS for p in ea_positions)
    return f"{d}-{m}-{a}"


def as_int(value, what: str) -> int:
    if pd.isna(value):
        raise ValueError(f"Missing value: {what}")
    return int(value)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    players = pd.read_csv(PLAYERS_CSV, usecols=PLAYER_COLS, low_memory=False)
    teams = pd.read_csv(TEAMS_CSV, usecols=TEAM_COLS, low_memory=False)
    players["fifa_version"] = players["fifa_version"].astype(int)
    teams["fifa_version"] = teams["fifa_version"].astype(int)
    players = players[players.club_team_id.notna()].copy()
    players["club_team_id"] = players["club_team_id"].astype(int)
    teams = teams[teams.league_id.isin([lid for lid, _ in LEAGUES])].copy()
    teams["league_id"] = teams["league_id"].astype(int)
    excluded = {(v, tid) for v, ids in EXCLUDED_TEAMS.items() for tid in ids}
    teams = teams[[(v, t) not in excluded for v, t in zip(teams.fifa_version, teams.team_id)]]
    return players, teams


def player_json(slot: str, fit: str, row) -> dict:
    out = {
        "slot": slot,
        "id": as_int(row.player_id, "player_id"),
        "name": row.short_name,
        "fullName": row.long_name,
        "nation": row.nationality_name,
        # Fails loudly if the nation has no flag code (D39)
        "nationCode": nation_code(row.nationality_name),
        "age": as_int(row.age, f"age of {row.short_name}"),
        "positions": list(parse_positions(row.player_positions)),
        "ovr": as_int(row.overall, f"overall of {row.short_name}"),
        "eaPos": row.club_position,
        "fit": fit,
    }
    if slot == "GK":
        out["gk"] = {k: as_int(getattr(row, c), f"{c} of {row.short_name}") for k, c in GK_STATS.items()}
    else:
        out["stats"] = {k: as_int(getattr(row, c), f"{c} of {row.short_name}") for k, c in FACE_STATS.items()}
    return out


def build_team(team, squad: pd.DataFrame) -> dict:
    if len(squad) < len(SLOTS):
        raise SystemExit(
            f"FIFA {team.fifa_version}: {team.team_name} (team_id {team.team_id}) has only {len(squad)} players"
        )
    rows = {int(r.player_id): r for r in squad.itertuples(index=False)}
    candidates = [
        Player(
            id=pid,
            overall=int(r.overall),
            positions=parse_positions(r.player_positions),
            ea_pos=None if pd.isna(r.club_position) else r.club_position,
        )
        for pid, r in rows.items()
    ]
    picks = best_xi(candidates)
    ea_xi = [p for p in squad.club_position.dropna() if p not in NON_XI_EA_POSITIONS]
    return {
        "id": int(team.team_id),
        "name": team.team_name,
        "leagueId": int(team.league_id),
        "ovr": as_int(team.overall, f"overall of {team.team_name}"),
        "eaFormation": ea_formation(ea_xi),
        "xi": [player_json(p.slot, p.fit, rows[p.player.id]) for p in picks],
    }


def xi_average(team_json: dict) -> float:
    """Team strength for random matchups (D45): mean `ovr` of the Best XI, 2 decimals."""
    xi = team_json["xi"]
    return round(sum(p["ovr"] for p in xi) / len(xi), 2)


def write_json(path: Path, data) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path.stat().st_size


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    players, teams = load()
    league_order = {lid: i for i, (lid, _) in enumerate(LEAGUES)}
    squads = dict(tuple(players.groupby(["fifa_version", "club_team_id"])))

    versions_json = []
    # One entry per team across all versions, for the random matchup mode
    index_json = []
    for version in sorted(teams.fifa_version.unique()):
        tv = teams[teams.fifa_version == version].copy()
        tv["league_rank"] = tv.league_id.map(league_order)
        tv = tv.sort_values(["league_rank", "overall", "team_name"], ascending=[True, False, True])
        out_teams = []
        for team in tv.itertuples(index=False):
            squad = squads.get((version, int(team.team_id)), players.iloc[0:0])
            out_teams.append(build_team(team, squad))
        snapshot = sorted(tv.update_as_of.unique())
        if len(snapshot) != 1:
            raise SystemExit(f"FIFA {version}: expected one snapshot date, got {snapshot}")
        size = write_json(OUT_DIR / str(version) / "teams.json", {"version": int(version), "teams": out_teams})
        index_json.extend(
            {"v": int(version), "id": t["id"], "name": t["name"], "leagueId": t["leagueId"], "xiAvg": xi_average(t)}
            for t in out_teams
        )
        versions_json.append({
            "id": int(version),
            "label": version_label(int(version)),
            "snapshotDate": snapshot[0],
            "leagues": [{"id": lid, "name": name} for lid, name in LEAGUES],
            "teamCount": len(out_teams),
        })
        print(f"{version_label(int(version)):>16}: {len(out_teams)} teams, {size / 1024:.1f} KB")

    write_json(OUT_DIR / "versions.json", versions_json)
    index_size = write_json(OUT_DIR / "index.json", index_json)
    print(f"Wrote {len(versions_json)} versions and index.json ({len(index_json)} teams, {index_size / 1024:.1f} KB) "
          f"to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
