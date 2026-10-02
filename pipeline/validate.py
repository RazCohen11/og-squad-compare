"""Validate the generated app data. Reads only app/public/data/, exits non-zero on any failure.

Run from the repository root:
    pipeline/.venv/Scripts/python pipeline/validate.py      (Windows)
    pipeline/.venv/bin/python pipeline/validate.py          (macOS / Linux)
"""

import json
import sys
from collections import Counter
from pathlib import Path

from best_xi import ADJACENT, NATURAL, SLOTS
from nations import CODE_PATTERN

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "app" / "public" / "data"

VERSIONS = list(range(15, 28))
# Sources without an EA team sheet: eaPos and eaFormation are null there (stage 10)
NO_TEAM_SHEET = {25, 27}
LEAGUE_IDS = [13, 53, 31, 19, 16]

# Expected clubs per league (stage 01 report, after D13)
DEFAULT_COUNTS = {13: 20, 53: 20, 31: 20, 19: 18, 16: 20}
EXPECTED_COUNTS = {v: dict(DEFAULT_COUNTS) for v in VERSIONS}
EXPECTED_COUNTS[21][31] = 18  # Roma and Spezia excluded (D13)
EXPECTED_COUNTS[24][16] = 18  # Ligue 1 has had 18 clubs since 2023-24
for _v in (25, 26, 27):
    EXPECTED_COUNTS[_v][16] = 18

STATS_KEYS = {"pac", "sho", "pas", "dri", "def", "phy"}
GK_KEYS = {"div", "han", "kic", "ref", "spd", "pos"}
PLAYER_KEYS = {"slot", "id", "name", "fullName", "nation", "nationCode", "age", "positions", "ovr", "eaPos", "fit"}
NON_XI = {"SUB", "RES"}


def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    errors: list[str] = []
    err = errors.append
    summary = []
    # Expected index.json entries, rebuilt from the team files: (version, team id) -> entry
    expected_index: dict[tuple[int, int], dict] = {}

    versions = json.loads((DATA_DIR / "versions.json").read_text(encoding="utf-8"))
    if [v.get("id") for v in versions] != VERSIONS:
        err(f"versions.json ids are {[v.get('id') for v in versions]}, expected {VERSIONS}")

    for ventry in versions:
        v = ventry["id"]
        where = f"FIFA {v}"
        if [lg["id"] for lg in ventry.get("leagues", [])] != LEAGUE_IDS:
            err(f"{where}: versions.json leagues are not {LEAGUE_IDS}")
        path = DATA_DIR / str(v) / "teams.json"
        if not path.exists():
            err(f"{where}: {path.relative_to(ROOT)} missing")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != v:
            err(f"{where}: teams.json version is {data.get('version')}")
        teams = data["teams"]
        if ventry.get("teamCount") != len(teams):
            err(f"{where}: teamCount {ventry.get('teamCount')} != {len(teams)} teams")

        counts = Counter(t["leagueId"] for t in teams)
        if dict(counts) != EXPECTED_COUNTS[v]:
            err(f"{where}: teams per league {dict(counts)}, expected {EXPECTED_COUNTS[v]}")

        seen_players: dict[int, str] = {}
        team_ids = set()
        adjacent = bench = 0
        for t in teams:
            tw = f"{where} {t['name']}"
            if t["xi"]:
                expected_index[(v, t["id"])] = {
                    "v": v, "id": t["id"], "name": t["name"], "leagueId": t["leagueId"],
                    "xiAvg": round(sum(p["ovr"] for p in t["xi"]) / len(t["xi"]), 2),
                }
            if t["id"] in team_ids:
                err(f"{tw}: duplicate team id {t['id']}")
            team_ids.add(t["id"])
            formation_ok = t.get("eaFormation") is None if v in NO_TEAM_SHEET else isinstance(t.get("eaFormation"), str)
            if not is_int(t.get("ovr")) or not is_int(t.get("leagueId")) or not formation_ok:
                err(f"{tw}: bad team fields")
            xi = t["xi"]
            if len(xi) != 11:
                err(f"{tw}: {len(xi)} players")
            if [p["slot"] for p in xi] != list(SLOTS):
                err(f"{tw}: slots {[p['slot'] for p in xi]}")
            ids = [p["id"] for p in xi]
            if len(set(ids)) != len(ids):
                err(f"{tw}: duplicate player id in XI")
            for p in xi:
                pw = f"{tw} {p.get('slot')} {p.get('name')}"
                missing = PLAYER_KEYS - p.keys()
                if missing:
                    err(f"{pw}: missing keys {sorted(missing)}")
                    continue
                if not is_int(p["id"]) or not is_int(p["age"]):
                    err(f"{pw}: id/age not integers")
                if not is_int(p["ovr"]) or not 40 <= p["ovr"] <= 99:
                    err(f"{pw}: ovr {p['ovr']}")
                ea_pos_ok = p["eaPos"] is None if v in NO_TEAM_SHEET else isinstance(p["eaPos"], str)
                if not p["name"] or not p["nation"] or not ea_pos_ok:
                    err(f"{pw}: empty name/nation or bad eaPos")
                if not isinstance(p["nationCode"], str) or not CODE_PATTERN.match(p["nationCode"]):
                    err(f"{pw}: bad nationCode {p['nationCode']!r}")
                positions = set(p["positions"])
                if p["fit"] == "natural":
                    if not positions & NATURAL[p["slot"]]:
                        err(f"{pw}: natural fit but positions {p['positions']}")
                elif p["fit"] == "adjacent":
                    adjacent += 1
                    if not positions & ADJACENT[p["slot"]] or positions & NATURAL[p["slot"]]:
                        err(f"{pw}: adjacent fit but positions {p['positions']}")
                else:
                    err(f"{pw}: fit {p['fit']!r}")
                if p["slot"] == "GK":
                    stats, keys, other = p.get("gk"), GK_KEYS, "stats"
                else:
                    stats, keys, other = p.get("stats"), STATS_KEYS, "gk"
                if not isinstance(stats, dict) or set(stats) != keys or not all(is_int(x) for x in stats.values()):
                    err(f"{pw}: bad stats {stats}")
                if other in p:
                    err(f"{pw}: unexpected '{other}' block")
                if p["eaPos"] in NON_XI:
                    bench += 1
                if p["id"] in seen_players:
                    err(f"{pw}: also in {seen_players[p['id']]}")
                seen_players[p["id"]] = t["name"]

        summary.append((v, len(teams), sum(len(t["xi"]) for t in teams), adjacent, bench))

    # index.json (random matchup mode, D45) must match the team files exactly
    index_path = DATA_DIR / "index.json"
    if not index_path.exists():
        err("index.json missing")
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        seen_keys: set[tuple[int, int]] = set()
        for entry in index:
            key = (entry.get("v"), entry.get("id"))
            if key in seen_keys:
                err(f"index.json: duplicate entry {key}")
            seen_keys.add(key)
            expected = expected_index.get(key)
            if expected is None:
                err(f"index.json: unknown team {key}")
            elif entry != expected:
                err(f"index.json: {key} is {entry}, expected {expected}")
        for key in expected_index.keys() - seen_keys:
            err(f"index.json: missing team {key}")
        print(f"index.json: {len(index)} teams")

    print(f"{'version':>7} {'teams':>5} {'players':>7} {'adjacent':>8} {'from SUB/RES':>12}")
    for v, nt, npl, adj, bench in summary:
        print(f"{v:>7} {nt:>5} {npl:>7} {adj:>8} {bench:>12}")
    print(f"{'total':>7} {sum(s[1] for s in summary):>5} {sum(s[2] for s in summary):>7} "
          f"{sum(s[3] for s in summary):>8} {sum(s[4] for s in summary):>12}")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s)")
        for e in errors[:100]:
            print(f"  - {e}")
        return 1
    print("\nOK: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
