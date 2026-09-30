"""Print the data sections of docs/reports/02-pipeline.md as markdown.

Compares the generated Best XI (app/public/data/) with EA's starting XI from the raw CSV,
lists adjacent fits, output sizes and sample XIs. Run after build.py:
    pipeline/.venv/Scripts/python pipeline/report_02.py > out.md
"""

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

from best_xi import NON_XI_EA_POSITIONS
from build import OUT_DIR, PLAYERS_CSV, version_label

# (version, team_id) of the XIs printed for the eye check
SAMPLE_XIS = [(21, 241), (22, 73), (24, 243), (24, 10), (16, 11), (18, 9)]


def md_table(rows: list[dict]) -> str:
    if not rows:
        return "(none)"
    cols = list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    raw = pd.read_csv(
        PLAYERS_CSV, usecols=["player_id", "fifa_version", "short_name", "overall", "club_team_id", "club_position"],
        low_memory=False,
    )
    raw = raw[raw.club_team_id.notna() & raw.club_position.notna() & ~raw.club_position.isin(NON_XI_EA_POSITIONS)]
    raw["fifa_version"] = raw.fifa_version.astype(int)
    raw["club_team_id"] = raw.club_team_id.astype(int)
    ea_xis = {k: g for k, g in raw.groupby(["fifa_version", "club_team_id"])}

    versions = json.loads((OUT_DIR / "versions.json").read_text(encoding="utf-8"))
    data = {v["id"]: json.loads((OUT_DIR / str(v["id"]) / "teams.json").read_text(encoding="utf-8")) for v in versions}

    # Best XI vs EA XI
    per_version, changes, adjacent = [], [], []
    for v, d in data.items():
        changed_counts = []
        for t in d["teams"]:
            ea = ea_xis.get((v, t["id"]))
            ea_ids = set(ea.player_id) if ea is not None else set()
            best_ids = {p["id"] for p in t["xi"]}
            came_in = [p for p in t["xi"] if p["id"] not in ea_ids]
            went_out = ea[~ea.player_id.isin(best_ids)].sort_values("overall", ascending=False) if ea is not None else None
            changed_counts.append(len(came_in))
            # A rating gain is only comparable when EA's XI is complete
            gain = sum(p["ovr"] for p in t["xi"]) - int(ea.overall.sum()) if len(ea_ids) == 11 else None
            changes.append({
                "version": v, "team": t["name"], "changed": len(came_in), "EA XI size": len(ea_ids),
                "XI ovr gain": gain,
                "in": ", ".join(f"{p['name']} {p['ovr']} ({p['eaPos']}→{p['slot']})" for p in came_in),
                "out": ", ".join(f"{r.short_name} {r.overall} ({r.club_position})" for r in went_out.itertuples())
                if went_out is not None else "",
            })
            for p in t["xi"]:
                if p["fit"] == "adjacent":
                    adjacent.append({"version": v, "team": t["name"], "slot": p["slot"], "player": p["name"],
                                     "ovr": p["ovr"], "positions": ", ".join(p["positions"]), "eaPos": p["eaPos"]})
        n = len(changed_counts)
        per_version.append({
            "version": v, "teams": n,
            "avg changed per team": f"{sum(changed_counts) / n:.2f}",
            "teams unchanged": sum(c == 0 for c in changed_counts),
            "max changed": max(changed_counts),
        })

    print("## Best XI vs EA's starting XI\n")
    print("\"Changed\" = Best XI players who were not in EA's starting XI (SUB/RES in the data).\n")
    print(md_table(per_version))
    print()
    top = sorted(changes, key=lambda c: (-c["changed"], -(c["XI ovr gain"] or -999), c["version"], c["team"]))[:10]
    for c in top:
        if c["XI ovr gain"] is None:
            c["XI ovr gain"] = f"n/a (EA XI had {c['EA XI size']})"
    print("### 10 biggest changes\n")
    print("Ranked by number of changed players, then by total XI rating gain over EA's XI "
          "(n/a when EA's XI in the data has fewer than 11 players).\n")
    print(md_table([{k: c[k] for k in ("version", "team", "changed", "XI ovr gain", "in", "out")} for c in top]))
    print()

    print("## Adjacent fits\n")
    print(md_table(adjacent))
    print()

    print("## Output file sizes\n")
    size_rows = []
    for v in data:
        path = OUT_DIR / str(v) / "teams.json"
        blob = path.read_bytes()
        size_rows.append({"version": v, "file": f"{v}/teams.json", "raw (KB)": f"{len(blob) / 1024:.1f}",
                          "gzip (KB)": f"{len(gzip.compress(blob, 9)) / 1024:.1f}"})
    vblob = (OUT_DIR / "versions.json").read_bytes()
    size_rows.append({"version": "", "file": "versions.json", "raw (KB)": f"{len(vblob) / 1024:.1f}",
                      "gzip (KB)": f"{len(gzip.compress(vblob, 9)) / 1024:.1f}"})
    print(md_table(size_rows))
    print()

    print("## Sample XIs\n")
    for v, tid in SAMPLE_XIS:
        team = next(t for t in data[v]["teams"] if t["id"] == tid)
        print(f"### {version_label(v)} — {team['name']} (EA formation {team['eaFormation']})\n")
        print(md_table([{"slot": p["slot"], "name": p["name"], "positions": ", ".join(p["positions"]),
                         "ovr": p["ovr"], "eaPos": p["eaPos"], "fit": p["fit"]} for p in team["xi"]]))
        print()


if __name__ == "__main__":
    main()
