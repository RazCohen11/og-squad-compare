# OG Squad Compare

A single-player browser guessing game. Pick two clubs, each from any game between **FIFA 15** and
**EA SPORTS FC 24** (for example, FC Barcelona FIFA 15 vs Real Madrid FIFA 17). Each club's best XI is laid
out on a 4-3-3 pitch. Slot by slot, you see both players with their ratings hidden and guess who had the higher
Ultimate Team base rating, or whether they were equal. The card with the higher rating drops into the slot, and
after 11 rounds you get your score and the combined XI.

**Play it:** https://razcohen11.github.io/og-squad-compare/

Fan project: not affiliated with EA SPORTS. Ratings: SoFIFA data via Kaggle
([EA Sports FC 24 complete player dataset](https://www.kaggle.com/datasets/stefanoleone992/ea-sports-fc-24-complete-player-dataset)).

## Repository layout

```
app/        Vite + React + TypeScript web app (static, no backend)
  public/data/   Generated game data (committed): versions.json, <version>/teams.json
pipeline/   Python scripts that turn the raw CSVs into app/public/data
data/raw/   Downloaded Kaggle files (not committed)
docs/       Plan, decision log, stage prompts and reports
```

## Rebuild the game data

You only need to do this to change the data. The generated JSON is already committed.

1. Download the Kaggle dataset linked above (you need a Kaggle account). Put `male_players.csv` and
   `male_teams.csv` into `data/raw/FIFA 15-24/`. The folder name includes the space.
2. Create the Python environment (Python 3.11+):

   ```bash
   python -m venv pipeline/.venv
   pipeline/.venv/Scripts/python -m pip install -r pipeline/requirements.txt   # Windows
   # pipeline/.venv/bin/python -m pip install -r pipeline/requirements.txt    # macOS / Linux
   ```

3. From the repository root, build and validate:

   ```bash
   pipeline/.venv/Scripts/python pipeline/build.py      # writes app/public/data/
   pipeline/.venv/Scripts/python pipeline/validate.py   # exits non-zero on any problem
   pipeline/.venv/Scripts/python -m pytest pipeline/tests -q
   ```

The rules behind the data are in `docs/PLAN.md` §3 and `docs/DECISIONS.md`. In short, each club gets its best 11
players from the whole launch-roster squad, and each player is placed only in a position they are listed for.

## Run the app locally

Requires Node.js 22 (developed with 22.19.0).

```bash
cd app
npm install
npm run dev        # http://localhost:5173
npm test           # unit tests (Vitest)
npm run lint
npm run build      # type-check + production build into app/dist
npm run preview    # serve the production build
```

## Deployment

The site is hosted on GitHub Pages and deployed by `.github/workflows/deploy.yml`:

- Every push to `master`, or a manual run from the Actions tab, installs dependencies (`npm ci`), runs the
  tests, builds `app/`, and publishes `app/dist` with the official Pages actions.
- To redeploy, push to `master`.
- The app uses relative paths (`base: './'`), so it works from the `/og-squad-compare/` sub-path without any
  configuration.
- One-time setup: in the repository settings, under **Pages → Build and deployment → Source**, choose
  **GitHub Actions**.
