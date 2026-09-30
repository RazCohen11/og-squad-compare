# Stage 02 report — Data pipeline + Best XI in 4-3-3

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
pipeline/.venv/Scripts/python -m pytest pipeline/tests -q      # 11 passed
pipeline/.venv/Scripts/python pipeline/build.py                # ~4 s, writes app/public/data/
pipeline/.venv/Scripts/python pipeline/validate.py             # prints summary, exit 0 = OK
pipeline/.venv/Scripts/python pipeline/report_02.py            # optional: report tables as markdown
```

`validate.py` output:

```
version teams players adjacent from SUB/RES
     15    98    1078        3          354
     16    98    1078        1          310
     17    98    1078        1          251
     18    98    1078        0          260
     19    98    1078        0          234
     20    98    1078        0          227
     21    96    1056        2          243
     22    98    1078        1          280
     23    98    1078        3          294
     24    96    1056        0          279
  total   976   10736       11         2732

OK: all checks passed
```

## Open issues

1. **Secondary positions are used freely.** `first listed position` is only a tie-break, so any natural
   position counts fully. 12.9% of natural picks (1,384 of 10,725) sit in a slot that matches only a
   secondary position. Most are sensible: CB→RB/LB, ST→LW/RW, LM↔RW. But because CAM is eligible for all
   three CM slots, 11 star wingers or forwards rated 85+ end up in central midfield. Examples: Neymar
   (LW, CAM) at LCM for PSG in FIFA 20–22, Coutinho (LW, CAM) for Liverpool in FIFA 18, Payet, Mahrez,
   Müller, and Rooney (FIFA 15). This follows D21 as written. If it reads wrong in the game, the options are
   a small penalty for a secondary position (e.g. 1–2 points), or dropping CAM from the CM slots for
   players whose first position is wide. This needs a planning decision.
2. **The Best XI differs a lot from EA's XI**: 2.3–3.6 players per team on average, 2,732 of 10,736 picks
   from SUB/RES. Most of this is by design (D19): the whole squad is used, and every team is forced into a
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
| 15 | 98 | 3.61 | 1 | 8 |
| 16 | 98 | 3.16 | 1 | 6 |
| 17 | 98 | 2.56 | 3 | 7 |
| 18 | 98 | 2.65 | 3 | 5 |
| 19 | 98 | 2.39 | 5 | 6 |
| 20 | 98 | 2.32 | 3 | 5 |
| 21 | 96 | 2.53 | 3 | 6 |
| 22 | 98 | 2.86 | 1 | 8 |
| 23 | 98 | 3.00 | 0 | 8 |
| 24 | 96 | 2.91 | 1 | 8 |

### 10 biggest changes

Ranked by number of changed players, then by total XI rating gain over EA's XI (n/a when EA's XI in the data has fewer than 11 players).

| version | team | changed | XI ovr gain | in | out |
|---|---|---|---|---|---|
| 23 | Nottingham Forest | 8 | 41 | Renan Lodi 80 (SUB→LB), W. Boly 78 (SUB→LCB), M. Niakhaté 78 (SUB→RCB), S. Aurier 78 (RES→RB), C. Kouyaté 77 (RES→LCM), R. Freuler 80 (SUB→CM), E. Dennis 76 (SUB→LW), T. Awoniyi 77 (SUB→ST) | M. Gibbs-White 75 (LS), J. Worrall 74 (RCB), L. O'Brien 73 (RCM), R. Yates 73 (LCM), S. McKenna 73 (LCB), H. Toffolo 72 (LWB), S. Cook 72 (CB), N. Williams 71 (RWB) |
| 15 | Leicester City | 8 | 30 | M. Upson 72 (SUB→LB), M. Wasilewski 71 (SUB→LCB), D. Simpson 73 (SUB→RB), E. Cambiasso 78 (SUB→LCM), D. Drinkwater 70 (SUB→CM), N. Powell 69 (SUB→RCM), A. Knockaert 70 (SUB→LW), M. Albrighton 71 (SUB→RW) | D. Nugent 71 (RS), L. Moore 69 (LCB), R. Mahrez 69 (RM), R. De Laet 69 (RB), A. King 68 (RCM), P. Konchesky 68 (LB), D. Hammond 67 (LCM), J. Schlupp 63 (LM) |
| 22 | Watford | 8 | 25 | B. Foster 78 (SUB→GK), D. Rose 75 (SUB→LB), C. Kabasele 75 (SUB→LCB), Kiko Femenía 75 (SUB→RB), J. Kucka 77 (SUB→LCM), O. Tufan 76 (SUB→CM), J. King 75 (SUB→LW), Cucho Hernández 75 (SUB→ST) | E. Dennis 74 (ST), A. Masina 74 (LB), T. Cleverley 74 (LCM), K. Sema 73 (LM), F. Sierralta 72 (LCB), O. Etebo 72 (CDM), C. Cathcart 72 (RB), D. Bachmann 70 (GK) |
| 24 | Nottingham Forest | 8 | 25 | O. Vlachodimos 81 (SUB→GK), Nuno Tavares 76 (SUB→LB), Felipe 78 (RES→LCB), M. Niakhaté 77 (SUB→RCB), G. Montiel 79 (SUB→RB), I. Sangaré 81 (SUB→CM), N. Domínguez 77 (SUB→RCM), C. Hudson-Odoi 75 (SUB→RW) | S. Aurier 78 (RWB), M. Turner 77 (GK), W. Boly 76 (RCB), R. Yates 75 (RCM), J. Worrall 74 (CB), A. Elanga 73 (RW), S. McKenna 73 (LCB), O. Aina 73 (LWB) |
| 15 | Aston Villa | 7 | 25 | R. Vlaar 79 (SUB→LCB), C. Clark 73 (RES→RCB), M. Lowton 73 (SUB→RB), C. Sánchez 76 (SUB→CM), C. N'Zogbia 75 (SUB→LW), C. Benteke 80 (SUB→ST), J. Cole 74 (SUB→RW) | A. Weimann 73 (RS), K. Richardson 73 (CAM), G. Agbonlahor 73 (LS), A. Westwood 72 (CDM), P. Senderos 72 (RCB), N. Baker 71 (LCB), A. Hutton 71 (RB) |
| 23 | FC Augsburg | 7 | 23 | F. Uduokhai 75 (SUB→RCB), R. Oxford 76 (SUB→RB), J. Baumgartlinger 76 (SUB→LCM), N. Dorsch 77 (RES→CM), A. Maier 76 (SUB→RCM), R. Vargas 75 (SUB→LW), D. Caligiuri 75 (SUB→RW) | F. Niederlechner 74 (RS), M. Berisha 73 (LS), E. Demirović 73 (LM), E. Rexhbeçaj 73 (LDM), C. Gruezo 72 (RDM), M. Bauer 71 (RCB), R. Gumny 71 (RB) |
| 17 | Sevilla | 7 | 16 | S. Sirigu 82 (SUB→GK), B. Trémoulinas 81 (SUB→LB), Daniel Carriço 81 (SUB→RCB), Mariano 79 (SUB→RB), M. Krohn-Dehli 82 (SUB→CM), F. Vázquez 82 (SUB→ST), Vitolo 82 (SUB→RW) | T. Kolodziejczak 80 (LCB), Sergio Rico 80 (GK), W. Ben Yedder 80 (RS), L. Vietto 79 (LS), H. Kiyotake 79 (CAM), Pablo Sarabia 78 (RM), N. Pareja 77 (RCB) |
| 15 | SC Freiburg | 6 | 40 | Torrejón 72 (SUB→LCB), S. Mitrović 72 (SUB→RCB), M. Mujdža 72 (SUB→RB), S. Riether 75 (SUB→CM), M. Frantz 72 (SUB→LW), A. Mehmedi 76 (SUB→ST) | C. Günter 70 (LB), F. Klaus 70 (LM), P. Krmaš 69 (RCB), K. Guédé 66 (RS), M. Kempf 63 (LCB), M. Philipp 61 (LS) |
| 19 | Lille | 6 | 35 | V. Enyeama 76 (RES→GK), A. Soumaoro 74 (SUB→LCB), Edgar Ié 74 (SUB→RB), Thiago Mendes 76 (SUB→CM), Thiago Maia 75 (SUB→RCM), Luiz Araújo 74 (SUB→LW) | M. Maignan 75 (GK), Xeka 73 (LDM), J. Bamba 71 (LM), Z. Çelik 66 (RB), Gabriel 66 (LCB), B. Soumaré 63 (RDM) |
| 21 | Fulham | 6 | 34 | A. Areola 82 (SUB→GK), K. Tete 77 (SUB→RB), M. Lemina 77 (SUB→LCM), J. Seri 77 (RES→CM), A. Zambo Anguissa 77 (SUB→RCM), A. Knockaert 74 (SUB→RW) | T. Cairney 76 (LDM), M. Rodák 74 (GK), H. Reed 73 (RDM), T. Ream 70 (LCB), N. Kebano 70 (RM), J. Onomah 67 (CAM) |

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
| 15 | 15/teams.json | 252.6 | 46.9 |
| 16 | 16/teams.json | 252.8 | 47.2 |
| 17 | 17/teams.json | 252.6 | 47.3 |
| 18 | 18/teams.json | 252.8 | 47.4 |
| 19 | 19/teams.json | 253.5 | 47.9 |
| 20 | 20/teams.json | 252.4 | 47.4 |
| 21 | 21/teams.json | 247.6 | 46.5 |
| 22 | 22/teams.json | 252.8 | 47.6 |
| 23 | 23/teams.json | 252.6 | 47.5 |
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
| LCM | Neymar Jr | LW, CAM | 91 | LW | natural |
| CM | M. Verratti | CM, CAM | 87 | LCM | natural |
| RCM | G. Wijnaldum | CM, CDM | 84 | RCM | natural |
| LW | Á. Di María | RW, LW | 87 | SUB | natural |
| ST | K. Mbappé | ST, LW | 91 | ST | natural |
| RW | L. Messi | RW, ST, CF | 93 | RW | natural |

### EA SPORTS FC 24 — Real Madrid (EA formation 4-4-2)

| slot | name | positions | ovr | eaPos | fit |
|---|---|---|---|---|---|
| GK | T. Courtois | GK | 90 | SUB | natural |
| LB | D. Alaba | CB, LB | 85 | LCB | natural |
| LCB | Éder Militão | CB | 86 | SUB | natural |
| RCB | A. Rüdiger | CB | 85 | RCB | natural |
| RB | Nacho Fernández | CB, LB, RB | 83 | SUB | natural |
| LCM | L. Modrić | CM | 87 | SUB | natural |
| CM | T. Kroos | CM, CDM | 86 | SUB | natural |
| RCM | J. Bellingham | CM, CAM | 86 | CAM | natural |
| LW | Vini Jr. | LW | 89 | SUB | natural |
| ST | Rodrygo | RW, LW, ST | 85 | RS | natural |
| RW | F. Valverde | CM, RW | 88 | RCM | natural |

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
| LB | D. Blind | CDM, LB, CM | 80 | LCB | natural |
| LCB | M. Rojo | CB, LB | 81 | LB | natural |
| RCB | P. Jones | CB, RB | 80 | SUB | natural |
| RB | M. Darmian | RB, RWB, LWB | 81 | RB | natural |
| LCM | M. Schneiderlin | CDM, CM | 82 | LDM | natural |
| CM | B. Schweinsteiger | CM, CDM | 86 | SUB | natural |
| RCM | Ander Herrera | CM, CAM | 81 | SUB | natural |
| LW | M. Depay | LW, CAM | 81 | LM | natural |
| ST | W. Rooney | ST, CM, CAM | 86 | CAM | natural |
| RW | Juan Mata | RM, CAM | 84 | RM | natural |

