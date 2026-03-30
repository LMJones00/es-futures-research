# Project Notes

## Session 1 — 2026-03-30

### What We Did
1. **Explored all 4 notebooks** — Claude read every cell and produced a full audit of the pipeline: inputs, outputs, issues, and improvement opportunities.
2. **Created `CLAUDE.md`** — Project documentation file that Claude reads at the start of every session so it always has full context without needing to re-explain things.
3. **Created `.gitignore`** — Tells git to ignore all CSV and Excel data files (they're too large and should not be in version control), as well as credentials, checkpoints, and virtual environments.
4. **Created `requirements.txt`** — Lists all Python packages the project depends on so the environment can be recreated on any machine.
5. **Initialized git** — The `Nadex Code/` folder is now a git repository. First commit `aec8d07` saved.

---

### Platform Note: Nadex Status
Nadex (the binary options platform this project was originally built for) **is still operating**. It was acquired by **IG Group** but continues to run at **nadex.com** under the Nadex brand. It still offers binary options and bull spreads on US indices including the S&P 500.

**Action:** Log into nadex.com to verify your account is still active. If Nadex is no longer viable for you, the strategy logic maps cleanly to **MES (Micro E-mini S&P 500) futures via IBKR** — your existing connection — as a standard long/short trade.

---

### How to Push to GitHub (Fix for Terminal Error)

The `!` prefix only works inside the **Claude Code chat input**, not in a regular terminal window. For a regular terminal (PowerShell or Command Prompt), run these commands directly:

**Step 1 — Check if GitHub CLI is installed:**
```
gh --version
```

If you get an error, install it from: https://cli.github.com

**Step 2 — Authenticate (one time only):**
```
gh auth login
```
Follow the prompts to log in to GitHub.

**Step 3 — Create the repo and push:**
```
cd "C:\Users\lmjsp\Desktop\Claude Code Test\Nadex Code"
gh repo create nadex-strategy --private --source . --push
```

If you prefer to skip the CLI and use the GitHub website:
1. Go to github.com → New repository → name it `nadex-strategy` → Private → Create
2. Then in your terminal run:
```
cd "C:\Users\lmjsp\Desktop\Claude Code Test\Nadex Code"
git remote add origin https://github.com/YOUR_USERNAME/nadex-strategy.git
git push -u origin master
```

---

### Known Issues Found in the Notebooks (Phase 2 To-Do)

| Priority | File | Issue |
|---|---|---|
| HIGH | `barsToCleaning.ipynb` | `.iterrows()` loop for `contract_location` — very slow; replace with `np.select()` |
| HIGH | `barsToCleaning.ipynb` | `secs.iloc[1140:]` magic number — replace with `volume > 0` filter |
| HIGH | `preparing.ipynb` | 6 duplicate `determine_direction()` functions — consolidate into vectorized `np.where()` |
| HIGH | `preparing.ipynb` | Typo: `column_name="'diff_open_conLoc"` — extra quote causes KeyError |
| MED | `gettingData.ipynb` | Hardcoded contract month, dates, file names — move to CONFIG block |
| MED | `barsToCleaning.ipynb` | Holiday dates hardcoded with no explanation — document and move to config |
| MED | `cleaingToClean.ipynb` | No validation if 16:00/16:15 close bars are missing for a date |
| LOW | All notebooks | No data validation after each step — add row counts and range checks |

---

### External Data Planned (Phase 3+)

- **VIX** — Free via `yfinance`, no API key needed. Adds market volatility context. Going in next.
- **Oil (CL futures)** — Via existing IBKR connection. Shows oil/ES correlation.
- **Geopolitical sentiment** — GDELT (free) or NewsAPI (~$50/mo) for war/conflict news scoring.
