# OG Squad Compare — project context for Claude Code

## What we are building
A browser guessing game. The player picks a FIFA/FC game version (year) and two clubs.
Both clubs' in-game starting XIs are laid out on a pitch, slot by slot. For each slot the
player sees two cards (one per club) WITHOUT rating and stats, and guesses which player has
the higher Ultimate Team base rating. The answer is revealed, the higher-rated card (fully
revealed) drops into the slot on the pitch, and the game moves to the next slot.

## How work is organised
- Planning and decisions happen in a separate planning session. You receive one stage prompt at a time.
- Source of truth for scope: `docs/PLAN.md`. Decision log: `docs/DECISIONS.md`. Do not contradict
  a logged decision; if you think one is wrong, say so in your report instead of changing it.
- At the end of every stage, write a report to `docs/reports/<stage-id>.md` containing:
  what was done, files created/changed/deleted, how to run/verify it, open issues, and anything
  you assumed that was not in the prompt.
- Do only what the stage prompt asks. No speculative features.

## Conventions
- Code comments: English only, each comment starts with a capital letter.
- Data pipeline: Python 3 (pandas). Web app: Vite + React + TypeScript, static build, no backend.
- Raw data lives in `data/raw/` and is NEVER committed (it is large). Generated app data lives in
  `app/public/data/` and IS committed.
- Keep the app fully static: no login, no server, no persistence beyond the page session.

## Repository layout (target)
```
CLAUDE.md
docs/        PLAN.md, DECISIONS.md, prompts/, reports/
data/raw/    Downloaded source datasets (gitignored)
pipeline/    Python scripts that turn raw data into app JSON
app/         Vite + React + TS web app
```
