# Stage 07 report — Polish + deploy to GitHub Pages

## Status

**The site is not live yet.** The GitHub CLI (`gh`) is not installed on this machine. `gh` is not on `PATH` in
Bash or PowerShell, and it is not in `C:\Program Files\GitHub CLI\` or `%LOCALAPPDATA%\Programs\GitHub CLI\`.
As the stage prompt instructs, I stopped before step 3 and did nothing outward-facing:

- no repository was created;
- no remote was added;
- nothing was pushed.

Everything else is done and committed locally. The exact commands to go live are in
[Go live: steps for you](#go-live-steps-for-you) below. After that, steps 3–4 (watching the run, checking the live
URL, and a Playwright game against it) can be completed in a follow-up.

## What was done

1. **Planning docs** (`docs/PLAN.md`, `docs/DECISIONS.md` D42–D44, this prompt) were committed as-is in `b431c5e`.
2. **Polish**
   - **Footer** (D44) on the setup and end screens (`components/Footer.tsx`): "Fan project — not affiliated with
     EA SPORTS." and "Ratings: SoFIFA data via Kaggle (EA Sports FC 24 complete player dataset)." It is small,
     muted and centred at the bottom. The setup screen is now at least one viewport tall, so the footer sits at
     the bottom.
   - **`index.html`:**
     - `<title>OG Squad Compare</title>`, a meta description and `theme-color`;
     - Open Graph `og:type`, `og:title` and `og:description`, plus `twitter:card=summary`;
     - no external images or fonts. The favicon is the local SVG.
   - **Root `README.md`:** what the game is, the repository layout, how to rebuild the data, how to run the app,
     and how deployment works. The Kaggle link resolves. The live URL is a placeholder until the repository exists.
3. **Deployment workflow**: `.github/workflows/deploy.yml`.
   - **Triggers:** push to **`master`** (the default branch here) and `workflow_dispatch`.
   - **Permissions:** `contents: read`, `pages: write`, `id-token: write`.
   - **Concurrency:** group `pages`, `cancel-in-progress: false`.
   - **`build` job:**
     - `actions/checkout@v7`;
     - `actions/setup-node@v7` with Node **22.19.0** (the local version) and the npm cache keyed on
       `app/package-lock.json`;
     - `npm ci`, `npm test` and `npm run build` in `app/`;
     - `actions/configure-pages@v6`, then `actions/upload-pages-artifact@v5` with `app/dist`.
   - **`deploy` job:** `actions/deploy-pages@v5` in the `github-pages` environment, with the page URL as the
     environment URL.
   - **Action versions:** these are the latest major tags (read with `git ls-remote`). I checked every input I use
     against each action's `action.yml`.
   - **Linux install:** the lockfile already contains the Linux native bindings (rolldown, oxlint, lightningcss),
     so `npm ci` works on `ubuntu-latest`.
4. **Sub-path check**
   - I served the production build under `/og-squad-compare/` with `vite preview --base /og-squad-compare/`. That
     is the same path GitHub Pages will use.
   - `/og-squad-compare/`, `data/versions.json`, `data/24/teams.json` and `favicon.svg` all returned HTTP 200.
   - A Playwright full game ran at 375 px through that sub-path: FC Barcelona FIFA 15 vs Real Madrid FIFA 17.
     **17/17 checks passed:**
     - the page title is right;
     - the footer appears on the setup and end screens;
     - flags loaded in all 11 rounds, with no broken images;
     - there were **no failed requests** and no console errors.
   - This confirms that the relative `base: './'` works for scripts, CSS, data fetches and the lazily loaded flag
     SVGs.
   - Note for Git Bash users: MSYS rewrites `/og-squad-compare/` into a Windows path. Run such commands with
     `MSYS_NO_PATHCONV=1`, or from PowerShell.
5. **What gets pushed**
   - `git ls-files` contains no `data/raw`, `node_modules`, `dist`, `.venv`, `__pycache__` or `.pytest_cache`
     paths.
   - `git check-ignore` confirms that `data/raw/…`, `app/node_modules`, `app/dist` and `pipeline/.venv` are
     ignored.
   - The repository is about 7 MB without ignored folders and history, mostly the committed game data and report
     screenshots.
6. **Checks:** `npm run build`, `npm run lint` (0 warnings), `npm test` (37 passed), `pytest` (19 passed) and
   `validate.py` all pass.

## Go live: steps for you

You can do this either with the GitHub CLI (option A) or on github.com (option B). Run the commands from the
repository root: `C:\Users\RazCohen\Private\fun\FIFA - OG squad compare`.

### Option A: GitHub CLI

```powershell
# 1. Install and log in (one time)
winget install --id GitHub.cli
# Open a NEW terminal so gh is on PATH, then:
gh auth login          # GitHub.com → HTTPS → log in with a browser

# 2. Create the PUBLIC repo and add it as "origin" (no push yet)
gh repo create og-squad-compare --public --source . --remote origin

# 3. Turn on Pages with "GitHub Actions" as the source
gh api -X POST "repos/{owner}/{repo}/pages" -f build_type=workflow

# 4. Push; this starts the deploy workflow
git push -u origin master

# 5. Watch the run until it finishes
gh run watch
```

### Option B: github.com in the browser

1. Go to <https://github.com/new>. Set the repository name to `og-squad-compare` and visibility to **Public**. Do
   **not** add a README, .gitignore or license, because the repo must start empty. Click **Create repository**.
2. In a terminal, from the repository root:

   ```powershell
   git remote add origin https://github.com/<your-github-username>/og-squad-compare.git
   git push -u origin master
   ```

3. On GitHub, open the repo, then **Settings → Pages → Build and deployment → Source** and choose
   **GitHub Actions**.
4. Open the **Actions** tab. If the first "Deploy to GitHub Pages" run failed because Pages was not enabled yet,
   open it and click **Re-run all jobs**. You can also start a new run with **Run workflow**.

### After deployment

- The site will be at **`https://<your-github-username>.github.io/og-squad-compare/`**.
- Put the real URL in `README.md`, in the "Play it" line, and push.
- Tell me when it is live, and I'll finish steps 3–4: confirm HTTP 200 for the page and `data/versions.json`, and
  play a full game against the live URL at 375 px with a screenshot in `docs/reports/07-screens/`.
- D43 notes that free GitHub Pages needs a **public** repository. Everything in this repo is safe to publish.
  The raw Kaggle files are ignored, and the committed data holds only the generated XIs.

## How to redeploy

Push to `master`. The workflow tests, builds and deploys on its own. To redeploy without a code change, use
**Actions → Deploy to GitHub Pages → Run workflow**, or run `gh workflow run deploy.yml` with the CLI.

## Files

Created:
- `.github/workflows/deploy.yml`
- `README.md`
- `app/src/components/Footer.tsx` and `Footer.module.css`
- `docs/reports/07-deploy.md`

Changed:
- `app/index.html`: title, description, theme colour, Open Graph and Twitter card.
- `app/src/components/SetupScreen.tsx` and `.module.css`: footer; the screen fills at least the viewport.
- `app/src/components/EndScreen.tsx`: footer.

Deleted: none.

## Open issues

1. **Not deployed** because `gh` is missing. The steps above take a few minutes.
2. **The live URL is a placeholder** in `README.md` until the repository exists. I don't know your GitHub username
   for certain. The local git author name is `RazCohen11`, but that may not be your GitHub account.
3. **Safari / iPhone** is still untested, as PLAN stage 7 notes. The 3D flip (`preserve-3d`,
   `backface-visibility`) and the Web Animations fly are the parts most worth checking on a real iPhone.
4. **The first workflow run may fail at the deploy step** if Pages is not enabled before the first push (option B).
   Re-running fixes it. Option A avoids this by enabling Pages before the push.
5. **The deploy uploads all 271 flag SVGs**, about 5.5 MB in total with the data (from stage 06). Players only
   download what they see.

## Assumptions not in the prompt

- The default branch is `master`: it is both the current branch and git's `init.defaultBranch` here, and the
  workflow triggers on it.
- I pinned Node exactly to the local `22.19.0`, rather than `22.x`, to match "the version used locally".
- The workflow does not run `npm run lint`. The prompt lists `npm ci`, `npm test` and `npm run build`, and the
  build already type-checks.
- I added `actions/configure-pages` before the upload. It is the officially recommended step. I left it without
  `enablement: true`, because the default `GITHUB_TOKEN` cannot turn Pages on, so that stays a one-time manual step.
- I added a `twitter:card` tag to the Open Graph tags. There is no `og:image`, because the brief says no external
  images and there is no own artwork.
- The footer text uses an em dash, exactly as in the prompt.
