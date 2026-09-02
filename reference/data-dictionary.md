# Data Dictionary

Last updated: 2026-04-15

Reference for the pipeline's files and columns. Loaded only when working with the data itself.

## Data files

None of these are committed to git (excluded via `.gitignore`).

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

## Key column definitions

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

## Conventions

- All timestamps are **US/Eastern**.
- Weekends are filtered out at fetch time; the pipeline processes **weekdays only**.
- Column names use snake_case; special columns with times use colons (e.g. `market_open_09:30`).
- Equal-direction rows (~20% of data) are excluded from `clean.csv` and preserved in `equal_rows.csv`.
