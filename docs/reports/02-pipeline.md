# Stage 02 report — Data pipeline + Best XI in 4-3-3

> Updated in stage 02b (secondary-position penalty, D24). The generated data sections and the validate
> output reflect the 02b data. The 02b changes are summarised in the last section.

## What was done

0. **Housekeeping** (separate commit `0190cfd`)
   - Added `.gitattributes` (`* text=auto eol=lf`) and ran a one-time renormalise. `explore.py` now writes with
     `newline="\n"`, which was the source of the CRLF in the stage 01 report. All new scripts write UTF-8 with LF.
   - Committed the planning-session versions of `docs/PLAN.md` (v3), `docs/DECISIONS.md` (D12–D23) and
     `docs/prompts/02-pipeline.md` as-is.
1. **`pipeline/best_xi.py`** is a pure module with no I/O. It contains the slots, the `NATURAL` and `ADJACENT`
   eligibility tables, and `best_xi(squad) -> list[Pick]`, which uses scipy `linear_sum_assignment`.
   - The cost of a natural pick is `-(ovr + tie-break bonuses)`. The bonuses are: first listed position 1e-2,
     in EA's XI 1e-4, lower id up to 1e-6 (by id rank). Summed over 11 picks, the bonuses of each level stay
     below one bonus of the level above, and all of them together stay below 1 rating point.
   - The cost of an adjacent pick is `10 000 - (ovr - 5 + bonuses)`. The solver therefore minimises the
     number of adjacent fits first, so they are used only when no complete natural XI exists. It then
     maximises rating.
   - If a slot is still unfilled, the module raises `UnfillableSlotError`.
   - LCB/RCB and LCM/CM/RCM have identical eligibility, so the solver's left/right choice between them is
     arbitrary. The module fixes it: players are ordered by the side of their EA position (L…, centre, R…),
     then by id. This keeps output deterministic and puts an EA left-centre-back at LCB.
   - The adjacency table is documented in the module docstring and comments.
2. **`pipeline/tests/test_best_xi.py`** has 11 pytest tests, all passing. They cover:
   - a normal squad and an injured star from the bench;
   - moving a player to a secondary natural position;
   - the no-natural-LB adjacent fallback, and that the fallback is not used when a weak natural LB exists;
   - each tie-break level, and that tie-breaks never outweigh 1 point;
   - determinism under shuffled input and EA-side ordering of the CBs;
   - an unfillable GK, and a squad that is too small.
   pytest was added to `requirements.txt`.
3. **`pipeline/build.py`** writes `app/public/data/versions.json` and `app/public/data/<v>/teams.json` in the
   format from the prompt.
   - Teams are filtered by `league_id` (D17), and the D13 exclusions live in the `EXCLUDED_TEAMS` config.
   - The build stops with an error if any team's squad has fewer than 11 players.
   - The output is minified with no image URLs, and rebuilds are byte-identical.
4. **`pipeline/validate.py`** reads only the generated JSON and exits 1 on any failure. It runs all checks
   from the prompt, plus: `versions.json` agrees with the team files, GK players have `gk` and not `stats`
   (and the reverse), and adjacent fits are really adjacent.
   - I checked that it catches errors by corrupting `24/teams.json` in five ways: ovr 120, a null stat,
     an ineligible natural fit, a player in two teams, and a missing team. It reported all six resulting
     errors and exited 1. The file was then rebuilt.
5. **`pipeline/report_02.py`** is a small helper that prints the data sections of this report: the Best XI
   vs EA's XI comparison, adjacent fits, output sizes and sample XIs.

## Files

Created:
- `.gitattributes`
- `pipeline/best_xi.py`, `pipeline/build.py`, `pipeline/validate.py`, `pipeline/report_02.py`
- `pipeline/tests/test_best_xi.py`
- `app/public/data/versions.json` and `app/public/data/{15..24}/teams.json`
- `docs/reports/02-pipeline.md`

Changed: `pipeline/requirements.txt` (added `pytest==8.4.2`) and `pipeline/explore.py` (LF output only).

Deleted: none.

## How to run

From the repository root (Windows paths shown; use `pipeline/.venv/bin/python` on macOS / Linux):

```bash
pipeline/.venv/Scripts/python -m pip install -r pipeline/requirements.txt
pipeline/.venv/Scripts/python -m pytest pipeline/tests -q      # 14 passed (after 02b)
pipeline/.venv/Scripts/python pipeline/build.py                # ~4 s, writes app/public/data/
pipeline/.venv/Scripts/python pipeline/validate.py             # prints summary, exit 0 = OK
pipeline/.venv/Scripts/python pipeline/report_02.py            # optional: report tables as markdown
```

`validate.py` output (after 02b):

```
version teams players adjacent from SUB/RES
     15    98    1078        3          356
     16    98    1078        1          305
     17    98    1078        1          251
     18    98    1078        0          265
     19    98    1078        0          223
     20    98    1078        0          227
     21    96    1056        2          239
     22    98    1078        1          274
     23    98    1078        3          297
     24    96    1056        0          275
  total   976   10736       11         2712

OK: all checks passed
```

## Open issues

1. ~~**Secondary positions are used freely.**~~ **Resolved in 02b (D24).** Before 02b, 12.9% of natural
   picks sat in a slot matching only a secondary position, and star wingers (Neymar, Coutinho, Payet…) landed
   in central midfield via CAM. A 3-point secondary-position penalty now applies (see the 02b section).
2. **The Best XI differs a lot from EA's XI**: 2.3–3.6 players per team on average (2.28–3.63), 2,712 of 10,736 picks
   from SUB/RES (after 02b). Most of this is by design (D19): the whole squad is used, and every team is forced into a
   4-3-3. A team EA fielded in a 3-5-2 or 4-4-2 loses a striker or a centre-back to the shape. Lower-table
   clubs change most (Nottingham Forest, Watford, Leicester in FIFA 15), because EA's XI there often isn't
   the highest-rated one.
3. **The 5-point adjacent penalty has no practical effect.** Adjacent fits are allowed only when needed,
   and the solver first minimises how many are used. Among assignments with the same number of adjacent
   fits, the penalty subtracts the same total from each, so it never changes the outcome. The penalty is
   still implemented as specified. It would only matter if adjacency were allowed to compete with natural
   fits.
4. **`eaFormation` reflects the gaps in the data.** For the FIFA 16 clubs that are missing starters (stage 01),
   it gives shapes like `4-5-0` (Man United) or `4-4-1`, because the D-M-A string is derived from an
   incomplete XI.
5. **Team names come from the data**, e.g. "Paris Saint Germain" without the hyphen, and "Inter".

## Assumptions not in the prompt

- An adjacent pick is valued at `ovr - 5` and still gets the EA-XI and id tie-breaks, but never the
  first-position bonus.
- EA-side ordering inside LCB/RCB and LCM/CM/RCM (described above) is my own choice. The prompt did not
  specify how to order those slots.
- `positions` keeps the data order and can hold up to 4 entries (PLAN says up to 3).
- Clubless players (null `club_team_id`) are dropped before building squads. Squads include every
  `club_position`, including null, but no top-5 squad player has a null `club_position`.
- Teams are sorted by league in the order EPL, La Liga, Serie A, Bundesliga, Ligue 1, then by team `ovr`
  descending, then by name.
- Files are written without a trailing newline, since they are minified.
- In the "10 biggest changes" table, a change means a Best XI player who was not in EA's XI. Rows are
  ranked by number of changes, then by total rating gain. The gain is shown as n/a where EA's XI in the
  data has fewer than 11 players (FIFA 16).
- The adjacency table extends the prompt's examples symmetrically. Wingers can also be covered by the
  opposite wide midfielder or forward and by CF, and centre-backs by wing-backs. LF and RF are in the
  tables for completeness, but never occur in `player_positions`: the data has 15 generic codes.

The sections below were generated by `pipeline/report_02.py`.

## Best XI vs EA's starting XI

"Changed" = Best XI players who were not in EA's starting XI (SUB/RES in the data).

| version | teams | avg changed per team | teams unchanged | max changed |
|---|---|---|---|---|
| 15 | 98 | 3.63 | 1 | 7 |
| 16 | 98 | 3.11 | 2 | 7 |
| 17 | 98 | 2.56 | 3 | 6 |
| 18 | 98 | 2.70 | 4 | 5 |
| 19 | 98 | 2.28 | 7 | 6 |
| 20 | 98 | 2.32 | 4 | 5 |
| 21 | 96 | 2.49 | 4 | 6 |
| 22 | 98 | 2.80 | 2 | 7 |
| 23 | 98 | 3.03 | 0 | 8 |
| 24 | 96 | 2.86 | 2 | 8 |

### 10 biggest changes

Ranked by number of changed players, then by total XI rating gain over EA's XI (n/a when EA's XI in the data has fewer than 11 players).

| version | team | changed | XI ovr gain | in | out |
|---|---|---|---|---|---|
| 23 | Nottingham Forest | 8 | 41 | Renan Lodi 80 (SUB→LB), W. Boly 78 (SUB→LCB), M. Niakhaté 78 (SUB→RCB), S. Aurier 78 (RES→RB), C. Kouyaté 77 (RES→LCM), R. Freuler 80 (SUB→CM), E. Dennis 76 (SUB→LW), T. Awoniyi 77 (SUB→ST) | M. Gibbs-White 75 (LS), J. Worrall 74 (RCB), L. O'Brien 73 (RCM), R. Yates 73 (LCM), S. McKenna 73 (LCB), H. Toffolo 72 (LWB), S. Cook 72 (CB), N. Williams 71 (RWB) |
| 24 | Nottingham Forest | 8 | 22 | O. Vlachodimos 81 (SUB→GK), Nuno Tavares 76 (SUB→LB), Felipe 78 (RES→LCB), M. Niakhaté 77 (SUB→RCB), G. Montiel 79 (SUB→RB), I. Sangaré 81 (SUB→CM), N. Domínguez 77 (SUB→RCM), C. Hudson-Odoi 75 (SUB→LW) | S. Aurier 78 (RWB), M. Turner 77 (GK), Danilo 76 (LCM), W. Boly 76 (RCB), R. Yates 75 (RCM), J. Worrall 74 (CB), S. McKenna 73 (LCB), O. Aina 73 (LWB) |
| 15 | Leicester City | 7 | 27 | M. Upson 72 (SUB→LCB), D. Simpson 73 (SUB→RB), E. Cambiasso 78 (SUB→LCM), D. Drinkwater 70 (SUB→CM), N. Powell 69 (SUB→RCM), A. Knockaert 70 (SUB→LW), M. Albrighton 71 (SUB→RW) | D. Nugent 71 (RS), L. Moore 69 (LCB), R. Mahrez 69 (RM), R. De Laet 69 (RB), A. King 68 (RCM), D. Hammond 67 (LCM), J. Schlupp 63 (LM) |
| 15 | Aston Villa | 7 | 25 | R. Vlaar 79 (SUB→LCB), C. Clark 73 (RES→RCB), M. Lowton 73 (SUB→RB), C. Sánchez 76 (SUB→CM), C. N'Zogbia 75 (SUB→LW), C. Benteke 80 (SUB→ST), J. Cole 74 (SUB→RW) | A. Weimann 73 (RS), K. Richardson 73 (CAM), G. Agbonlahor 73 (LS), A. Westwood 72 (CDM), P. Senderos 72 (RCB), N. Baker 71 (LCB), A. Hutton 71 (RB) |
| 22 | Watford | 7 | 23 | B. Foster 78 (SUB→GK), D. Rose 75 (SUB→LB), C. Kabasele 75 (SUB→LCB), Kiko Femenía 75 (SUB→RB), J. Kucka 77 (SUB→LCM), O. Tufan 76 (SUB→CM), J. King 75 (SUB→ST) | E. Dennis 74 (ST), A. Masina 74 (LB), T. Cleverley 74 (LCM), F. Sierralta 72 (LCB), O. Etebo 72 (CDM), C. Cathcart 72 (RB), D. Bachmann 70 (GK) |
| 23 | FC Augsburg | 7 | 23 | F. Uduokhai 75 (SUB→RCB), R. Oxford 76 (SUB→RB), J. Baumgartlinger 76 (SUB→LCM), N. Dorsch 77 (RES→CM), A. Maier 76 (SUB→RCM), R. Vargas 75 (SUB→LW), D. Caligiuri 75 (SUB→RW) | F. Niederlechner 74 (RS), M. Berisha 73 (LS), E. Demirović 73 (LM), E. Rexhbeçaj 73 (LDM), C. Gruezo 72 (RDM), M. Bauer 71 (RCB), R. Gumny 71 (RB) |
| 15 | Crystal Palace | 7 | 15 | B. Hangeland 74 (SUB→LCB), M. Kelly 74 (SUB→RB), M. Chamakh 75 (SUB→CM), J. Ledley 72 (SUB→RCM), Y. Bolasie 73 (SUB→LW), A. Johnson 73 (SUB→ST), B. Bannan 75 (SUB→RW) | J. Puncheon 73 (RM), W. Zaha 72 (LM), F. Campbell 72 (CAM), D. Delaney 72 (LCB), J. McArthur 71 (RDM), D. Gayle 71 (ST), A. Mariappa 70 (RB) |
| 16 | Juventus | 7 | n/a (EA XI had 10) | Alex Sandro 82 (SUB→LB), A. Barzagli 84 (SUB→RCB), C. Marchisio 84 (SUB→CM), S. Khedira 83 (SUB→RCM), K. Asamoah 79 (SUB→LW), M. Mandžukić 83 (SUB→ST), J. Cuadrado 82 (SUB→RW) | L. Bonucci 83 (RCB), Morata 81 (LS), R. Pereyra 81 (CAM), P. Evra 81 (LB), P. Dybala 78 (RS), S. Sturaro 77 (CDM) |
| 19 | Lille | 6 | 35 | V. Enyeama 76 (RES→GK), A. Soumaoro 74 (SUB→LCB), Edgar Ié 74 (SUB→RB), Thiago Mendes 76 (SUB→CM), Thiago Maia 75 (SUB→RCM), Luiz Araújo 74 (SUB→LW) | M. Maignan 75 (GK), Xeka 73 (LDM), J. Bamba 71 (LM), Z. Çelik 66 (RB), Gabriel 66 (LCB), B. Soumaré 63 (RDM) |
| 15 | West Bromwich Albion | 6 | 34 | J. Lescott 79 (SUB→RCB), C. Gamboa 71 (SUB→RB), S. Sessègnon 77 (SUB→LCM), Y. Mulumbu 76 (SUB→CM), C. Yacob 77 (SUB→RCM), Varela 78 (SUB→RW) | C. Gardner 74 (LDM), G. Dorrans 73 (RM), J. Morrison 73 (RDM), A. Wisdom 69 (RB), C. Dawson 68 (RCB), S. Berahino 67 (CAM) |

## Adjacent fits

| version | team | slot | player | ovr | positions | eaPos |
|---|---|---|---|---|---|---|
| 15 | Empoli | LW | M. Maccarone | 72 | ST | SUB |
| 15 | Empoli | RW | P. Zieliński | 68 | CAM, CF | SUB |
| 15 | Toulouse | LB | A. Aguilar | 73 | CDM, CB | CDM |
| 16 | Sampdoria | RW | L. Christodoulopoulos | 75 | CM, LW | SUB |
| 17 | Empoli | RW | M. Pucciarelli | 75 | ST, CF | RS |
| 21 | Sheffield United | RW | D. McGoldrick | 74 | ST | LS |
| 21 | Montpellier | RW | G. Laborde | 76 | ST | RS |
| 22 | Inter | RW | E. Džeko | 83 | ST | RS |
| 23 | Empoli | RW | M. Pjaca | 75 | CF, ST | SUB |
| 23 | Strasbourg | LW | L. Ajorque | 79 | ST | LS |
| 23 | Strasbourg | RW | H. Diallo | 77 | ST | SUB |

## Output file sizes

| version | file | raw (KB) | gzip (KB) |
|---|---|---|---|
| 15 | 15/teams.json | 252.5 | 47.0 |
| 16 | 16/teams.json | 252.9 | 47.1 |
| 17 | 17/teams.json | 252.4 | 47.2 |
| 18 | 18/teams.json | 252.8 | 47.4 |
| 19 | 19/teams.json | 253.4 | 47.9 |
| 20 | 20/teams.json | 252.3 | 47.5 |
| 21 | 21/teams.json | 247.6 | 46.5 |
| 22 | 22/teams.json | 252.8 | 47.6 |
| 23 | 23/teams.json | 252.6 | 47.3 |
| 24 | 24/teams.json | 247.9 | 46.6 |
|  | versions.json | 2.2 | 0.3 |

## Sample XIs

### FIFA 21 — FC Barcelona (EA formation 4-3-3)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | M. ter Stegen | GK | 90 | GK | natural |
| LB | Jordi Alba | LB | 86 | LB | natural |
| LCB | C. Lenglet | CB | 85 | LCB | natural |
| RCB | Piqué | CB | 86 | RCB | natural |
| RB | Nélson Semedo | RB | 83 | RB | natural |
| LCM | F. de Jong | CM | 85 | LCM | natural |
| CM | Sergio Busquets | CDM | 87 | SUB | natural |
| RCM | M. Pjanić | CM, CDM | 85 | RCM | natural |
| LW | A. Griezmann | ST, CF, LW | 87 | ST | natural |
| ST | L. Suárez | ST | 87 | SUB | natural |
| RW | L. Messi | RW, ST, CF | 93 | CAM | natural |

### FIFA 22 — Paris Saint Germain (EA formation 4-3-3)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | G. Donnarumma | GK | 89 | GK | natural |
| LB | Juan Bernat | LB | 82 | LB | natural |
| LCB | Sergio Ramos | CB | 88 | LCB | natural |
| RCB | Marquinhos | CB, CDM | 87 | RCB | natural |
| RB | A. Hakimi | RB, RWB | 85 | RB | natural |
| LCM | M. Verratti | CM, CAM | 87 | LCM | natural |
| CM | I. Gueye | CDM, CM | 82 | CM | natural |
| RCM | G. Wijnaldum | CM, CDM | 84 | RCM | natural |
| LW | Neymar Jr | LW, CAM | 91 | LW | natural |
| ST | K. Mbappé | ST, LW | 91 | ST | natural |
| RW | L. Messi | RW, ST, CF | 93 | RW | natural |

### EA SPORTS FC 24 — Real Madrid (EA formation 4-4-2)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | T. Courtois | GK | 90 | SUB | natural |
| LB | F. Mendy | LB | 82 | SUB | natural |
| LCB | D. Alaba | CB, LB | 85 | LCB | natural |
| RCB | Éder Militão | CB | 86 | SUB | natural |
| RB | Carvajal | RB | 82 | RB | natural |
| LCM | L. Modrić | CM | 87 | SUB | natural |
| CM | J. Bellingham | CM, CAM | 86 | CAM | natural |
| RCM | F. Valverde | CM, RW | 88 | RCM | natural |
| LW | Vini Jr. | LW | 89 | SUB | natural |
| ST | Joselu | ST | 82 | LS | natural |
| RW | Rodrygo | RW, LW, ST | 85 | RS | natural |

### EA SPORTS FC 24 — Manchester City (EA formation 4-3-3)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | Ederson | GK | 88 | GK | natural |
| LB | J. Gvardiol | CB, LB | 82 | SUB | natural |
| LCB | Rúben Dias | CB | 89 | LCB | natural |
| RCB | J. Stones | CB, RB | 85 | RCB | natural |
| RB | K. Walker | RB | 84 | RB | natural |
| LCM | K. De Bruyne | CM, CAM | 91 | SUB | natural |
| CM | Bernardo Silva | CM, RW | 88 | SUB | natural |
| RCM | Rodri | CDM, CM | 89 | RCM | natural |
| LW | J. Grealish | LW, LM | 85 | LW | natural |
| ST | E. Haaland | ST | 91 | ST | natural |
| RW | P. Foden | LW, RW | 85 | RW | natural |

### FIFA 16 — Manchester United (EA formation 4-5-0)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | De Gea | GK | 86 | GK | natural |
| LB | L. Shaw | LB | 78 | SUB | natural |
| LCB | M. Rojo | CB, LB | 81 | LB | natural |
| RCB | P. Jones | CB, RB | 80 | SUB | natural |
| RB | M. Darmian | RB, RWB, LWB | 81 | RB | natural |
| LCM | M. Schneiderlin | CDM, CM | 82 | LDM | natural |
| CM | B. Schweinsteiger | CM, CDM | 86 | SUB | natural |
| RCM | Ander Herrera | CM, CAM | 81 | SUB | natural |
| LW | M. Depay | LW, CAM | 81 | LM | natural |
| ST | W. Rooney | ST, CM, CAM | 86 | CAM | natural |
| RW | Juan Mata | RM, CAM | 84 | RM | natural |

### FIFA 18 — Liverpool (EA formation 4-3-3)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | S. Mignolet | GK | 81 | GK | natural |
| LB | J. Milner | LB, CM | 80 | SUB | natural |
| LCB | D. Lovren | CB | 81 | LCB | natural |
| RCB | J. Matip | CB | 83 | RCB | natural |
| RB | N. Clyne | RB | 82 | RB | natural |
| LCM | A. Lallana | CM | 83 | SUB | natural |
| CM | J. Henderson | CDM, CM | 82 | CDM | natural |
| RCM | G. Wijnaldum | CM, CAM | 82 | RCM | natural |
| LW | Coutinho | LW, CAM | 86 | LCM | natural |
| ST | Roberto Firmino | ST, CF, CAM | 83 | ST | natural |
| RW | S. Mané | RW, LW | 84 | LW | natural |


## 02b — Secondary-position penalty (D24)

### What changed

- `pipeline/best_xi.py`: added `SECONDARY_PENALTY = 3`. A natural pick whose slot does not match the
  player's first listed position is now valued at `overall - 3`. First-position natural picks and adjacent
  picks are unchanged, and so are the tie-break bonuses and their guarantees. The module docstring now
  lists the three pick values. The `ovr` written to the JSON is never changed; the penalty only affects
  the assignment.
- `pipeline/tests/test_best_xi.py`: 3 new tests, 14 in total, all passing.
  - `test_wide_first_player_stays_wide_when_natural_cm_is_within_penalty`: a player listed LW then CAM
    stays at LW when a natural CM is within 3 points. I checked that this test fails when the penalty is
    set to 0.
  - `test_wide_first_player_moves_to_cm_when_gap_exceeds_penalty`: the same player moves to CM when the
    gap is 4.
  - `test_secondary_pick_still_beats_much_weaker_primary_pick`: a CB 85 still takes RB over a natural RB 78.
  - None of the 11 existing tests needed a changed expectation.
- `pipeline/report_02.py`: FIFA 18 Liverpool added to the sample XIs.
- Rebuilt `app/public/data/`. `validate.py` passes and the build is still deterministic.
- `docs/PLAN.md`, `docs/DECISIONS.md` (D24–D26) and the 02b prompt were committed as-is from the
  planning session.

### Before / after

"Before" is the stage 02 data (commit `96e0c29`, no penalty). "After" is the data with the 3-point penalty.
In total, 587 of 976 teams changed at least one slot assignment, and 738 players were swapped in or out
across all XIs. Most changes only move players between slots.

| metric | before (no penalty) | after (penalty 3) |
|---|---|---|
| secondary-position picks (of 10,725 natural picks) | 1,384 (12.9%) | 478 (4.5%) |
| wide/attacking-first players in LCM/CM/RCM | 211 | 27 |

| version | avg XI rating sum before | after | diff |
|---|---|---|---|
| 15 | 833.44 | 831.98 | -1.46 |
| 16 | 847.40 | 845.77 | -1.63 |
| 17 | 858.73 | 857.32 | -1.42 |
| 18 | 859.41 | 857.91 | -1.50 |
| 19 | 859.20 | 858.04 | -1.16 |
| 20 | 858.09 | 856.37 | -1.72 |
| 21 | 856.10 | 854.53 | -1.57 |
| 22 | 857.04 | 855.63 | -1.41 |
| 23 | 856.83 | 855.66 | -1.16 |
| 24 | 854.86 | 853.51 | -1.35 |
| all | 854.11 | 852.67 | -1.44 |


#### FIFA 21 — FC Barcelona

| slot | before | after |
|---|---|---|
| GK | M. ter Stegen 90 (GK) | M. ter Stegen 90 (GK) |
| LB | Jordi Alba 86 (LB) | Jordi Alba 86 (LB) |
| LCB | C. Lenglet 85 (CB) | C. Lenglet 85 (CB) |
| RCB | Piqué 86 (CB) | Piqué 86 (CB) |
| RB | Nélson Semedo 83 (RB) | Nélson Semedo 83 (RB) |
| LCM | F. de Jong 85 (CM) | F. de Jong 85 (CM) |
| CM | Sergio Busquets 87 (CDM) | Sergio Busquets 87 (CDM) |
| RCM | M. Pjanić 85 (CM, CDM) | M. Pjanić 85 (CM, CDM) |
| LW | A. Griezmann 87 (ST, CF, LW) | A. Griezmann 87 (ST, CF, LW) |
| ST | L. Suárez 87 (ST) | L. Suárez 87 (ST) |
| RW | L. Messi 93 (RW, ST, CF) | L. Messi 93 (RW, ST, CF) |

#### FIFA 22 — Paris Saint Germain

| slot | before | after |
|---|---|---|
| GK | G. Donnarumma 89 (GK) | G. Donnarumma 89 (GK) |
| LB | Juan Bernat 82 (LB) | Juan Bernat 82 (LB) |
| LCB | Sergio Ramos 88 (CB) | Sergio Ramos 88 (CB) |
| RCB | Marquinhos 87 (CB, CDM) | Marquinhos 87 (CB, CDM) |
| RB | A. Hakimi 85 (RB, RWB) | A. Hakimi 85 (RB, RWB) |
| LCM | Neymar Jr 91 (LW, CAM) | M. Verratti 87 (CM, CAM) ◀ |
| CM | M. Verratti 87 (CM, CAM) | I. Gueye 82 (CDM, CM) ◀ |
| RCM | G. Wijnaldum 84 (CM, CDM) | G. Wijnaldum 84 (CM, CDM) |
| LW | Á. Di María 87 (RW, LW) | Neymar Jr 91 (LW, CAM) ◀ |
| ST | K. Mbappé 91 (ST, LW) | K. Mbappé 91 (ST, LW) |
| RW | L. Messi 93 (RW, ST, CF) | L. Messi 93 (RW, ST, CF) |

#### FIFA 24 — Real Madrid

| slot | before | after |
|---|---|---|
| GK | T. Courtois 90 (GK) | T. Courtois 90 (GK) |
| LB | D. Alaba 85 (CB, LB) | F. Mendy 82 (LB) ◀ |
| LCB | Éder Militão 86 (CB) | D. Alaba 85 (CB, LB) ◀ |
| RCB | A. Rüdiger 85 (CB) | Éder Militão 86 (CB) ◀ |
| RB | Nacho Fernández 83 (CB, LB, RB) | Carvajal 82 (RB) ◀ |
| LCM | L. Modrić 87 (CM) | L. Modrić 87 (CM) |
| CM | T. Kroos 86 (CM, CDM) | J. Bellingham 86 (CM, CAM) ◀ |
| RCM | J. Bellingham 86 (CM, CAM) | F. Valverde 88 (CM, RW) ◀ |
| LW | Vini Jr. 89 (LW) | Vini Jr. 89 (LW) |
| ST | Rodrygo 85 (RW, LW, ST) | Joselu 82 (ST) ◀ |
| RW | F. Valverde 88 (CM, RW) | Rodrygo 85 (RW, LW, ST) ◀ |

#### FIFA 24 — Manchester City

| slot | before | after |
|---|---|---|
| GK | Ederson 88 (GK) | Ederson 88 (GK) |
| LB | J. Gvardiol 82 (CB, LB) | J. Gvardiol 82 (CB, LB) |
| LCB | Rúben Dias 89 (CB) | Rúben Dias 89 (CB) |
| RCB | J. Stones 85 (CB, RB) | J. Stones 85 (CB, RB) |
| RB | K. Walker 84 (RB) | K. Walker 84 (RB) |
| LCM | K. De Bruyne 91 (CM, CAM) | K. De Bruyne 91 (CM, CAM) |
| CM | Bernardo Silva 88 (CM, RW) | Bernardo Silva 88 (CM, RW) |
| RCM | Rodri 89 (CDM, CM) | Rodri 89 (CDM, CM) |
| LW | J. Grealish 85 (LW, LM) | J. Grealish 85 (LW, LM) |
| ST | E. Haaland 91 (ST) | E. Haaland 91 (ST) |
| RW | P. Foden 85 (LW, RW) | P. Foden 85 (LW, RW) |

#### FIFA 16 — Manchester United

| slot | before | after |
|---|---|---|
| GK | De Gea 86 (GK) | De Gea 86 (GK) |
| LB | D. Blind 80 (CDM, LB, CM) | L. Shaw 78 (LB) ◀ |
| LCB | M. Rojo 81 (CB, LB) | M. Rojo 81 (CB, LB) |
| RCB | P. Jones 80 (CB, RB) | P. Jones 80 (CB, RB) |
| RB | M. Darmian 81 (RB, RWB, LWB) | M. Darmian 81 (RB, RWB, LWB) |
| LCM | M. Schneiderlin 82 (CDM, CM) | M. Schneiderlin 82 (CDM, CM) |
| CM | B. Schweinsteiger 86 (CM, CDM) | B. Schweinsteiger 86 (CM, CDM) |
| RCM | Ander Herrera 81 (CM, CAM) | Ander Herrera 81 (CM, CAM) |
| LW | M. Depay 81 (LW, CAM) | M. Depay 81 (LW, CAM) |
| ST | W. Rooney 86 (ST, CM, CAM) | W. Rooney 86 (ST, CM, CAM) |
| RW | Juan Mata 84 (RM, CAM) | Juan Mata 84 (RM, CAM) |

#### FIFA 18 — Liverpool

| slot | before | after |
|---|---|---|
| GK | S. Mignolet 81 (GK) | S. Mignolet 81 (GK) |
| LB | J. Milner 80 (LB, CM) | J. Milner 80 (LB, CM) |
| LCB | D. Lovren 81 (CB) | D. Lovren 81 (CB) |
| RCB | J. Matip 83 (CB) | J. Matip 83 (CB) |
| RB | N. Clyne 82 (RB) | N. Clyne 82 (RB) |
| LCM | Coutinho 86 (LW, CAM) | A. Lallana 83 (CM) ◀ |
| CM | A. Lallana 83 (CM) | J. Henderson 82 (CDM, CM) ◀ |
| RCM | G. Wijnaldum 82 (CM, CAM) | G. Wijnaldum 82 (CM, CAM) |
| LW | S. Mané 84 (RW, LW) | Coutinho 86 (LW, CAM) ◀ |
| ST | Roberto Firmino 83 (ST, CF, CAM) | Roberto Firmino 83 (ST, CF, CAM) |
| RW | M. Salah 83 (RW) | S. Mané 84 (RW, LW) ◀ |

### Comparison with the planning simulation

| | planning simulation | this build |
|---|---|---|
| secondary picks | ~489 (4.6%) | 478 (4.5% of natural picks) |
| wide-first players in CM | 27 | 27 |
| average XI sum change | −1.4 | −1.44 |
| FIFA 22 PSG | Neymar LW, Mbappé ST, Messi RW | same |
| FC 24 Real Madrid | F. Mendy LB, Carvajal RB, Joselu ST | same |

The difference of 11 in secondary picks is exactly the 11 adjacent picks. An adjacent pick never matches
the player's first position, so counting "first position not in the slot's natural set" over all 10,736
picks gives 478 + 11 = 489 (4.6%). My count includes natural picks only, so both numbers describe the same
build.

### Notes

- **FIFA 18 Liverpool:** Coutinho (LW, CAM) now plays LW and Mané (RW, LW) moves to RW, both in their
  first positions. Salah (83, RW) drops out and Henderson (82, CDM/CM) comes in at CM. The rule works
  correctly here: Mané at RW (84) outranks Salah (83), and the new XI's values sum higher (417 vs 412
  over the five changed slots). Players may still find it surprising that Salah is out.
- **FC 24 Real Madrid:** Valverde (CM, RW) moves from RW to RCM (his first position). Kroos (86, CM)
  drops out: he ties with Bellingham (86, CM), and Bellingham wins the second tie-break because he was in
  EA's XI. The central midfielders are Modrić 87, Bellingham 86 and Valverde 88.
- **FIFA 16 Manchester United:** Shaw (LB, 78) replaces Blind (CDM first, 80 valued 77) at LB.
