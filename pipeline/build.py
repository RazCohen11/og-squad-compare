"""Build the static app data from the raw source files.

Writes:
    app/public/data/versions.json
    app/public/data/<version>/teams.json
    app/public/data/index.json

Which source serves which version is defined in sources.VERSIONS; each loader returns the same common frames.

Run from the repository root:
    pipeline/.venv/Scripts/python pipeline/build.py      (Windows)
    pipeline/.venv/bin/python pipeline/build.py          (macOS / Linux)
"""

import json
import sys
from pathlib import Path

import pandas as pd

from best_xi import NON_XI_EA_POSITIONS, SLOTS, Player, best_xi
from nations import canonical_nation, nation_code
from sources import LEAGUES, VERSIONS

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "app" / "public" / "data"

FACE_STATS = {"pac": "pace", "sho": "shooting", "pas": "passing", "dri": "dribbling", "def": "defending", "phy": "physic"}
GK_STATS = {
    "div": "goalkeeping_diving", "han": "goalkeeping_handling", "kic": "goalkeeping_kicking",
    "ref": "goalkeeping_reflexes", "spd": "goalkeeping_speed", "pos": "goalkeeping_positioning",
}

# Position groups for the D-M-A string of EA's starting XI (same as stage 01)
DEFENDERS = {"LWB", "LB", "LCB", "CB", "RCB", "RB", "RWB"}
MIDFIELDERS = {"LDM", "CDM", "RDM", "LM", "LCM", "CM", "RCM", "RM", "LAM", "CAM", "RAM"}
ATTACKERS = {"LW", "LF", "CF", "RF", "RW", "LS", "ST", "RS"}


def version_label(version: int) -> str:
    return f"EA SPORTS FC {version}" if version >= 24 else f"FIFA {version}"


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


def player_json(slot: str, fit: str, row) -> dict:
    out = {
        "slot": slot,
        "id": as_int(row.player_id, "player_id"),
        "name": row.short_name,
        "fullName": row.long_name,
        "nation": canonical_nation(row.nationality_name),
        # Fails loudly if the nation has no flag code (D39)
        "nationCode": nation_code(row.nationality_name),
        "age": as_int(row.age, f"age of {row.short_name}"),
        "positions": list(parse_positions(row.player_positions)),
        "ovr": as_int(row.overall, f"overall of {row.short_name}"),
        # None when the source has no EA team sheet (FC 25, FC 27)
        "eaPos": None if pd.isna(row.club_position) else row.club_position,
        "fit": fit,
    }
    if slot == "GK":
        out["gk"] = {k: as_int(getattr(row, c), f"{c} of {row.short_name}") for k, c in GK_STATS.items()}
    else:
        out["stats"] = {k: as_int(getattr(row, c), f"{c} of {row.short_name}") for k, c in FACE_STATS.items()}
    return out


def xi_average(team_json: dict) -> float:
    """Team strength for random matchups (D45): mean `ovr` of the Best XI, 2 decimals."""
    xi = team_json["xi"]
    return round(sum(p["ovr"] for p in xi) / len(xi), 2)


def build_team(version: int, team, squad: pd.DataFrame) -> dict:
    if len(squad) < len(SLOTS):
        raise SystemExit(f"Version {version}: {team.team_name} (team_id {team.team_id}) has only {len(squad)} players")
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
    has_team_sheet = squad.club_position.notna().any()
    ea_xi = [p for p in squad.club_position.dropna() if p not in NON_XI_EA_POSITIONS]
    out = {
        "id": int(team.team_id),
        "name": team.team_name,
        "leagueId": int(team.league_id),
        "ovr": None,
        "eaFormation": ea_formation(ea_xi) if has_team_sheet else None,
        "xi": [player_json(p.slot, p.fit, rows[p.player.id]) for p in picks],
    }
    # Sources without a team rating (FC 25-27): the rounded Best XI average is used for sorting
    out["ovr"] = int(round(xi_average(out))) if pd.isna(team.overall) else as_int(team.overall, team.team_name)
    return out


def write_json(path: Path, data) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path.stat().st_size


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    league_order = {lid: i for i, (lid, _) in enumerate(LEAGUES)}

    versions_json = []
    # One entry per team across all versions, for the random matchup mode
    index_json = []
    for version in sorted(VERSIONS):
        data = VERSIONS[version].loader(version)
        squads = dict(tuple(data.players.groupby("club_team_id")))
        out_teams = [
            build_team(version, team, squads.get(int(team.team_id), data.players.iloc[0:0]))
            for team in data.teams.itertuples(index=False)
        ]
        # By league, then team rating (descending), then name
        out_teams.sort(key=lambda t: (league_order[t["leagueId"]], -t["ovr"], t["name"]))
        size = write_json(OUT_DIR / str(version) / "teams.json", {"version": version, "teams": out_teams})
        index_json.extend(
            {"v": version, "id": t["id"], "name": t["name"], "leagueId": t["leagueId"], "xiAvg": xi_average(t)}
            for t in out_teams
        )
        versions_json.append({
            "id": version,
            "label": version_label(version),
            "snapshotDate": data.snapshot_date,
            "leagues": [{"id": lid, "name": name} for lid, name in LEAGUES],
            "teamCount": len(out_teams),
        })
        print(f"{version_label(version):>16}: {len(out_teams)} teams, {size / 1024:.1f} KB")

    write_json(OUT_DIR / "versions.json", versions_json)
    index_size = write_json(OUT_DIR / "index.json", index_json)
    print(f"Wrote {len(versions_json)} versions and index.json ({len(index_json)} teams, {index_size / 1024:.1f} KB) "
          f"to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
