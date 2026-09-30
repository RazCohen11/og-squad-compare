import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from best_xi import ADJACENT, NATURAL, SLOTS, Player, UnfillableSlotError, best_xi  # noqa: E402


def make(pid, ovr, positions, ea_pos="SUB"):
    return Player(id=pid, overall=ovr, positions=tuple(positions.split()), ea_pos=ea_pos)


def base_squad():
    """A plain 4-3-3 starting XI plus weaker bench players."""
    return [
        make(1, 85, "GK", "GK"),
        make(2, 80, "LB", "LB"),
        make(3, 82, "CB", "LCB"),
        make(4, 81, "CB", "RCB"),
        make(5, 79, "RB", "RB"),
        make(6, 84, "CM CDM", "LCM"),
        make(7, 83, "CDM", "CDM"),
        make(8, 86, "CAM CM", "RCM"),
        make(9, 84, "LW LM", "LW"),
        make(10, 88, "ST", "ST"),
        make(11, 83, "RW", "RW"),
        # Bench
        make(12, 70, "GK"),
        make(13, 72, "CB LB"),
        make(14, 73, "CM", "RES"),
        make(15, 71, "ST CF"),
        make(16, 69, "RM RB"),
    ]


def by_slot(picks):
    return {p.slot: p for p in picks}


def test_normal_squad_picks_ea_xi_in_slot_order():
    picks = best_xi(base_squad())
    assert [p.slot for p in picks] == list(SLOTS)
    got = {p.slot: p.player.id for p in picks}
    assert got == {"GK": 1, "LB": 2, "LCB": 3, "RCB": 4, "RB": 5, "LCM": 6, "CM": 7, "RCM": 8,
                   "LW": 9, "ST": 10, "RW": 11}
    assert all(p.fit == "natural" for p in picks)


def test_injured_star_on_bench_enters_the_xi():
    squad = base_squad() + [make(99, 91, "CM CAM", "SUB")]
    picks = by_slot(best_xi(squad))
    ids = {p.player.id for p in picks.values()}
    assert 99 in ids
    # The weakest natural central midfielder (83, id 7) drops out
    assert 7 not in ids
    assert picks["CM"].player.id == 99 or picks["LCM"].player.id == 99 or picks["RCM"].player.id == 99


def test_high_rated_player_moves_to_a_secondary_natural_position():
    # A 90 ST who also lists LW beats the 84 LW, while the 88 ST keeps ST
    squad = base_squad() + [make(50, 90, "ST LW", "SUB")]
    picks = by_slot(best_xi(squad))
    assert picks["LW"].player.id == 50
    assert picks["ST"].player.id == 10
    assert picks["LW"].fit == "natural"


def test_no_natural_left_back_uses_adjacent_fallback():
    squad = [p for p in base_squad() if p.id != 2]  # Remove the only LB
    squad = [p for p in squad if p.id != 13]  # Remove the CB/LB backup too
    picks = best_xi(squad)
    adjacent = [p for p in picks if p.fit == "adjacent"]
    assert len(adjacent) == 1
    assert adjacent[0].slot == "LB"
    # RB 79 (id 5) at LB + RM/RB 69 (id 16) at RB ties with the reverse on rating. The first-position
    # tie-break keeps id 5 at RB (RB is listed first), so the RM/RB player covers LB
    lb = by_slot(picks)["LB"].player
    assert set(lb.positions) & ADJACENT["LB"]
    assert not set(lb.positions) & NATURAL["LB"]
    assert lb.id == 16
    assert by_slot(picks)["RB"].player.id == 5


def test_fallback_not_used_when_a_natural_player_exists():
    # A weak natural LB must be preferred to a much stronger adjacent RB
    squad = [p for p in base_squad() if p.id not in (2, 13)] + [make(60, 55, "LB")]
    picks = by_slot(best_xi(squad))
    assert picks["LB"].player.id == 60
    assert all(p.fit == "natural" for p in picks.values())


def test_tie_prefers_first_listed_position_then_ea_xi_then_lower_id():
    squad = base_squad()
    # Equal to the ST (88): lists ST only second, so the natural ST (first position) keeps ST
    squad.append(make(20, 88, "CAM ST"))
    picks = by_slot(best_xi(squad))
    assert picks["ST"].player.id == 10

    # Two equal GKs, neither in EA's XI: lower id wins
    squad2 = [p for p in base_squad() if p.id != 1] + [make(40, 85, "GK"), make(30, 85, "GK")]
    assert by_slot(best_xi(squad2))["GK"].player.id == 30

    # Two equal GKs, the higher id is in EA's XI: EA's XI wins over lower id
    squad3 = [p for p in base_squad() if p.id != 1] + [make(40, 85, "GK", "GK"), make(30, 85, "GK")]
    assert by_slot(best_xi(squad3))["GK"].player.id == 40


def test_tie_breaks_never_outweigh_one_rating_point():
    # Every tie-break favours the XI players, but a bench CB rated 1 point higher still gets in
    squad = base_squad() + [make(1000, 83, "CB")]
    ids = {p.player.id for p in best_xi(squad)}
    assert 1000 in ids
    assert 4 not in ids  # The 81 CB drops out


def test_result_is_deterministic_under_input_order():
    squad = base_squad() + [make(21, 82, "CB"), make(22, 84, "LM LW"), make(23, 84, "RM RW")]
    expected = [(p.slot, p.player.id, p.fit) for p in best_xi(squad)]
    rng = random.Random(7)
    for _ in range(20):
        shuffled = squad[:]
        rng.shuffle(shuffled)
        assert [(p.slot, p.player.id, p.fit) for p in best_xi(shuffled)] == expected


def test_interchangeable_slots_follow_ea_side():
    # The EA RCB (id 3 swapped side) ends up at RCB, the EA LCB at LCB
    squad = [p for p in base_squad() if p.id not in (3, 4)] + [make(3, 82, "CB", "RCB"), make(4, 81, "CB", "LCB")]
    picks = by_slot(best_xi(squad))
    assert picks["LCB"].player.id == 4
    assert picks["RCB"].player.id == 3


def winger_squad(natural_cm_ovr):
    """12 players, one sits out. W (88, LW then CAM) competes with X (88, LW) for LW and with Y for CM.

    W at LW + Y at CM is worth 88 + Y; W at CM + X at LW is worth (88 - 3) + 88 = 173.
    So W stays wide when Y is within 3 points of W (Y >= 86), and moves to CM when the gap is larger.
    """
    return [
        make(1, 80, "GK", "GK"),
        make(2, 80, "LB", "LB"),
        make(3, 80, "CB", "LCB"),
        make(4, 80, "CB", "RCB"),
        make(5, 80, "RB", "RB"),
        make(6, 90, "CM", "LCM"),
        make(7, 90, "CM", "RCM"),
        make(8, natural_cm_ovr, "CM", "CM"),  # Y
        make(9, 88, "LW CAM", "LW"),  # W
        make(10, 88, "LW"),  # X
        make(11, 85, "ST", "ST"),
        make(12, 85, "RW", "RW"),
    ]


def test_wide_first_player_stays_wide_when_natural_cm_is_within_penalty():
    picks = by_slot(best_xi(winger_squad(86)))
    assert picks["LW"].player.id == 9
    cm_ids = {picks[s].player.id for s in ("LCM", "CM", "RCM")}
    assert cm_ids == {6, 7, 8}
    assert 10 not in {p.player.id for p in picks.values()}


def test_wide_first_player_moves_to_cm_when_gap_exceeds_penalty():
    picks = by_slot(best_xi(winger_squad(84)))
    cm_ids = {picks[s].player.id for s in ("LCM", "CM", "RCM")}
    assert 9 in cm_ids
    assert picks["LW"].player.id == 10
    assert 8 not in {p.player.id for p in picks.values()}


def test_secondary_pick_still_beats_much_weaker_primary_pick():
    # CB 85 (RB secondary) is valued 82 at RB, above the natural RB 78; the CB slots hold 88 and 87
    squad = [
        make(1, 80, "GK", "GK"),
        make(2, 80, "LB", "LB"),
        make(3, 88, "CB", "LCB"),
        make(4, 87, "CB", "RCB"),
        make(5, 78, "RB", "RB"),
        make(6, 85, "CB RB"),
        make(7, 80, "CM"), make(8, 80, "CM"), make(9, 80, "CM"),
        make(10, 80, "LW"), make(11, 80, "ST"), make(12, 80, "RW"),
    ]
    picks = by_slot(best_xi(squad))
    assert picks["RB"].player.id == 6
    assert picks["RB"].fit == "natural"
    assert 5 not in {p.player.id for p in picks.values()}


def test_unfillable_gk_raises():
    squad = [p for p in base_squad() if "GK" not in p.positions]
    with pytest.raises(UnfillableSlotError, match="GK"):
        best_xi(squad)


def test_too_small_squad_raises():
    with pytest.raises(UnfillableSlotError):
        best_xi(base_squad()[:8])
