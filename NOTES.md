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

### Known Issues — Status

| Priority | File | Issue | Status |
|---|---|---|---|
| HIGH | `barsToCleaning.ipynb` | `.iterrows()` loop for `contract_location` — slow | FIXED (commit f39bf8b) |
| HIGH | `barsToCleaning.ipynb` | `secs.iloc[1140:]` magic number | DOCUMENTED (commit f39bf8b) |
| HIGH | `barsToCleaning.ipynb` | Holiday dates hardcoded with no explanation | FIXED (commit f39bf8b) |
| HIGH | `preparing.ipynb` | 6 duplicate `determine_direction()` functions | FIXED (commit 69d5eb5) |
| HIGH | `preparing.ipynb` | Typo: `column_name="'diff_open_conLoc"` — extra quote causes KeyError | FIXED (commit 69d5eb5) |
| HIGH | `preparing.ipynb` | Nested for-loop streak functions — slow | FIXED (commit 69d5eb5) |
| MED | `gettingData.ipynb` | Hardcoded contract month, dates, file names | PENDING |
| MED | `cleaingToClean.ipynb` | No validation if 16:00/16:15 close bars are missing | PENDING |
| LOW | All notebooks | No data validation after each step — add row counts | PENDING |

---

---

## Session 2 — 2026-03-31

### What We Did
1. **Enhanced `barsToCleaning.ipynb`** (commit `f39bf8b`) — 5 changes:
   - Vectorized the `.iterrows()` `contract_location` loop using `np.select()` (~100x faster)
   - Vectorized `day_of_week` using `pd.DatetimeIndex.dt.day_name()` instead of a lambda loop
   - Vectorized `initial_direction` using `np.where()` instead of an `.apply()` function
   - Documented the magic number `1140` with an explanation and a more robust alternative
   - Moved holiday dates to `EXCLUDED_DATES` with a comment for each date and a CME calendar link

2. **Enhanced `preparing.ipynb`** (commit `69d5eb5`) — 10 changes:
   - Replaced all 6 `determine_direction()` functions with `np.where()` or direct `.abs()` math
   - Added NaN validation before `money_made` so you know when contract data is missing
   - Documented SDV bins in both `categorize_*` functions (bins shift as data grows)
   - Fixed typo: `column_name="'diff_open_conLoc"` had an extra quote that caused a KeyError
   - Replaced nested `for` loop streak functions with a vectorized cumsum approach

3. **Configured the context % statusline** — now visible at the bottom of the terminal

---

### What You Learned: Vectorization

**The core idea:** Instead of Python visiting each row one at a time (like a cashier scanning items individually), vectorized code hands the entire column to NumPy — which processes all rows at once using optimized C code under the hood.

**Three tools used:**
- `np.where(condition, value_if_true, value_if_false)` — like Excel's IF(), but for a whole column at once. Can be nested for multiple conditions.
- `np.select(conditions_list, choices_list, default)` — like a vectorized if/elif/else chain. Used for `contract_location`.
- `series.abs()` and direct column math (`col_a - col_b`) — no function needed at all for simple differences.

**Why it matters for your data:** With 30,000+ rows, the `.iterrows()` loop for `contract_location` alone was visiting each row individually with Python overhead. `np.select()` processes all 30,000 in one operation.

---

### What You Learned: The Cumsum Streak Trick

Counting consecutive wins/losses (streaks) without a loop uses this pattern:

```python
mask = series == 'yes'           # True where there's a win
group_ids = (~mask).cumsum()     # Increments every time we're NOT winning -> labels each streak run
streak = mask * (mask.groupby(group_ids).cumcount() + 1)
```

Example for `[yes, yes, no, yes, yes, yes, no]`:
- mask:      `[T, T, F, T, T, T, F]`
- ~mask:     `[F, F, T, F, F, F, T]`
- cumsum:    `[0, 0, 1, 1, 1, 1, 2]`  ← group ID increments at each break
- cumcount within group × mask: `[1, 2, 0, 1, 2, 3, 0]` ✓

The key insight: `cumsum` of NOT-mask creates a unique ID for each consecutive run — no loop needed.

---

### External Data Planned (Phase 3+)

- **VIX** — Free via `yfinance`, no API key needed. Adds market volatility context. Going in next.
- **Oil (CL futures)** — Via existing IBKR connection. Shows oil/ES correlation.
- **Geopolitical sentiment** — GDELT (free) or NewsAPI (~$50/mo) for war/conflict news scoring.
