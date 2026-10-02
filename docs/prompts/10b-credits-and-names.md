Stage 10b — Small fixes after stage 10. Read `docs/DECISIONS.md` D57–D59 and `docs/reports/10-add-fc25-27.md`.
`docs/DECISIONS.md`, `docs/BACKLOG.md` and this prompt were updated in the planning session: commit them as-is.

1. Credits (D58): replace the footer's second line with
   "Ratings: SoFIFA and EA SPORTS FC ratings data, via public Kaggle datasets."
   Keep the first line ("Fan project — not affiliated with EA SPORTS.") unchanged. In `README.md`, list all four
   datasets with links (FIFA 15–FC 24: stefanoleone992; FC 25: nyagami; FC 26: rovnez; FC 27: mikedpad).
2. Name overrides (D59): add `pipeline/name_overrides.py` — an explicit `{(version, player_id): display name}`
   table applied after the name rule, used by the EA-format loaders. Start with Son in FC 25 (→ "Son"). Then list
   every FC 25 / FC 27 best-XI player whose generated `name` differs from his `short_name` in our FC 24 or FC 26
   SoFIFA data (same `player_id`), review them, and add overrides only where ours is clearly worse (e.g. split
   Korean/Japanese/Brazilian names). Put the full before/after list in the report.
3. Rebuild, `validate.py`, pytest, app tests; FIFA 15–FC 26 files must not change except where an override applies
   (FC 26 should not change at all).
4. Report: add a "10b" section to `docs/reports/10-add-fc25-27.md`. Commit, push, confirm the deploy succeeded and
   the live footer shows the new text.
