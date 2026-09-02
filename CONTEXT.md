# ES Futures / Binary Options Strategy — Project Context

Last updated: 2026-09-02 · **CLOSED-OUT as a strategy** — the headline signal was shown to be an artifact on
2026-09-02; the pipeline and re-analysis scripts remain as a research template. No capital committed.

> Numbers below are from the 2026-09-02 re-analysis (`reference/exploration-2026-09-02.md`, reproducible via
> `python reanalysis/run_all.py`). The pre-September findings are kept in `reference/analysis-findings.md`
> for the record; read them with Section "Where things stand" in mind.

## What this project is

A research project that tested a **mean-reversion hypothesis** on the S&P 500:

> The market tends to finish the day in the **opposite direction** of its initial move after the 09:30 ET open.

**Trade logic as originally framed:**
- Market initially moves **UP** after 09:30 → **SELL** at the nearest contract strike **BELOW** the open price.
- Market initially moves **DOWN** → **BUY** at the nearest contract strike **ABOVE** the open price.

Designed for **Nadex binary options** on the S&P 500 (Nadex is operated by IG Group), with ES/MES futures via
IBKR as the alternative instrument. This is a **research pipeline, not a live trading system.**

## The process — run notebooks in this exact order

0. `getNadexContracts.ipynb` — downloads Nadex settlement PDFs from S3 → `contract_locations.csv`.
   Run whenever new trading dates are added. Skips covered dates (incremental). PDFs publish after
   market close, not same-day.
1. `gettingData.ipynb` — fetches raw OHLCV bars from IBKR for ES futures. **Only notebook needing TWS.**
2. `barsToCleaning.ipynb` — merges 1-min and 1-sec bars; adds market open price, initial direction,
   contract location.
3. `cleaingToClean.ipynb` — adds close prices (16:00 and 16:15); filters equal-direction rows.
4. `preparing.ipynb` — feature engineering: direction, profitability, SDV categories, streaks, VIX.

Then `analysis.ipynb` (Sections 0–19) for the original research, and `reanalysis/run_all.py` for the
September 2026 re-analysis (needs `clean.csv`, `cleaning.csv`, and internet for the SPY stage).

## Where things stand

**The 76.9% headline is a head-start artifact, not an edge.** It scores a "win" when the close is past a
strike ≤ 12 pts from the open — but on every "strong drift" day price was already ~20 pts past that strike at
10:00. Traded as futures from the 10:00 price, the same 40 days win 52.5% with mean −0.9 pts; the 64
strong-drift days average −7 pts. No stop level changes that. Section 20 (MAE/MFE) is therefore moot.
Nadex priced those binaries at ~$75 because ~75% was the right probability.

**The premise is mildly wrong-signed.** The 09:35 direction agrees with the close direction 57.7% of the
time — slight continuation, not reversal — and neither is tradeable from 10:00.

**One new candidate was tested and falsified.** Fading the overnight gap from 10:00 earned +5.4 pts/day
(t = 2.8) on the two years of ES data and passed a selection-adjusted test — then showed no edge over
25 years of SPY (t = 0.4), lost money in every month after the ES data ended (Apr–Sep 2026, −10 bp/day),
and turned out to be riding 2025, the best year for that rule since 1999.

**Where the long-history evidence points:** SPY 1999–2026 overnight return +3.4 bp/day (t = 4.0) vs
open-to-close +0.9 bp/day (t = 0.75). The documented index-level edge is overnight — the mirror of this
project's intraday frame.

## What good looks like

There is no pending analysis deliverable. If the project is reopened, the bar is:

1. **Daily-history first.** Any candidate signal clears a 25-year SPY/ES daily test
   (`reanalysis/04_spy_25yr_history.py` is the template) and a selection-adjusted permutation test
   *before* any intraday engineering.
2. **Score from the tradeable price.** A signal that fires at 10:00 is scored from the 10:00 price.
3. **Fix the pipeline first** — see the two bugs under "What to avoid".

## What to avoid

- **Do not score a signal from the open when the trade enters at 10:00.** "Close still on the same side"
  rises to 89% as the head start grows; profit from the entry price does not follow.
- **Do not trust two years of intraday data to separate a regime from an edge.** Free daily history can,
  in seconds.
- **Two known pipeline bugs:** (1) `market_open_09:30` is forward-filled in `barsToCleaning.ipynb`, so the
  pre-market bars on the first 22 days inherit the *previous* day's open and 21 days are scored wrong;
  (2) day-level "initial direction" is the 09:30:01 tick on 432 days — define it at a fixed clock time.
- **Do not use a trailing stop at the contract level** (100% of best-signal days retraced past it) — moot
  now, kept for the record.
- **Do not treat VIX as an entry filter.** It predicts morning range (r = 0.685), not direction.
- **Do not commit data files.** `*.csv` / `*.xlsx` and `reanalysis/_out/` are gitignored on purpose.
