Stage 07 — Polish + deploy to GitHub Pages. Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md` (especially
D10, D42 = rejected, D43, D44) and `docs/reports/06-card-design.md` first. `docs/PLAN.md`, `docs/DECISIONS.md`
and this prompt were updated in the planning session: commit them as-is.

Goal: the game is live on a public URL and playable on a phone.

1. Polish
   - Footer on the setup and end screens (small, unobtrusive): "Fan project — not affiliated with EA SPORTS.
     Ratings: SoFIFA data via Kaggle (EA Sports FC 24 complete player dataset)." (D44)
   - `index.html`: a proper `<title>` ("OG Squad Compare"), meta description, theme colour, and basic Open Graph
     tags (title, description). No external images or fonts.
   - Root `README.md`: what the game is, how to rebuild the data (download the Kaggle files into
     `data/raw/FIFA 15-24/`, then `build.py` + `validate.py`), how to run the app locally, how deployment works,
     and a link to the live site (fill in once known).

2. Deployment workflow
   - Add `.github/workflows/deploy.yml`: on push to the default branch (check whether it is `master` or `main`
     and use that) and on manual dispatch: checkout, setup Node (the version used locally), `npm ci` in `app/`,
     `npm test`, `npm run build`, then deploy `app/dist` with the official Pages actions
     (`actions/upload-pages-artifact` + `actions/deploy-pages`), with the required permissions and concurrency.
   - The app already uses `base: './'`; confirm the built site works from a sub-path (`/<repo>/`) by running
     `npm run preview` with a matching base or an equivalent check.

3. GitHub repository (these are outward-facing steps — tell me before each one runs)
   - Check whether the GitHub CLI (`gh`) is installed and authenticated (`gh auth status`).
   - If yes: create a PUBLIC repository `og-squad-compare` under my account, add it as `origin`, push, and enable
     Pages with "GitHub Actions" as the source (e.g. `gh api` on `repos/{owner}/{repo}/pages` with
     `build_type=workflow`). Then watch the workflow run until it finishes (`gh run watch`).
   - If `gh` is missing or not logged in: stop before this step and write exact, copy-paste instructions for me
     (install/login, or create the repo on github.com, the `git remote add` / `git push` commands, and where to
     switch Pages to "GitHub Actions" in the repo settings).
   - Make sure `data/raw/`, `node_modules/`, `dist/` and `.venv/` are not pushed (check with `git ls-files`).

4. Verify
   - Once deployed: fetch the live URL and a data file (e.g. `.../data/versions.json`) and confirm HTTP 200.
   - If Playwright is available, play one full game against the live URL at 375 px and save a screenshot of the
     end screen to `docs/reports/07-screens/`.

5. Report `docs/reports/07-deploy.md`: what was done, files, the live URL, how to redeploy (just push), open
   issues, assumptions. Commit (and push) at the end with a clear message.
