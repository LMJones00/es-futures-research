"""Stage 4: reconcile ES (2 yrs) vs SPY (25 yrs) on the gap fade; true out-of-sample months; intraday momentum test."""
import os
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"); os.makedirs(SP, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import warnings, numpy as np, pandas as pd
from scipy.stats import ttest_1samp, pearsonr
warnings.filterwarnings('ignore'); pd.set_option('display.width', 220)

G = pd.read_csv(f"{SP}/gaptable.csv", parse_dates=['date']).set_index('date').sort_index()
S = pd.read_csv(f"{SP}/spy_table.csv", parse_dates=['Date']).set_index('Date')
S.index = pd.to_datetime(S.index)
def hdr(t): print("\n" + "="*100 + f"\n{t}\n" + "="*100)
def tstat(x): x = pd.Series(x).dropna(); return x.mean()/(x.std()/np.sqrt(len(x)))
def summ(label, pnl, unit='bp'):
    pnl = pd.Series(pnl).dropna(); n = len(pnl); w = int((pnl>0).sum())
    print(f"  {label:<58} N={n:>4}  win={w/n:6.1%}  mean={pnl.mean():+6.1f} {unit}  med={pnl.median():+6.1f}  t={tstat(pnl):5.2f}  p={ttest_1samp(pnl,0,alternative='greater').pvalue:.4f}")

hdr("1. SAME RULE, SAME DATES — ES gap fade vs SPY gap fade, both open->close, in basis points")
G['es_fade_open_bp'] = (G['close'] - G['open']) / G['open'] * 1e4 * (-G['gap_dir'])
G['es_fade_open_1600_bp'] = (G['close_reg'] - G['open']) / G['open'] * 1e4 * (-G['gap_dir'])
G['es_fade_10_bp'] = G['fade_pnl'] / G['P_1000'] * 1e4
S['spy_fade_bp'] = S['fade'] * 100
J = G[['es_fade_open_bp','es_fade_open_1600_bp','es_fade_10_bp','gap_pct']].join(S[['spy_fade_bp','gap_pct']].rename(columns={'gap_pct':'spy_gap_pct'}), how='inner')
print(f"  Overlapping dates: {len(J)}")
print(f"  Gap agreement (sign): {(np.sign(J['gap_pct'])==np.sign(J['spy_gap_pct'])).mean():.1%}   corr of gap sizes: {pearsonr(J['gap_pct'], J['spy_gap_pct'])[0]:.3f}")
print(f"  Daily P&L correlation ES(open->16:15) vs SPY(open->close): {pearsonr(J['es_fade_open_bp'], J['spy_fade_bp'])[0]:.3f}")
summ('ES  fade open -> 16:15', J['es_fade_open_bp']); summ('ES  fade open -> 16:00', J['es_fade_open_1600_bp'])
summ('ES  fade 10:00 -> 16:15', J['es_fade_10_bp']); summ('SPY fade open -> close (same dates)', J['spy_fade_bp'])
w = S[(S.index >= G.index.min()) & (S.index <= G.index.max())]
summ('SPY fade, full ES window incl. dates ES is missing', w['spy_fade_bp'])
miss = w[~w.index.isin(G.index)]
summ(f'SPY fade on the {len(miss)} dates MISSING from the ES sample', miss['spy_fade_bp'])

hdr("2. TRUE OUT-OF-SAMPLE — SPY after the ES data ends (2026-04-10 -> today)")
oos = S[S.index > '2026-04-09']
summ('SPY fade open->close, 2026-04-10 -> 2026-09-02', oos['spy_fade_bp'])
summ('   ... |gap| >= 0.10% only', oos.loc[oos['gap_pct'].abs()>=0.10, 'spy_fade_bp'])
summ('   ... VIX >= 15 only', oos.loc[oos['vix_prev']>=15, 'spy_fade_bp'])
print("  Monthly (bp/day):", {f"{d.year}-{d.month:02d}": round(float(v),1) for d, v in oos['spy_fade_bp'].groupby(oos.index.to_period('M')).mean().items()})

hdr("3. WHY 2025 LOOKED SO GOOD — SPY fade in 2025 by month, and the share of the year's P&L from April")
y25 = S[S.index.year == 2025]
mm = y25['spy_fade_bp'].groupby(y25.index.month).sum()
print("  2025 monthly sum (bp):", {int(k): round(float(v)) for k, v in mm.items()})
print(f"  April share of 2025 total: {mm.get(4,0)/mm.sum():.0%}   2025 excluding April: mean {y25[y25.index.month!=4]['spy_fade_bp'].mean():+.1f} bp, t={tstat(y25[y25.index.month!=4]['spy_fade_bp']):.2f}")
print("  Long-history context — best calendar years for the SPY gap fade (mean bp): ",
      {int(k): round(float(v),1) for k, v in S['spy_fade_bp'].groupby(S.index.year).mean().sort_values(ascending=False).head(6).items()})

hdr("4. A PUBLISHED ALTERNATIVE — intraday momentum (Gao, Han, Li & Zhou 2018): first half-hour return predicts the LAST half-hour")
# ES: first half-hour = prev close -> 10:00 (their definition includes the overnight); last half-hour = 15:30 -> 16:00
G['r_first'] = (G['P_1000'] - G['prev_close']) / G['prev_close'] * 1e4
G['r_first_rth'] = (G['P_1000'] - G['open']) / G['open'] * 1e4
G['r_last'] = (G['P_1600'] - G['P_1530']) / G['P_1530'] * 1e4
G['r_1230'] = (G['P_1300'] - G['P_1230']) / G['P_1230'] * 1e4
ok = G[['r_first','r_last']].notna().all(axis=1)
print(f"  N={ok.sum()}  corr(first half-hour incl. overnight, last half-hour) = {pearsonr(G.loc[ok,'r_first'], G.loc[ok,'r_last'])[0]:+.3f}   "
      f"corr(first half-hour RTH only, last half-hour) = {pearsonr(G.loc[ok,'r_first_rth'], G.loc[ok,'r_last'])[0]:+.3f}")
summ('trade last 30 min in direction of (prev close -> 10:00)', (G['r_last'] * np.sign(G['r_first']))[ok])
summ('trade last 30 min in direction of (open -> 10:00)', (G['r_last'] * np.sign(G['r_first_rth']))[ok])
big = ok & (G['r_first'].abs() > 30)
summ('   ... only when |first half-hour| > 30 bp', (G['r_last'] * np.sign(G['r_first']))[big])
summ('trade last 30 min in direction of (prev close -> 15:30) [day momentum]', (G['r_last'] * np.sign((G['P_1530']-G['prev_close'])))[ok])
summ('trade 15:30->16:15 in direction of (prev close -> 10:00)', (((G['P_1615']-G['P_1530'])/G['P_1530']*1e4) * np.sign(G['r_first']))[ok])
print("  (Paper's SPY 1993-2013 result was a positive, significant relation; here N is small — this is a sanity check, not a finding.)")

hdr("5. FOR THE RECORD — the plain 'reversal' thesis on 25 yrs of SPY: does the first-30-min direction reverse by the close?")
print("  SPY daily data has no 10:00 price, so the closest test is: does the OPEN->CLOSE direction oppose the overnight gap (already shown: no edge).")
print("  ES 2-yr: direction at 09:35 vs open agreed with the close direction 57.7% of the time (continuation, not reversal).")

hdr("6. WHERE THE LONG-HISTORY EDGE ACTUALLY LIVES — overnight vs intraday return, SPY 1999-2026 and ES 2024-26")
on = (S['Open']/S['prev_close']-1)*1e4; intra = (S['Close']/S['Open']-1)*1e4
print(f"  SPY overnight (prev close->open): mean {on.mean():+.1f} bp/day  t={tstat(on):.2f}  N={on.notna().sum()}   cumulative {on.sum()/100:+.0f}%")
print(f"  SPY intraday  (open->close):      mean {intra.mean():+.1f} bp/day  t={tstat(intra):.2f}   cumulative {intra.sum()/100:+.0f}%")
for lo,hi in [(1999,2009),(2010,2019),(2020,2026)]:
    m=(S.index.year>=lo)&(S.index.year<=hi); print(f"    {lo}-{hi}: overnight {on[m].mean():+.1f} bp (t={tstat(on[m]):.2f})   intraday {intra[m].mean():+.1f} bp (t={tstat(intra[m]):.2f})")
onE = (G['open']/G['prev_close']-1)*1e4; inE = (G['close']/G['open']-1)*1e4
print(f"  ES 2024-03..2026-04: overnight {onE.mean():+.1f} bp (t={tstat(onE):.2f})   intraday {inE.mean():+.1f} bp (t={tstat(inE):.2f})   N={len(G)}")
