# ES Futures / Binary Options Trading Strategy

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

1. `gettingData.ipynb` — Fetches raw OHLCV bars from IBKR for ES futures
2. `barsToCleaning.ipynb` — Merges 1-min and 1-sec bars; adds market open price, initial direction, contract location
3. `cleaingToClean.ipynb` — Adds close prices (16:00 and 16:15); filters equal-direction rows
4. `preparing.ipynb` — Feature engineering: direction, profitability, SDV categories, win/loss streaks

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
| `fixedConLocUpTo03-5-24.xlsx` | (manual) | barsToCleaning | Contract above/below strikes per date — **only covers through 2024-03-05** |

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

---

## Magic Numbers & Non-Obvious Code

- **`secs.iloc[1140:]` in barsToCleaning.ipynb** — Drops the first 1,140 rows of the 1-second data, which had zero volume (pre-market rows from IBKR before an identified data gap). **This number must be recalculated if new sec data is prepended to `NewGoodOldGoodOld.csv`.** A more robust alternative is filtering by `volume > 0`.

- **SDV thresholds in preparing.ipynb** — The standard deviation bins for `open_close_diff_sdv_interval` are computed dynamically from the dataset's own mean and standard deviation. They are **not fixed values** — they shift as more data is added.

- **Holiday date list in barsToCleaning.ipynb** — Hardcoded list of CME early-close or holiday dates that must be manually updated when they occur (check the CME holiday calendar each year).

---

## Known Limitations

- `fixedConLocUpTo03-5-24.xlsx` only covers contract location data through **March 5, 2024**. Dates beyond this will have `NaN` for `above`, `below`, and `contract_location` columns. New entries must be added manually.
- The 1-second bar fetch window (09:30–10:00) and the contract month (`202506`) are hardcoded in `gettingData.ipynb` and must be updated manually each quarter.
- The equal-direction rows (~20% of data) are excluded from `clean.csv` — these are rows where the bar opens exactly at the market open price. They are preserved in `equal_rows.csv` for separate analysis.

---

## Prerequisites

- **IBKR TWS or IB Gateway** running on `localhost:7496` before running `gettingData.ipynb`
- Python packages: see `requirements.txt`
- `fixedConLocUpTo03-5-24.xlsx` must be present in the `Nadex Code/` directory

## Conventions

- All timestamps are **US/Eastern** timezone
- Weekends are filtered out at data fetch time
- The pipeline processes **weekdays only**
- Column names use snake_case; special columns with times use colons (e.g., `market_open_09:30`)
