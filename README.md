# ES Futures Quantitative Research

**Status: closed research project (September 2026). No capital was ever committed.**

A two-year research pipeline that tested one hypothesis on the S&P 500: *the market tends to finish the
day in the opposite direction of its first move after the 09:30 ET open.* The pipeline found a filter
with a 76.9% win rate. The re-analysis showed that number was a scoring artifact, and this repository
documents both.

## What was built

A 5-stage Python pipeline over 533 trading days of E-mini S&P 500 (ES) data:

1. **Contracts** — downloads and parses 533+ Nadex daily settlement PDFs from public S3 to recover binary
   contract strike levels (`getNadexContracts.ipynb`, `parse_pdf.py`)
2. **Bars** — pulls 1-minute and 1-second ES bars from Interactive Brokers via the async API
   (`gettingData.ipynb`)
3. **Cleaning** — merges bar resolutions, adds the market open, initial direction and contract location
4. **Features** — 43 engineered columns, vectorized in NumPy, plus pre-market VIX and the CME holiday
   calendar (`preparing.ipynb`)
5. **Analysis** — filter search, binomial tests, Pearson correlation, rolling win rates and calendar
   seasonality (`analysis.ipynb`)

## What it found

**The 76.9% was real but was not an edge.** A "win" was scored when the close finished past a strike
within 12 points of the open. On every day the best filter selected, price was already about 20 points
past that strike by 10:00, when the trade could actually be entered. Scored from the 10:00 price, the
same 40 days win 52.5% and average −0.9 points. The market had priced those contracts at about $75
because 75% was the correct probability.

**A second candidate was tested and falsified.** Fading the overnight gap from 10:00 earned +5.4
points/day (t = 2.8) on the two years of ES data and passed a selection-adjusted test. It then showed no
edge across 25 years of SPY history (t = 0.4), lost money in every month after the sample ended, and
turned out to be riding 2025, that rule's best year since 1999.

## What transfers

- **Score a signal from the price you can actually trade.** A signal that fires at 10:00 is measured
  from 10:00.
- **Two years of intraday data cannot separate a regime from an edge.** Free daily history can, in
  seconds. Any new candidate should clear a long-history test before any intraday engineering.
- **Kill results before they cost money.** Both candidates were retired before any capital was
  committed.

## Repository map

| Path | Contents |
|---|---|
| `reference/exploration-2026-09-02.md` | The re-analysis: the head-start artifact, the gap-fade falsification, pipeline bugs (`.html` twin has the charts) |
| `reference/analysis-findings.md` | The original results (April 2026), kept for the record |
| `reference/data-dictionary.md` · `technical-notes.md` | Every column, file and pipeline convention |
| `reanalysis/` | Five scripts reproducing the September findings; `run_all.py` runs them in about 3 minutes |
| `*.ipynb` | The pipeline and analysis notebooks, in run order in `CONTEXT.md` |

Data files are not committed. Reproducing the pipeline needs an Interactive Brokers account with market
data (TWS running); the SPY long-history stage needs only an internet connection.

**Stack:** Python · pandas · NumPy · SciPy · ib_insync · pypdfium2 · yfinance · Plotly · Jupyter
