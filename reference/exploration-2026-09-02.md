# Exploration — 2026-09-02: the headline is a head start, and the one new lead is a mirage

Fresh-eyes re-analysis of the whole project. Everything here is reproducible with
`python reanalysis/run_all.py` (needs `clean.csv` / `cleaning.csv` from the pipeline and internet for the
SPY stage). The day-level table was rebuilt from `cleaning.csv` and reproduces the prior headline numbers
first (61.3% / 70.3% / 76.6% / 77.5% vs the documented 60.6% / 69.8% / 76.1% / 76.9%), so the comparisons
below are like-for-like.

## Verdict in three lines

1. **The 76.9% "win rate" is real but is not an edge.** It measures the chance that a price *already ~20 pts
   past the strike at 10:00* is still past it at the close. Traded as futures from the 10:00 price, the same
   days win 50–52% and average **−1 to −7 pts**. Nadex priced those binaries at ~$75 because 75% was the
   correct probability. Section 20 (MAE/MFE) is not needed: no stop level rescues it.
2. **The one genuinely new candidate — fade the overnight gap from 10:00 — looked excellent on the two years of
   ES data** (+5.4 pts/day, t = 2.8, survives a selection-adjusted test at p < 0.01) **and fails everywhere
   else:** flat over 25 years of SPY (t = 0.4, 13 of 28 years positive), negative in every month since the ES
   data ended (Apr–Sep 2026: −10 bp/day, 42% win), and 2025 was the single best year for that rule since 1999.
3. **The lesson that transfers:** two years of intraday data cannot tell a regime from an edge. Free daily
   history can, in 30 seconds. Any future candidate should clear a 25-year daily test *before* intraday work.

## 1. The head-start fallacy

How the prior signal is scored: `money_made = 'yes'` if the 16:15 close is past the near-money strike in the
"reversal" direction. The strike sits ≤ 12 pts from the open. On every "strong drift" day, price at 10:00 is
already **past that strike** (100% of the 64 days; median 20.4 pts past on the best-40 set). So a "win" only
requires that price not give the whole head start back.

| Subset (prior label) | N | prior win rate | already past strike at 10:00 | futures win (enter 10:00) | mean pts | t |
|---|---|---|---|---|---|---|
| Wide + Reversal | 124 | 61.3% | 86% | 50.8% | −2.2 | −0.56 |
| + Strong drift (>0.30%) | 64 | 70.3% | 100% | 50.0% | −7.0 | −1.08 |
| + non-Q4 | 47 | 76.6% | 100% | 51.1% | −0.5 | −0.07 |
| + not Thursday | 40 | 77.5% | 100% | 52.5% | −0.9 | −0.13 |

Of the 31 "wins" in the best-40 set, 10 were days the futures trade from 10:00 lost money.

The same effect, without any filter, on all 501 days by size of the 10:00 move from the open:

| \|10:00 move\| | N | close on same side as 10:00 | futures win from 10:00 | mean pts |
|---|---|---|---|---|
| > 0.30% | 133 | 76.7% | 52.6% | +1.4 |
| > 0.40% | 78 | 82.1% | 55.1% | +8.5 |
| > 0.50% | 46 | 89.1% | 58.7% | +14.5 (t = 1.2) |

"Still on the same side at the close" climbs to 89% as the head start grows. The profit from the 10:00 price
does not follow; none of it is significant. **Rule: score a signal from the price you can actually trade
at, never from the open.**

Two smaller findings in the same vein:

- **"Initial direction" was a one-second tick.** The day-level direction comes from the first bar whose open
  differs from the 09:30 open — the 09:30:01 tick on 432 days, the 09:31 bar on 38. It agrees with the close
  direction 55.6% of the time. The 09:35 direction agrees 57.7% — i.e. the market *continues* its first five
  minutes slightly more often than it reverses. The project's premise is mildly wrong-signed, and neither
  version is tradeable from 10:00.
- **Selection.** Random relabeling of the 127 Wide+Reversal days produces a ≥ 76.9% subset (N ≥ 35) 4.1% of
  the time under the 24-filter family actually searched. Calendar filters were mildly lucky, on top of the
  head start.

## 2. The gap fade: what a mirage looks like in your own data

Rule: at 10:00, trade **against** the overnight gap (open vs prior 16:15 close), hold to 16:15, no stop.

**In-sample (ES, 477 consecutive-day pairs, Mar 2024 – Apr 2026):** +5.42 pts/trade, 52.8% win, t = 2.77.
Positive in every year and both halves; survives removing the April 2025 tariff week (+4.2, t = 2.4); sign-flip
permutation over an 18-member threshold family gives p = 0.004 (iid) / 0.009 (10-day blocks). Net of two ticks
and commission, one MES contract ≈ +$5.3k/yr with a ≈ $1.7k max drawdown; Sharpe ≈ 1.75. Everything a
notebook would call confirmed.

**Then the checks that cost nothing:**

| Test | Result |
|---|---|
| Same rule, same 467 dates, on SPY daily data (Yahoo) | +10.2 bp/day, t = 2.5 — identical (daily P&L r = 0.92). The intraday pipeline added nothing. |
| Same rule, SPY 1999–2026 (6,781 days) | +0.5 bp/day, t = 0.41. 13 of 28 years positive. VIX ≥ 15 filter: t = 0.31. |
| Where 2025 sits in that history | Best year of 28 (+12.4 bp/day). April 2025 alone = 55% of the year. |
| Out-of-sample: SPY 2026-04-10 → 2026-09-02 (100 days, after the ES data ends) | **−10.0 bp/day, 42% win, t = −1.8, negative in all six months.** |
| The 43 dates *missing* from the ES sample (holidays, IBKR gaps) inside its own window | −12.2 bp/day. The sample's holes flattered it. |
| Literature | A 2026 systematic falsification study on MNQ futures reports the gap-fill fade fails at every tested entry time (arXiv 2605.04004). |

Also checked and empty on this data: entry-time sweep 09:35–15:00 (no special time), exit sweep (hold to close
is best but nothing significant), stop sweep (every stop lowers the mean), Nadex framing (nearest strike past
the 10:00 price wins 44%), and the published "intraday momentum" relation (first half-hour → last half-hour:
t = −0.6 here).

## 3. Data issues to fix if the pipeline is ever rerun

- **21 days scored against the previous day's open.** `market_open_09:30` is forward-filled in
  `barsToCleaning.ipynb`, so the 07:00–09:15 pre-market bars (present for the first 22 days, Mar–Apr 2024)
  inherit the *prior* day's open, survive as non-`equal` rows, and become the first row of the day in
  `clean.csv`. Every day-level outcome for those 21 days is wrong. Fix: set the open per date, not by ffill.
- **Define "initial direction" at a fixed clock time** (e.g. 09:35 or 10:00), not "first bar that differs".
- Bars after 10:00 are sampled roughly every 15 minutes, so any MAE/MFE from `candle_high/low` is a lower
  bound.

## 4. Where index-level evidence actually points

SPY 1999–2026, ex-dividend days removed: overnight (prior close → open) **+3.4 bp/day, t = 4.0, cumulative
+229%**; intraday (open → close) +0.9 bp/day, t = 0.75, +61%. Overnight is positive in each of 1999–2009,
2010–2019, 2020–2026. This is the documented "overnight drift" (NY Fed staff report 917; Cooper, Cliff &
Gulen 2008). It is an unconditional premium, not a timing signal, and it carries gap risk — but it is the exact
mirror of this project's intraday-only frame. If the project continues, that is the half of the day with a
25-year record behind it.

## 5. What to do with this

1. Retire the 76.9% headline and the "futures path". Update the resume line to the honest version: built the
   pipeline, found the signal, then falsified it with a head-start analysis and a 25-year out-of-sample test.
   That is a better story than an unverified edge.
2. Adopt a **daily-history-first rule**: any candidate is tested on 25 years of SPY/ES daily data (stage 04
   pattern) and passes a selection-adjusted permutation test before any intraday engineering.
3. Fix the two data bugs above before trusting any future output of the pipeline.
4. Keep `reanalysis/` as the template for the next idea; it runs end-to-end in about three minutes.

Sources: [arXiv 2605.04004 — Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures](https://arxiv.org/pdf/2605.04004) ·
[NY Fed Staff Report 917 — The Overnight Drift](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf) ·
[Elm Wealth — Night Moves: the overnight drift](https://elmwealth.com/night-moves-overnight-drift/)
