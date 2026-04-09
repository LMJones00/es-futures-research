# ES Futures / Binary Options Trading Strategy

## Session Protocol

At the end of every session, Claude must automatically:
1. Stage all modified tracked files and any new code files (notebooks, .py scripts)
2. Commit with a descriptive message summarizing what changed this session
3. Push to `origin master`

Do not commit or push data files (*.csv, *.xlsx) — these are excluded by .gitignore.

## Strategy Description

This project analyzes a **mean-reversion hypothesis** on the S&P 500:

> The market tends to finish the day in the **opposite direction** of its initial move after the 09:30 ET open.

**Trade logic:**
- If the market initially moves **UP** after 09:30 → enter a **SELL** position at the nearest contract strike **BELOW** the open price
- If the market initially moves **DOWN** → enter a **BUY** position at the nearest contract strike **ABOVE** the open price

Originally designed for **Nadex binary options** on the S&P 500 (Nadex is operated by IG Group; verify current platform status at nadex.com). The strategy logic maps cleanly to ES/MES futures via IBKR as well.

---

## Pipeline Execution Order

Run notebooks in this exact sequence:

0. `getNadexContracts.ipynb` — Downloads Nadex settlement PDFs from S3 and writes `contract_locations.csv`. Run whenever new trading dates have been added to `GoodOldGoodOld.csv`. Skips already-covered dates (incremental). PDFs are available after market close — not same-day.
1. `gettingData.ipynb` — Fetches raw OHLCV bars from IBKR for ES futures
2. `barsToCleaning.ipynb` — Merges 1-min and 1-sec bars; adds market open price, initial direction, contract location
3. `cleaingToClean.ipynb` — Adds close prices (16:00 and 16:15); filters equal-direction rows
4. `preparing.ipynb` — Feature engineering: direction, profitability, SDV categories, win/loss streaks, VIX integration

---

## Data Files

These files are **not committed to git** (excluded via .gitignore):

| File | Produced By | Consumed By | Description |
|---|---|---|---|
| `GoodOldGoodOld.csv` | gettingData | barsToCleaning | Raw 1-minute OHLCV bars |
| `NewGoodOldGoodOld.csv` | gettingData | barsToCleaning | Raw 1-second bars (09:30–10:00 window) |
| `newBarsCombined.csv` | barsToCleaning | barsToCleaning | Intermediate merged bars |
| `cleaning.csv` | barsToCleaning | cleaingToClean | Enriched bars with contract location |
| `clean.csv` | cleaingToClean | preparing | Analysis-ready dataset (equal rows removed) |
| `equal_rows.csv` | cleaingToClean | (analysis) | Rows where open == market open (separated) |
| `open_rows.csv` | cleaingToClean | (analysis) | 09:30 open bar subset of equal_rows |
| `contract_locations.csv` | getNadexContracts | barsToCleaning | Contract above/below strikes per date — auto-generated from Nadex S3 PDFs |
| `fixedConLocUpTo03-5-24.xlsx` | (archived) | — | Old manual Excel file, superseded by `contract_locations.csv` |

---

## Key Column Definitions

| Column | Description |
|---|---|
| `market_open_09:30` | The `candle_open_price` at exactly 09:30:00 for each trading day — the reference price for the whole day |
| `initial_direction` | Whether each bar's open is `'above'`, `'below'`, or `'equal'` vs `market_open_09:30` |
| `contract_location` | The target Nadex strike level for this bar. If `initial_direction == 'above'` → use the `below` strike (expecting reversal down). If `'below'` → use the `above` strike. |
| `market_close_16:15` | After-hours close price (extended session) |
| `market_reg_close_16:00` | Regular session close price |
| `day_direction_16:15` | Whether price closed `'up'`, `'down'`, or `'equal'` relative to market open |
| `philo_result` | `'correct'` if the day's closing direction matched the predicted reversal; `'incorrect'` otherwise |
| `money_made` | `'yes'` if price crossed the `contract_location` in the predicted direction by end of day |
| `diff_open_close` | Absolute difference between `market_open_09:30` and `market_close_16:15` (daily range) |
| `open_close_diff_sdv_interval` | Categorical SDV band for `diff_open_close`: Very Low / Low / Slightly Low / Neutral / Slightly High / High / Very High |
| `diff_open_conLoc` | Absolute distance between `market_open_09:30` and `contract_location` |
| `dow_win_streak` | Running consecutive wins for this time + day-of-week combination |
| `overall_win_streak` | Running consecutive wins for this time slot across all days |
| `vix_close` | Daily VIX closing value fetched via yfinance (forward-filled for holidays/weekends) |
| `vix_category` | Fixed-threshold VIX band: `Low` (<15), `Moderate` (15–25), `Elevated` (25–35), `High` (>35) |
| `vix_favorable` | `True` when VIX is 15–30 — the mean-reversion sweet spot (enough noise for reversals, not enough trend to override them) |

---

## Magic Numbers & Non-Obvious Code

- **`secs.iloc[1140:]` in barsToCleaning.ipynb** — Drops the first 1,140 rows of the 1-second data, which had zero volume (pre-market rows from IBKR before an identified data gap). **This number must be recalculated if new sec data is prepended to `NewGoodOldGoodOld.csv`.** A more robust alternative is filtering by `volume > 0`. Note: the tick-based fetch (Section 2 of gettingData) always writes `volume=0` — filter by volume is not applicable for newly fetched data; rely on the `time` column filter instead.

- **SDV thresholds in preparing.ipynb** — The standard deviation bins for `open_close_diff_sdv_interval` are computed dynamically from the dataset's own mean and standard deviation. They are **not fixed values** — they shift as more data is added.

- **Holiday date list in barsToCleaning.ipynb** — Hardcoded list of CME early-close or holiday dates that must be manually updated when they occur (check the CME holiday calendar each year).

- **`VIX_TICKER = '^VIX'` and `categorize_vix()` in preparing.ipynb (Section 13)** — VIX thresholds (`[0, 15, 25, 35, inf]`) are **fixed absolute values**, unlike SDV bins which are computed dynamically from the dataset. `vix_favorable` uses an upper bound of **30**, not 35 — trending/panic behavior starts dominating above 30 even though the `'Elevated'` category band extends to 35 (deliberate split for analytical granularity vs. trade filter). The MultiIndex column flatten (`vix_raw.columns.get_level_values(0)`) is required for compatibility with yfinance >=0.2.x which returns multi-level columns for single-ticker downloads.

---

## Known Limitations

- Contract location data is now auto-generated by `getNadexContracts.ipynb`, which downloads Nadex settlement PDFs from `https://s3.amazonaws.com/market-data-prod.nadex.com/YYYYMMDD_tradingResults.pdf`. Run it before `barsToCleaning.ipynb` to ensure all dates are covered. PDFs are published after market close — same-day contracts still require manual lookup on nadex.com.
- The 1-second bar fetch window (09:30–10:00) and the contract month are set in the **CONFIG cell** at the top of `gettingData.ipynb`. Update `CONTRACT_MONTH`, `MINUTES_END_DATE`, `SECS_START_DATE`, and `SECS_END_DATE` there before each run. Current contract month: `202606` (June 2026 — update each quarter: Mar/Jun/Sep/Dec).
- The equal-direction rows (~20% of data) are excluded from `clean.csv` — these are rows where the bar opens exactly at the market open price. They are preserved in `equal_rows.csv` for separate analysis.

---

## IBKR Data Subscription Notes

- **`whatToShow='TRADES'`** requires an active CME Real-Time (NF2) subscription with live entitlement. If you see Error 162 "HMDS query returned no data" for TRADES but not for MIDPOINT, the subscription's commission-waiver condition is not being met. **Both sections of `gettingData.ipynb` use `whatToShow='MIDPOINT'`** as the reliable fallback — prices differ by at most 0.125 ES points (half a tick), which is negligible for this strategy.
- **Section 1 (1-min bars)** uses `reqHistoricalDataAsync` — IBKR retains 1-minute data for years.
- **Section 2 (1-sec bars)** uses `reqHistoricalTicksAsync` — this is the same backend as TWS Time & Sales and reaches further back than the HMDS 1-second bar endpoint (which only retains ~30 days). Fetches raw ticks for 09:30–09:31 per day and snaps each to the last tick price at or before each target second.
- **`reqHistoricalTicksAsync` datetime format** — Use UTC with dash notation: `'YYYYMMDD-HH:MM:SS'` (e.g. `'20240311-13:30:00'`). The `'YYYYMMDD HH:MM:SS US/Eastern'` format causes Error 10314 in some TWS versions for this specific endpoint (even though it works fine for `reqHistoricalDataAsync`). Convert using pandas: `pd.Timestamp(f'{date} 09:30:00', tz='US/Eastern').tz_convert('UTC').strftime('%Y%m%d-%H:%M:%S')` — handles DST automatically.
- **`reqHistoricalTicksAsync` only accepts ONE of startDateTime or endDateTime** — passing both causes Error 10314. Use `startDateTime=utc_str, endDateTime=''` to fetch ticks forward from 09:30:00.
- **`numberOfTicks=1000`** in Section 2 is the per-request cap for `reqHistoricalTicksAsync`. If exactly 1000 ticks are returned for a day, the window may have been truncated — paging would be needed (not yet implemented).

## Prerequisites

- **IBKR TWS or IB Gateway** running on `localhost:7496` — **only required for `gettingData.ipynb`**. Notebooks 2–4 do not connect to IBKR.
- **Internet access** required for `preparing.ipynb` Section 13 — fetches VIX data via `yfinance`
- Python packages: see `requirements.txt`
- `fixedConLocUpTo03-5-24.xlsx` must be present in the `Nadex Code/` directory

## Conventions

- All timestamps are **US/Eastern** timezone
- Weekends are filtered out at data fetch time
- The pipeline processes **weekdays only**
- Column names use snake_case; special columns with times use colons (e.g., `market_open_09:30`)
