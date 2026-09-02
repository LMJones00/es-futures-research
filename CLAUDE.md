# ES Futures / Binary Options Trading Strategy

Last updated: 2026-09-02 · **CLOSED-OUT as a strategy on 2026-09-02** — headline signal shown to be a
head-start artifact; pipeline and re-analysis kept as a research template. No capital committed.

Map for a research project that tested a mean-reversion hypothesis on the S&P 500 — the market finishes
the day opposite its initial move after the 09:30 ET open. Research pipeline, **not** a live trading system.

**The strategy, the pipeline order, the September 2026 verdict, and what to avoid are in
[CONTEXT.md](CONTEXT.md). Read it first.** This file only routes.

## Folder map

| Path | What it holds |
|------|----------------|
| `CONTEXT.md` | Strategy, pipeline order, where things stand (2026-09-02 verdict), what to avoid |
| `reference/exploration-2026-09-02.md` | The re-analysis: head-start fallacy, gap-fade falsification, data bugs, next rules (`.html` twin = same content with charts; open in a browser) |
| `reference/analysis-findings.md` | Original Section 12–19 results (Apr 2026) — superseded, kept for the record |
| `reference/data-dictionary.md` | Pipeline file table + every column definition + conventions |
| `reference/technical-notes.md` | Magic numbers, IBKR quirks, known limitations, prerequisites |
| `reanalysis/` | Five numbered scripts + `run_all.py` reproducing the 2026-09-02 findings (~3 min); `_out/` gitignored |
| `*.ipynb` | The pipeline and analysis notebooks — run order in `CONTEXT.md` |
| `parse_pdf.py` | Nadex settlement-PDF parser used by `getNadexContracts.ipynb` |
| `*.csv`, `*.xlsx` | Generated data. **Gitignored — never committed** |
| `NOTES.md` | Session-by-session working notes (newest first) |

## Routing

| Task | Go to | Read |
|------|-------|------|
| Understand the strategy or the verdict; decide what to do next | `CONTEXT.md` | — |
| See why the 76.9% was not an edge, or how the gap fade was falsified | `reference/exploration-2026-09-02.md` | — |
| Test a new candidate signal | `reanalysis/04_spy_25yr_history.py` (template), then `run_all.py` | `CONTEXT.md` → "What good looks like" |
| Look up a column or data file | `reference/data-dictionary.md` | — |
| Edit a notebook / debug a data fetch | `reference/technical-notes.md` | then the notebook |
| Check how an original win rate was derived | `reference/analysis-findings.md` | — |
| Fetch new bars from IBKR | `gettingData.ipynb` | CONFIG cell — update contract month first |
| Refresh contract strikes | `getNadexContracts.ipynb` | — |

## Rules

- **Session protocol** — at the end of every session, stage modified tracked files and any new code
  (notebooks, `.py`), commit with a descriptive message, and push to `origin master`. ⚠️ The working tree
  holds **pre-existing uncommitted deletions** of helper scripts (`add_section16.py`, `extract_nb.py`, …)
  from an earlier session — stage files explicitly rather than `git add -A` until Luke resolves them.
- **Never commit data files** — `*.csv` / `*.xlsx` / `reanalysis/_out/` are gitignored deliberately.
- **This folder is its own git repo** (`es-futures-research`), separate from the Claude Code Files tree,
  which gitignores it. Commit here, not in the parent.
- Write in plain language; ask before assuming; say so when unsure.
