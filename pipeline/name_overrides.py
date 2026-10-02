"""Manual display-name fixes (D59), applied after the automatic name rule in the EA-format loaders (FC 25, FC 27).

Only for names where the rule is clearly worse than the name players know. Each entry was reviewed in stage 10b
against the player's SoFIFA short_name (FC 26 or FC 24, same player_id). Kept as rule output, on purpose: a plain
"F. Lastname" style difference ("J. Navas" vs "Jesús Navas") and EA's own common names in FC 27 ("Cala", "Puga").

build.py fails if an entry no longer matches a player of a top-5 club in its version, so stale entries cannot linger.
"""

# (version, player_id) -> display name
NAME_OVERRIDES: dict[tuple[int, int], str] = {
    # East Asian name order split as Western first/last
    (25, 200104): "Son",  # Rule: "H. Min Son" (EA name "Heung Min Son")
    (25, 244108): "Hong Hyeon Seok",  # Rule: "H. Hyeon Seok"
    # A particle or a second given name taken as part of the surname
    (25, 190149): "De Marcos",  # Rule: "D. Marcos"
    (25, 195272): "M. Faraoni",  # Rule: "M. Davide Faraoni"
    (25, 212382): "P. Onuachu",  # Rule: "P. Ebere Onuachu"
    (25, 216460): "J. Giménez",  # Rule: "J. María Giménez"
    (25, 251870): "J. Cabal",  # Rule: "J. David Cabal"
    (25, 257136): "O. Traoré",  # Rule: "O. Haktab Traoré"
    (25, 266256): "A. Adams",  # Rule: "A. Jerome Adams"
    (27, 265195): "E. Jelert",  # Rule: "E. Jelert Kristensen"
    # The second name is a given name or a nickname, not a surname
    (25, 204614): "Mário Rui",  # Rule: "M. Rui"
    (25, 251675): "Douglas Augusto",  # Rule: "D. Augusto"
    (25, 224458): "Diogo Jota",  # Rule: "D. Jota"
    # Brazilian / Portuguese players known by both names (as SoFIFA writes them)
    (25, 233927): "Lucas Paquetá",  # Rule: "L. Paquetá"
    (25, 251445): "Samuel Lino",  # Rule: "S. Lino"
    (25, 187598): "Rafael Tolói",  # Rule: "R. Tolói"
    (25, 207566): "William Carvalho",  # Rule: "W. Carvalho"
}
