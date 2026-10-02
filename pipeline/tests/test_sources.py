import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clubs_ea import EA_CLUBS  # noqa: E402
from nations import NATION_ALIASES, NATION_CODES, canonical_nation, nation_code  # noqa: E402
from sources import (  # noqa: E402
    EA_GK_SLOTS, EA_LEAGUES, FC25_CSV, FC27_CSV, GK_COLS, VERSIONS, age_on, ea_short_name, load_ea_fc25, load_ea_fc27,
)

HAS_FC25 = FC25_CSV.exists()
HAS_FC27 = FC27_CSV.exists()


# ---------------------------------------------------------------------- version table
def test_version_table_covers_fifa15_to_fc27():
    assert sorted(VERSIONS) == list(range(15, 28))


# ---------------------------------------------------------------------- club alias table (D54)
def test_alias_table_entries_are_well_formed():
    assert len(EA_CLUBS) >= 96
    for name, (team_id, display) in EA_CLUBS.items():
        assert name.strip() == name and name
        assert isinstance(team_id, int) and team_id > 0
        assert display.strip()


def test_alias_table_maps_unlicensed_ea_names_to_real_clubs():
    assert EA_CLUBS["Lombardia FC"] == (44, "Inter")
    assert EA_CLUBS["Milano FC"] == (47, "Milan")
    assert EA_CLUBS["Bergamo Calcio"] == (39, "Atalanta")
    assert EA_CLUBS["Latium"] == (46, "Lazio")
    assert EA_CLUBS["Paris SG"] == (73, "Paris Saint Germain")


def test_one_team_id_has_one_display_name():
    names: dict[int, set[str]] = {}
    for team_id, display in EA_CLUBS.values():
        names.setdefault(team_id, set()).add(display)
    assert {t: n for t, n in names.items() if len(n) > 1} == {}


@pytest.mark.skipif(not HAS_FC25, reason="FC 25 raw data not present")
def test_every_fc25_top5_club_is_mapped():
    import pandas as pd

    raw = pd.read_csv(FC25_CSV, usecols=["Team", "League"])
    clubs = set(raw[raw.League.isin(EA_LEAGUES)].Team)
    assert len(clubs) == 96
    assert clubs - set(EA_CLUBS) == set()


@pytest.mark.skipif(not HAS_FC27, reason="FC 27 raw data not present")
def test_every_fc27_top5_club_is_mapped():
    import pandas as pd

    raw = pd.read_csv(FC27_CSV, usecols=["club", "league", "gender"])
    clubs = set(raw[(raw.gender == "Men's Football") & raw.league.isin(EA_LEAGUES)].club)
    assert len(clubs) == 96
    assert clubs - set(EA_CLUBS) == set()


# ---------------------------------------------------------------------- name rule
@pytest.mark.parametrize(
    ("display", "first", "last", "common", "expected"),
    [
        ("Kylian Mbappé", None, None, None, "K. Mbappé"),
        ("Rodri", None, None, None, "Rodri"),
        ("Vini Jr.", None, None, None, "Vini Jr."),
        ("Neymar Jr", None, None, None, "Neymar Jr"),
        ("Marc-André ter Stegen", None, None, None, "M. ter Stegen"),
        ("Virgil van Dijk", None, None, None, "V. van Dijk"),
        ("Lamine Yamal", None, None, "Lamine Yamal", "Lamine Yamal"),
        ("Rodrigo Hernández Cascante", "Rodrigo", "Hernández Cascante", "Rodri", "Rodri"),
        ("Kylian Mbappé", "Kylian", "Mbappé", None, "K. Mbappé"),
        ("Erling Haaland", "Erling", "Haaland", "  ", "E. Haaland"),
    ],
)
def test_ea_short_name(display, first, last, common, expected):
    assert ea_short_name(display, first=first, last=last, known_short=common) == expected


# ---------------------------------------------------------------------- GK card slots
def test_gk_slot_mapping_follows_card_order():
    # PAC, SHO, PAS, DRI, DEF, PHY slots hold DIV, HAN, KIC, REF, SPD, POS for a goalkeeper
    assert [EA_GK_SLOTS[c] for c in GK_COLS] == [0, 1, 2, 3, 4, 5]
    assert EA_GK_SLOTS["goalkeeping_speed"] == 4


@pytest.mark.skipif(not HAS_FC25, reason="FC 25 raw data not present")
def test_fc25_gk_card_slots_equal_the_files_own_gk_columns():
    import pandas as pd

    raw = pd.read_csv(FC25_CSV)
    gk = raw[raw.Position == "GK"]
    for card, own in [("PAC", "GK Diving"), ("SHO", "GK Handling"), ("PAS", "GK Kicking"),
                      ("DRI", "GK Reflexes"), ("PHY", "GK Positioning")]:
        assert (gk[card] == gk[own]).all(), card


@pytest.mark.skipif(not HAS_FC27, reason="FC 27 raw data not present")
def test_fc27_loader_maps_gk_stats():
    players = load_ea_fc27(27).players
    courtois = players[players.long_name == "Thibaut Courtois"].iloc[0]
    # Card: 87 DIV, 89 HAN, 78 KIC, 90 REF, 46 SPD, 90 POS (pace/shooting/.../physicality columns of the file)
    got = [int(courtois[c]) for c in GK_COLS]
    assert got == [87, 89, 78, 90, 46, 90]
    assert courtois.short_name == "T. Courtois"
    assert courtois.club_team_id == 243


@pytest.mark.skipif(not HAS_FC25, reason="FC 25 raw data not present")
def test_fc25_loader_basic_fields():
    players = load_ea_fc25(25).players
    mbappe = players[players.player_id == 231747].iloc[0]
    assert mbappe.short_name == "K. Mbappé"
    assert mbappe.overall == 91
    assert mbappe.player_positions == "ST, LW"
    assert mbappe.club_team_id == 243
    assert players.club_position.isna().all()


def test_age_on():
    assert age_on("2000-07-21", "2026-09-12") == 26
    assert age_on("2000-09-13", "2026-09-12") == 25
    assert age_on("2000-09-12", "2026-09-12") == 26


# ---------------------------------------------------------------------- nation aliases
def test_nation_aliases_resolve_to_known_nations():
    for alias, canonical in NATION_ALIASES.items():
        assert canonical in NATION_CODES, alias
        assert alias not in NATION_CODES
        assert canonical_nation(alias) == canonical


@pytest.mark.parametrize(
    ("name", "code", "shown"),
    [
        ("Holland", "nl", "Netherlands"),
        ("Türkiye", "tr", "Turkey"),
        ("Czechia", "cz", "Czech Republic"),
        ("Cabo Verde", "cv", "Cape Verde Islands"),
        ("Guinea-Bissau", "gw", "Guinea Bissau"),
        ("Saudi Arabia", "sa", "Saudi Arabia"),
        ("Indonesia", "id", "Indonesia"),
        ("Malaysia", "my", "Malaysia"),
        ("Netherlands", "nl", "Netherlands"),
    ],
)
def test_new_nations_and_aliases(name, code, shown):
    assert nation_code(name) == code
    assert canonical_nation(name) == shown


# ---------------------------------------------------------------------- name overrides (D59)
def test_name_overrides_are_well_formed():
    from name_overrides import NAME_OVERRIDES

    assert NAME_OVERRIDES[(25, 200104)] == "Son"
    for (version, player_id), name in NAME_OVERRIDES.items():
        # Only the EA-format versions use the rule, so only they need fixes
        assert version in (25, 27)
        assert isinstance(player_id, int) and player_id > 0
        assert name.strip() == name and name


def test_stale_name_override_fails():
    import pandas as pd

    from sources import apply_name_overrides

    players = pd.DataFrame({"player_id": [1, 2], "short_name": ["A. One", "B. Two"]})
    with pytest.raises(SystemExit, match="unknown player ids"):
        apply_name_overrides(25, players)


@pytest.mark.skipif(not HAS_FC25, reason="FC 25 raw data not present")
def test_fc25_loader_applies_overrides():
    players = load_ea_fc25(25).players.set_index("player_id")
    assert players.loc[200104].short_name == "Son"
    assert players.loc[190149].short_name == "De Marcos"
    # Untouched rule output
    assert players.loc[231747].short_name == "K. Mbappé"
