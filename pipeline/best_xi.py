"""Best XI selection into the 11 slots of a canonical 4-3-3.

Pure functions, no I/O. See docs/PLAN.md §3 and docs/DECISIONS.md D19 / D21.

Selection rules
---------------
- The squad is every player of the club in one version (starters, SUB and RES).
- A player is *naturally* eligible for a slot when any of the generic positions in the player's
  `player_positions` is in NATURAL[slot].
- The assignment is optimal (scipy `linear_sum_assignment`) and maximises the sum of each pick's value:
  - a natural pick whose slot matches the player's FIRST listed position is valued at `overall`;
  - a natural pick that matches only a secondary position is valued at `overall - SECONDARY_PENALTY`
    (D24; a FUT card shows one position, the first one);
  - an adjacent pick is valued at `overall - ADJACENT_PENALTY` (see Fallback below).
  The `overall` written to the output is never changed; the penalties only steer the assignment.
- Tie-breaks, in order, are small bonuses in the cost that together can never outweigh 1 rating point:
  1. the slot matches the player's FIRST listed position,
  2. the player was in EA's starting XI,
  3. lower `player_id`.
- Fallback: an ADJACENT position may be used only when no complete natural assignment exists.
  Adjacent edges carry a large lexicographic cost, so the solver first minimises the number of
  adjacent fits and only then maximises rating. On top of that, an adjacent player is valued at
  `overall - ADJACENT_PENALTY`. Such players are marked `fit = "adjacent"`.
- If a slot cannot be filled even with the fallback (e.g. no goalkeeper), UnfillableSlotError is raised.

Interchangeable slots (LCB/RCB and LCM/CM/RCM) have identical eligibility, so the solver's choice
between them is arbitrary. The result is canonicalised: players in such a group are ordered left to
right by the side of their EA position (L*, centre, R*), then by `player_id`.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

SLOTS: tuple[str, ...] = ("GK", "LB", "LCB", "RCB", "RB", "LCM", "CM", "RCM", "LW", "ST", "RW")

# Natural eligibility: slot -> generic positions from `player_positions`
NATURAL: dict[str, frozenset[str]] = {
    "GK": frozenset({"GK"}),
    "LB": frozenset({"LB", "LWB"}),
    "LCB": frozenset({"CB"}),
    "RCB": frozenset({"CB"}),
    "RB": frozenset({"RB", "RWB"}),
    "LCM": frozenset({"CM", "CDM", "CAM"}),
    "CM": frozenset({"CM", "CDM", "CAM"}),
    "RCM": frozenset({"CM", "CDM", "CAM"}),
    "LW": frozenset({"LW", "LM", "LF"}),
    "ST": frozenset({"ST", "CF"}),
    "RW": frozenset({"RW", "RM", "RF"}),
}

# Adjacent (fallback) eligibility: slot -> generic positions that can cover it at a penalty.
# - Full-backs: the opposite full-back / wing-back, or a centre-back.
# - Centre-backs: a defensive midfielder or any full-back / wing-back.
# - Central midfield: a wide midfielder.
# - Wingers: the opposite wing, an attacking midfielder, or a striker.
# - Striker: any winger / wide forward, or an attacking midfielder.
# - Goalkeeper: no fallback.
ADJACENT: dict[str, frozenset[str]] = {
    "GK": frozenset(),
    "LB": frozenset({"RB", "RWB", "CB"}),
    "LCB": frozenset({"CDM", "LB", "RB", "LWB", "RWB"}),
    "RCB": frozenset({"CDM", "LB", "RB", "LWB", "RWB"}),
    "RB": frozenset({"LB", "LWB", "CB"}),
    "LCM": frozenset({"LM", "RM"}),
    "CM": frozenset({"LM", "RM"}),
    "RCM": frozenset({"LM", "RM"}),
    "LW": frozenset({"RW", "RM", "RF", "CAM", "ST", "CF"}),
    "ST": frozenset({"LW", "RW", "LF", "RF", "CAM"}),
    "RW": frozenset({"LW", "LM", "LF", "CAM", "ST", "CF"}),
}

# Groups of slots with identical eligibility, listed left to right
INTERCHANGEABLE: tuple[tuple[str, ...], ...] = (("LCB", "RCB"), ("LCM", "CM", "RCM"))

SECONDARY_PENALTY = 3
ADJACENT_PENALTY = 5
NON_XI_EA_POSITIONS = frozenset({"SUB", "RES"})

# Cost weights. Ratings are at most 99, so one XI sums to less than 1100.
_ADJACENT_COST = 10_000.0  # Makes each adjacent fit costlier than any rating difference
_FORBIDDEN_COST = 1e7  # Marks an ineligible player-slot pair
_BONUS_FIRST_POS = 1e-2  # 11 * 1e-2 = 0.11 < 1 rating point
_BONUS_EA_XI = 1e-4  # 11 * 1e-4 < one first-position bonus
_BONUS_ID = 1e-6  # Scaled by rank in [0, 1); 11 * 1e-6 < one EA-XI bonus


class UnfillableSlotError(ValueError):
    """Raised when a slot has no eligible player, even with the adjacent fallback."""


@dataclass(frozen=True)
class Player:
    id: int
    overall: int
    positions: tuple[str, ...]  # Generic positions in listed order, e.g. ("CM", "CAM")
    ea_pos: str | None = None  # EA `club_position`, e.g. "LCB", "SUB", "RES"

    @property
    def in_ea_xi(self) -> bool:
        return self.ea_pos is not None and self.ea_pos not in NON_XI_EA_POSITIONS


@dataclass(frozen=True)
class Pick:
    slot: str
    player: Player
    fit: str  # "natural" or "adjacent"


def fit_for(player: Player, slot: str) -> str | None:
    """Return "natural", "adjacent" or None for a player in a slot."""
    positions = set(player.positions)
    if positions & NATURAL[slot]:
        return "natural"
    if positions & ADJACENT[slot]:
        return "adjacent"
    return None


def _side_rank(ea_pos: str | None) -> int:
    if ea_pos and ea_pos not in NON_XI_EA_POSITIONS and ea_pos != "GK":
        if ea_pos.startswith("L"):
            return 0
        if ea_pos.startswith("R"):
            return 2
    return 1


def best_xi(squad: list[Player] | tuple[Player, ...]) -> list[Pick]:
    """Pick the best XI of a squad into SLOTS. Returns 11 picks in SLOTS order."""
    ids = [p.id for p in squad]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate player id in squad")

    # Sort by id so the result does not depend on the input order
    players = sorted(squad, key=lambda p: p.id)
    n = len(players)
    cost = np.full((len(SLOTS), max(n, 1)), _FORBIDDEN_COST)
    for j, p in enumerate(players):
        id_bonus = _BONUS_ID * (1 - j / n)
        ea_bonus = _BONUS_EA_XI if p.in_ea_xi else 0.0
        for i, slot in enumerate(SLOTS):
            fit = fit_for(p, slot)
            if fit == "natural":
                if p.positions and p.positions[0] in NATURAL[slot]:
                    value = p.overall + _BONUS_FIRST_POS
                else:
                    value = p.overall - SECONDARY_PENALTY
                cost[i, j] = -(value + ea_bonus + id_bonus)
            elif fit == "adjacent":
                cost[i, j] = _ADJACENT_COST - (p.overall - ADJACENT_PENALTY + ea_bonus + id_bonus)

    rows, cols = linear_sum_assignment(cost)
    chosen: dict[str, Player] = {}
    for i, j in zip(rows, cols):
        if cost[i, j] >= _FORBIDDEN_COST:
            continue
        chosen[SLOTS[i]] = players[j]
    missing = [s for s in SLOTS if s not in chosen]
    if missing:
        raise UnfillableSlotError(f"No eligible player for slot(s): {', '.join(missing)}")

    # Canonical left-to-right order inside interchangeable slot groups
    for group in INTERCHANGEABLE:
        group_players = sorted((chosen[s] for s in group), key=lambda p: (_side_rank(p.ea_pos), p.id))
        for slot, p in zip(group, group_players):
            chosen[slot] = p

    return [Pick(slot=s, player=chosen[s], fit=fit_for(chosen[s], s)) for s in SLOTS]
