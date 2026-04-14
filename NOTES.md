# Project Notes

## Session 14 — 2026-04-14

### What We Did

1. **Fixed SyntaxError in `analysis.ipynb` Cell 89 (Section 19b)**
   - A literal newline character was embedded inside a single-quoted f-string in `ax.set_title(...)`, split across two JSON source entries. Caused `SyntaxError: unterminated f-string literal` even on Python 3.14.
   - Fixed by merging the two source lines and replacing the literal newline with `\n` (the two-character escape sequence). All 91 cells now pass `ast.parse()`.

2. **Reviewed Section 19 results — OTM contract win rate:**
   - OTM strike = near-money contract ± 12 pts (one Nadex daily interval further in trade direction)
   - Best filter (Strong drift + non-Q4 + not-Thu): **66.7% OTM win rate** on 39 days
   - EV at realistic OTM entry prices: **+$17 to +$47/trade** (vs +$1.9/trade for near-money)
   - Median close is 18.5 pts past the near-money contract; OTM is only 12 pts further — most winning days already clear the OTM bar
   - Critical unknown: actual Nadex OTM prices at 10am on signal days unverified — must observe live before trading

3. **Reviewed Section 17 results — Intraday retracement:**
   - 100% of the 39 best-signal days had some retrace past the contract level after 10am
   - 76.9% still won despite those retraces — deep intraday counter-moves are normal, not predictive of losses
   - Median retrace: 21.2 pts (350% of open-to-contract gap); mean 33.9 pts
   - **Key implication:** Cannot use a stop at the contract level for futures — would stop out 100% of trades. Need MAE analysis to find a viable stop level.

4. **Reviewed Section 18 results — Pre-market VIX predictability:**
   - VIX r=0.685 with first-30-min range (strong predictor of morning volatility)
   - Elevated VIX (25–35) on calendar-passing days: 29.2% chance of best-signal day (4x baseline)
   - Low VIX (<15): 2.8% — mostly skip. Moderate (15–25): 13.5% — watch normally.

5. **Updated `CLAUDE.md`** — added Sections 17–19 findings, updated cell count (79→91), updated execution decision to reflect OTM binary as a viable second path alongside futures.

6. **Wrote Section 19 interpretation** (cell 90) — EV comparison table, OTM decision framework, live-verification requirement for Nadex pricing.

### Key Finding

OTM binary changes the Nadex viability picture significantly. Near-money was +$1.9/trade (not worth it). OTM at realistic entry prices is +$17 to +$47/trade — but hinges on unverified live Nadex pricing.

### Next Steps
1. **Section 20: MAE/MFE stop-loss analysis** — uses bar-level `df` on 39 best-signal days to find viable stop placement for ES/MES futures. Produces stop-sweep EV table. This is the priority.
2. **Live signal script** — Python script to run at 10am daily: checks range width, drift magnitude, direction, fires alert if all conditions met.
3. **Paper trade + OTM price observation** — log actual Nadex OTM prices on signal days to verify the $20–50 assumption.
4. **Resume update** — user to attach resume; Claude to update it based on this project's findings and technical work.

---

## Session 13 — 2026-04-13

### What We Did

1. **Discussed binary pricing vs. directional edge**
   - Raw win rate (60.6–76.9%) looks strong but Nadex binary pricing absorbs it.
   - Breakeven rule: at win rate W%, you need to buy the binary for < W×$1. At 70%, binary must cost < $70.
   - On Wide+Reversal days, 84% of days are already past the contract by 10am → binary priced at ~$62–75 (ITM).
   - At Strong drift 69.8% win rate: breakeven price is $70. If ITM binary is $75+, EV is negative.
   - Two viable exits: (a) enter early (~9:30–9:45) while binary is fairly priced (~$50), or (b) switch to ES/MES futures where no pricing penalty exists.

2. **Discussed streak-based position sizing**
   - Streak data from Section 9 shows no reliable signal — after a 4-game loss streak, win rate is 44%; after 5 losses it drops to 21%. Small samples (N=8–28), noise not signal.
   - "Martingale-lite" on the 127-day subset would require computing streaks *within* the filter — and sample sizes would be even thinner.

3. **Added Section 15 — Binary Entry Price Model** (cells 70–74):
   - **15a:** Maps `progress_ratio` to estimated 10am binary entry price (5-tier model, conservative/buyer-favorable)
   - **15b:** P&L summary by filter tier — compares Breakeven Price vs Avg Estimated Price
   - **15c:** Price sensitivity table — EV at $45–$85 entry prices for each filter; plus line chart
   - **Interpretation cell:** Explains the two actionable paths (early entry vs futures)

### Key Finding

| Filter | Win Rate | Breakeven Price |
|---|---|---|
| Wide+Rev (all 127) | 60.6% | $61 |
| Strong drift | 69.8% | $70 |
| Strong + non-Q4 | 76.1% | $76 |
| Strong + non-Q4 + not Thu | 76.9% | $77 |

The edge is real directionally. Profitability on Nadex binaries depends entirely on whether you can buy below the breakeven price. Most 10am entries on ITM binaries are priced at $62–75 — borderline or negative EV. **Early entry or futures is the more direct path to capturing the edge.**

### Next Steps
1. **Run Section 15** (cells 71–73) — need full Sections 0–14 run first; see actual P&L and price sensitivity numbers
2. **Consider futures path** — map entry rule to ES/MES: same Wide+Reversal+Strong drift signal, enter short/long at 10am, fixed stop and target
3. **Build entry checklist** — exact thresholds for a trading rulebook (wide open > 18pts, drift > 16pts, not Q4, not Thursday)

---

## Session 12 — 2026-04-13

### What We Did

1. **Fixed `analysis.ipynb` — streak columns missing from `df_day`**
   - `overall_win_streak`, `overall_loss_streak`, `dow_win_streak`, `dow_loss_streak` exist in `clean.csv` but were not listed in `DAY_COLS` in cell 4 — so `df_day` never had them.
   - Fixed by adding all four columns to `DAY_COLS`. Section 9 (streak analysis) now runs correctly.

2. **Ran full pipeline** — `preparing.ipynb` then `analysis.ipynb` Sections 0–11. All ran cleanly.

3. **Core analysis results (Sections 0–11):**
   - Tradeable win rate: **37.0%** (p≈1.0 — no edge on raw signal)
   - Philosophical win rate: **41.8%**
   - Strike cost gap: **4.9%**
   - No filter combination (VIX, SDV, day-of-week) exceeded 50%
   - Best case (VIX fav + SDV tight): 43.9% on 75 trades/yr

4. **Added Section 12 — Early-Session Signal Analysis** (cells 38–52):
   - **12a:** Price range and max-away analysis (first 30 mins, all 507 days)
   - **12b:** Volume spike analysis (145-day subset only — Apr–Nov 2024)
   - **12c:** Combined signal — tight/wide open × drift direction
   - **12d:** Triple filter — wide open + early reversal + close to contract location

### Key Finding

The 37% overall win rate was masking two populations:

| Condition | Win rate | N |
|---|---|---|
| Wide open + early reversal | **60.6%** | 127 |
| Wide open, drift confirms | 26.0% | 127 |
| Tight open + early reversal | 43.2% | 95 |
| Tight open, drift confirms | 29.1% | 158 |

**Definitions:**
- **Wide open** = first-30-min price range > median (≈0.351% of open price, ~18pts on 5200 open)
- **Early reversal** = net price drift in first 30 mins is already pulling back against initial direction
- **Max-away** = how far price moved away from contract location in first 30 mins; clear monotonic decay (54.9% → 25.5% from closest to furthest quintile)

**Practical implication:** Wait until ~10:00 before entering. If the open was volatile AND price is already pulling back, that's the setup. Don't enter when the market is still running with the initial direction at 10:00.

Section 12d (triple filter adding distance-from-contract-location) was added but not yet evaluated — run it next session.

### Next Steps
1. Run Section 12d and review results
2. Define exact entry rule thresholds as a trading checklist
3. Update Section 10 filter constants and Section 11 conclusions
4. Decide whether to pursue news sentiment (n8n) as an additional signal layer

---

## Session 11 — 2026-04-13

### What We Did

1. **Fixed `analysis.ipynb` — broken f-string in `annotate_heatmap`**
   - The line `annot.loc[r, c] = f'{val:.0%}{flag}\n({n_val:.0f})'` had a literal newline character inside the f-string (split across two JSON source entries in the notebook), making it a syntax error.
   - Fixed by replacing the literal newline with `\n` (the two-character escape sequence). Heatmap annotations will still show `{pct}` on one line and `({N})` below it — behavior unchanged.
   - Pylance error: "String literal is unterminated" at line 45.

2. **Fixed `barsToCleaning.ipynb` — bad merge keys**
   - Cell 6 merged `barsCombined` (1-min bars) with `secs` (1-sec bars) using `on=['date', 'open', 'high', 'low', 'close', 'volume', 'average', 'barCount', 'time']`.
   - `NewGoodOldGoodOld.csv` only has `['date', 'open', 'high', 'low', 'close', 'volume', 'time']` — no `average` or `barCount` columns.
   - Fixed by removing `'average'` and `'barCount'` from the merge keys. Those columns survive the outer merge as NaN for 1-sec rows, which is correct.
   - Runtime error: `KeyError: 'average'`.

3. **Ran pipeline through `cleaingToClean.ipynb`** — `check_close_bar` produced expected warnings:
   - 25 dates missing both 16:15 and 16:00 close bars.
   - 17 are confirmed holidays or CME early-close days (Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, MLK Day, Presidents' Day, July 3 early-close, Black Friday, Christmas Eve).
   - 8 are suspected IBKR data gaps (2024-06-17, 2024-06-18, 2024-07-16, 2024-07-30, 2024-08-13, 2024-08-27, 2024-12-16, 2024-12-17) with no obvious holiday explanation.
   - Both close columns (`market_close_16:15`, `market_reg_close_16:00`) are NaN for the same 25 dates → those rows will be dropped by `dropna()` in analysis. Not a blocker.

4. **Confirmed Pylance false positive in `cleaingToClean.ipynb`** — `"cleaning" is not defined` (severity 4 warning). `check_close_bar` references `cleaning` as a global defined in a prior cell; Pylance can't trace cross-cell state. No fix needed.

### Current State (End of Session 11)

- `cleaning.csv` — produced by `barsToCleaning.ipynb` ✓
- `clean.csv`, `equal_rows.csv`, `open_rows.csv` — produced by `cleaingToClean.ipynb` ✓
- **Next:** Run `preparing.ipynb` (needs internet for VIX via yfinance), then `analysis.ipynb`

### Next Steps
1. Run `preparing.ipynb` — feature engineering, VIX integration (internet required)
2. Run `analysis.ipynb` — review all 11 sections
3. Update Section 10 filter constants (`BEST_DOW`, `BEST_SDV_BANDS`, `BEST_DIRECTION`) from analysis output
4. Fill in Section 11 conclusions table with real win rates and recommendation

---

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
| MED | `gettingData.ipynb` | Hardcoded contract month, dates, file names | FIXED (Session 4) |
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

---

## Session 3 — 2026-04-01

### What We Did
1. **Created `analysis.ipynb`** (commit `27f27dc`) — Full strategy validation notebook, 11 sections:
   - Section 0: Setup, data load, builds `df` (bar-level) and `df_day` (1 row/day)
   - Section 2: Core win rate with binomial test vs p=0.50, 95% CI
   - Section 3: VIX filter validation (`vix_favorable` True vs False + by category)
   - Section 4: Time-of-day win rates (bar-level, line + twin-axis bar count)
   - Section 5: Day-of-week + VIX category heatmap
   - Section 6: Volatility environment (SDV bands + box plot)
   - Section 7: Year/month trends + rolling 90-day win rate line
   - Section 8: Initial direction symmetry (above vs below)
   - Section 9: Streak histograms + next-day win rate following N-game streaks
   - Section 10: Combined best-case filter + sensitivity table (update after running)
   - Section 11: Markdown conclusions template (fill in after running)

2. **`requirements.txt`** — Added `scipy` for binomtest

3. **`simplify` review** caught 3 bugs before first run:
   - Section 2: Denominator mismatch — `philo_wins`/`money_wins` counted from all `df_day` rows but `n` was from `dropna` subset (fixed: all from `df_core = df_day.dropna(...)`)
   - Section 9: `.shift(-1)` applied to a *filtered* series → gave next matching streak row, not next calendar day (fixed: pre-compute `daily_s['next_outcome'] = daily_s['money_made'].shift(-1)` on full sorted df, then filter)
   - Sections 5+8: Identical heatmap annotation loops duplicated → extracted to `annotate_heatmap(rate_df, count_df, flag_threshold=None)` helper in Section 0

---

### Next Steps
1. **Run `analysis.ipynb`** with real `clean.csv` — see actual win rates, fill in Section 11 conclusions
2. Update Section 10 filter constants (`BEST_DOW`, `BEST_SDV_BANDS`, `BEST_DIRECTION`) based on findings
3. Expand `fixedConLocUpTo03-5-24.xlsx` past 2024-03-05
4. ~~Update contract month in `gettingData.ipynb`~~ — done in Session 4

---

## Session 7 — 2026-04-09

### What We Did

1. **Fixed `getNadexContracts.ipynb` pdfminer warning spam** — Added `logging.getLogger('pdfminer').setLevel(logging.ERROR)` to imports cell. The "Data-loss while decompressing corrupted data" messages are harmless internal PDF noise; suppressing them makes progress output readable.

2. **Fixed `getNadexContracts.ipynb` performance — 3 rounds of optimization:**
   - **Round 1:** Removed slow `extract_table()` pass (Pass 1). Kept text-only regex scan (Pass 2). Table extraction was taking minutes per PDF on large settlement PDFs.
   - **Round 2 (via `/simplify`):** Replaced sequential fetch loop with `ThreadPoolExecutor(max_workers=12)`. S3 HTTP requests are I/O-bound — 12 parallel workers give ~10x speedup. Also switched from `.loc[]` DataFrame lookup per date to O(1) `dict` lookup.
   - **Other `/simplify` fixes:** Removed unused `PERIOD_FILTER` from CONFIG (4:15PM expiry already uniquely identifies Daily contracts); added per-date warnings when only one of `above`/`below` is found (asymmetric bracket); tightened docstrings.

3. **Installed Claude Code plugins** (user-invocable skills):
   - `/simplify` → `code-simplifier` — runs parallel review agents for bugs/quality/efficiency. Validated this session.
   - `commit-commands` — `/commit`, `/push`, `/pr` shortcuts
   - `claude-md-management` — audits/updates CLAUDE.md
   - `hookify` — creates hook rules for automated behaviors

4. **Pushed all pending commits to GitHub** — 5 sessions of local-only commits (sessions 2–6) were never pushed. All 7 commits are now at `https://github.com/LMJones00/nadex-strategy`.

5. **Added Session Protocol to `CLAUDE.md`** — Claude now automatically stages, commits, and pushes at the end of every session. No need to ask.

### Current State (End of Session)

`getNadexContracts.ipynb` is **currently running** the parallel fetch cell. Output before context clear:
```
2024-03-11  open=5177.75  below=5169.0  above=5181.0
2024-03-12  open=5206.25  below=5203.0  above=5215.0
```
The run should complete quickly with 12 parallel workers. Once it finishes, `contract_locations.csv` will cover all dates in `GoodOldGoodOld.csv`.

### Next Steps
1. **Verify `getNadexContracts.ipynb` output** — spot-check one date (e.g. 2024-03-11: below=5169, above=5181) against the Nadex website or screenshots
2. **Run `barsToCleaning.ipynb`** end-to-end — confirm `cleaning.csv` has no NaN in `above`/`below` for recent dates
3. **Run `analysis.ipynb`** with full up-to-date `clean.csv` — fill in Section 11 conclusions
4. **Update Section 10 filter constants** (`BEST_DOW`, `BEST_SDV_BANDS`, `BEST_DIRECTION`) based on analysis findings
5. **Add validation to `cleaingToClean.ipynb`** for missing 16:00/16:15 close bars

---

## Session 6 — 2026-04-08

### What We Did
1. **Created `getNadexContracts.ipynb`** — Fully automates the Nadex contract lookup that was previously done manually.
   - Downloads daily settlement PDFs from `https://s3.amazonaws.com/market-data-prod.nadex.com/YYYYMMDD_tradingResults.pdf` (public S3, no login required)
   - Parses PDFs with `pdfplumber` — tries table extraction first, falls back to full-text regex scan
   - Extracts US 500 Daily binary contract strikes from Display Name (handles both `>` and `+` prefix formats)
   - Finds the strikes immediately above and below the 09:30 market open price
   - Writes `contract_locations.csv` (`date`, `above`, `below`) — incremental, skips already-covered dates
   - Replaces the manual Excel file `fixedConLocUpTo03-5-24.xlsx` entirely

2. **Modified `barsToCleaning.ipynb` Cell 28** — replaced `pd.read_excel("fixedConLocUpTo03-5-24.xlsx")` with `pd.read_csv("contract_locations.csv")`. Logic unchanged.

3. **Added `pdfplumber` to `requirements.txt`** and installed it.

### Updated Pipeline Order
```
0. getNadexContracts.ipynb   ← Run when new dates needed (after market close)
1. gettingData.ipynb
2. barsToCleaning.ipynb
3. cleaingToClean.ipynb
4. preparing.ipynb
```

### Note on Same-Day Contracts
PDFs are settlement results, available after market close. For same-day live trading, you still need to look up current contracts on nadex.com manually. This script covers all historical backfill and end-of-day pipeline runs.

### Next Steps
1. **First run of `getNadexContracts.ipynb`** — verify it finds correct above/below by spot-checking one date against a screenshot
2. Run `barsToCleaning.ipynb` end-to-end to confirm `cleaning.csv` has no NaN in `above`/`below` for recent dates
3. Run `analysis.ipynb` with full up-to-date `clean.csv`
4. Add validation to `cleaingToClean.ipynb` for missing 16:00/16:15 close bars

---

## Session 5 — 2026-04-08

### What We Did
1. **Fixed `gettingData.ipynb` Section 2** — Resolved Error 10314 ("Start Date/Time invalid") that was causing all tick requests to return 0 ticks.
   - **Root cause 1:** `reqHistoricalTicksAsync` only accepts ONE of `startDateTime` or `endDateTime` — the old code passed both, which triggers Error 10314 regardless of format.
   - **Root cause 2:** The `'YYYYMMDD HH:MM:SS US/Eastern'` format (which works for `reqHistoricalDataAsync`) is rejected by some TWS versions for `reqHistoricalTicksAsync`.
   - **Fix:** Convert 09:30:00 ET to UTC using pandas (handles DST) and pass as `'YYYYMMDD-HH:MM:SS'` (dash notation). Set `endDateTime=''`. Section 2 now works correctly.

### Next Steps
1. Discuss and expand `fixedConLocUpTo03-5-24.xlsx` past 2024-03-05 (user to explain approach)
2. Add validation to `cleaingToClean.ipynb` for missing 16:00/16:15 close bars
3. Run `analysis.ipynb` with real `clean.csv` — fill in Section 11 conclusions
4. Update Section 10 filter constants based on analysis findings

---

## Session 4 — 2026-04-02

### What We Did
1. **Remade `gettingData.ipynb`** — full rewrite with the following fixes:
   - **Removed `nest_asyncio`** from both sections. Python 3.14 changed `asyncio.timeout()` to require being inside a Task; `nest_asyncio` broke this, causing `RuntimeError: Timeout should be used inside a task` on every run. Modern Jupyter (ipykernel ≥ 6) runs `await` natively in cells — no workaround needed.
   - **Added CONFIG cell** at the top with all values that need updating each quarter: `CONTRACT_MONTH`, `MINUTES_END_DATE`, `MINUTES_DURATION`, `SECS_START_DATE`, `SECS_END_DATE`. Run this cell first before either section.
   - **Updated contract month** from `202406` (June 2024) to `202506` (June 2025/current).
   - **Removed duplicate `"09:30:00"`** entry in Section 1's `specific_times` list.
   - **Renamed loop variable** in Section 2 from `date` to `day` (was shadowing `datetime.date`).
   - **Cleared all stale outputs** from prior failed runs.

---

### Next Steps
1. Run `analysis.ipynb` with real `clean.csv` — see actual win rates, fill in Section 11 conclusions
2. Update Section 10 filter constants (`BEST_DOW`, `BEST_SDV_BANDS`, `BEST_DIRECTION`) based on findings
3. Expand `fixedConLocUpTo03-5-24.xlsx` past 2024-03-05
4. Add validation to `cleaingToClean.ipynb` for missing 16:00/16:15 close bars
