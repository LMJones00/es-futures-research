# Analysis Findings — Sections 12–19

Last updated: 2026-04-15

Detailed results behind the headline in `../CONTEXT.md`. `analysis.ipynb` fully run over 507 days
(2024-03-11 → 2026-04-09), 91 cells, Sections 0–19.

**Baseline: the raw strategy has no edge.** Tradeable win rate 37.0%, philosophical 41.8%, p≈1.0.
No filter combination (VIX, SDV, DOW) breaks 50% — best case (VIX favourable + SDV tight) = 43.9%.

## Section 12 — the early-session signal

- Wide open (first-30-min range > median ≈0.351%) + early reversal (30-min drift already pulling back
  against initial direction) = **60.6% on 127 days** (25% of all days).
- Max-away from contract location decays monotonically: closer = better (54.9% → 25.5%).
- 12d triple filter (wide + reversal + close to contract, bottom 40%) = **68.2% on 66 days**.

## Section 13 — drift magnitude & calendar (on the 127 Wide+Reversal days)

- Pearson r = 0.363 (p<0.0001): bigger early pullbacks predict bigger final moves — weak-to-moderate
  but real.
- **Strong drift (>0.30%) = 69.8% on 63 days** — this is where the edge concentrates.
- Medium drift (0.15–0.30%) = 50.0% on 40 days (coin flip); small drift = 55% on 20 days.
- **The 60.6% headline is a 70% group and a 52% group averaged together.**
- Progress ratio: 84% of Wide+Reversal days already have price past the contract by 10am — binary entry
  likely deep in-the-money, inverted risk/reward is an execution concern.
- Calendar: Thursday weakest DOW at 50%; Q4 (Oct–Dec) weak at 42–50%; mid-late month (days 15–21)
  strongest at 72.4%; early month (days 1–7) weakest at 55.3% (turn-of-month effect).

## Section 14 — strong-drift stress test

- Strong drift + non-Q4 = **76.1% on 46 days** (~22/yr).
- Strong drift + non-Q4 + not Thursday = **76.9% on 39 days** (~19/yr).
- Mid-late month + strong drift = 80.0% on 20 days (N too small — directional hint only).
- Within non-Q4: Friday 100% (N=7), Wednesday 83.3% (N=6), Monday 78.6% (N=14) — small samples.

## Section 15 — binary entry price model

- Mean estimated 10am entry price **$68** (median $75); 74% of Wide+Reversal days are deep ITM (>150%
  past contract).
- P&L by filter: Wide+Rev all = −$986 total; strong drift = −$325; strong+non-Q4 = **+$50** (~+$1.1/trade);
  strong+non-Q4+not-Thu = **+$75** (~+$1.9/trade).
- **Verdict: Nadex pricing absorbs nearly all the edge.** Only the two strictest filters clear
  breakeven, and barely.
- Sensitivity: strong drift positive EV only at entry ≤$70; strong+non-Q4 positive at ≤$80.

## Section 16 — early entry (9:40 / 9:45)

- Price savings: 9:40 mean ~$59 (saves ~$9 vs 10am); 9:45 mean ~$62 (saves ~$6).
- Signal precision: a 9:40 reversal holds to 10am only 69.3% of the time (31% false positives).
- Win rate drops to 55.9% at 9:40 (vs 60.6% at 10am) — savings offset by the lower win rate.
- P&L: 9:40 all = −$434; 9:40+non-Q4+not-Thu = −$162; 10am+non-Q4+not-Thu = −$87.
- **Early entry does not rescue Nadex EV** — the strong-drift filter, the key edge concentrator, cannot
  be confirmed before 10am.

## Section 17 — intraday retracement (39 best-signal days)

- **100%** of best-signal days had some intraday retrace past the contract level after 10am.
- Win rate on crossback days: 76.9% — identical to overall. Deep retraces do **not** predict losses.
- Median retrace 21.2 pts (350% of the open-to-contract gap); mean 33.9 pts.
- 30/39 days retraced >150% of gap — most winners see violent counter-moves before closing correctly.
- **Implication for futures: a trailing stop at the contract level would be hit 100% of the time.**

## Section 18 — pre-market predictability (VIX as signal predictor)

- VIX (prior close) vs first-30-min range: Pearson r = 0.685 (p<0.0001) — strong predictor of morning
  volatility.
- Signal rate by VIX on calendar-passing (non-Q4, non-Thu) days, baseline 7.7%:
  Low (<15) 2.8% · Moderate (15–25) 13.5% (~2×) · Elevated (25–35) 29.2% (~4×) · High (>35) 40.0% (N=5).
- **VIX predicts whether the morning will be wide; it cannot predict whether price will reverse.**
  Use for attention-sizing, not entry.

## Section 19 — OTM contract win rate (one Nadex interval = 12 pts further)

| Filter | NM win% | OTM win% | Median close past NM |
|---|---|---|---|
| Wide + Reversal (all 127) | 60.6% | 55.1% | 15.5 pts |
| Strong drift (63) | 69.8% | 63.5% | 17.0 pts |
| Strong + non-Q4 (46) | 76.1% | 67.4% | 19.4 pts |
| Strong + non-Q4 + not-Thu (39) | 76.9% | 66.7% | 18.5 pts |

- EV at realistic OTM entry (best filter, 66.7%): +$46.7 at $20 entry, +$16.7 at $50. Breakeven $66.70.
- **Why OTM holds up:** median close is 18.5 pts past the near-money strike; the OTM strike is only
  12 pts further, so most winning days clear it anyway.
- **Critical unknown:** actual Nadex OTM prices at 10am on signal days are unverified. The EV table
  assumes $20–50. Observe live prices before committing capital.

## Next — Section 20 (not yet run)

MAE/MFE stop-loss analysis. Use bar-level `df` on the 39 best-signal days to compute Maximum Adverse
Excursion and Maximum Favorable Excursion; produce a stop-sweep EV table. This determines stop placement
for ES/MES futures and confirms or kills the futures path.
