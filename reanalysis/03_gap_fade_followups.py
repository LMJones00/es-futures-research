"""Stage 3: ES follow-ups on the gap fade — symmetry, costs, monthly consistency, VIX filter, gap-fill stats, chart data."""
import os
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"); os.makedirs(SP, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import warnings, json, numpy as np, pandas as pd
from scipy.stats import ttest_1samp, binomtest
warnings.filterwarnings('ignore'); pd.set_option('display.width', 220)

G = pd.read_csv(f"{SP}/gaptable.csv", parse_dates=['date']).set_index('date').sort_index()
yrs = (G.index.max() - G.index.min()).days / 365.25
def hdr(t): print("\n" + "="*100 + f"\n{t}\n" + "="*100)
def tstat(x): x = pd.Series(x).dropna(); return x.mean()/(x.std()/np.sqrt(len(x)))
def summ(label, pnl):
    pnl = pd.Series(pnl).dropna(); n = len(pnl); w = int((pnl>0).sum())
    print(f"  {label:<52} N={n:>4} ({n/yrs:>4.0f}/yr)  win={w/n:6.1%}  mean={pnl.mean():+6.2f}  med={pnl.median():+6.2f}  std={pnl.std():5.1f}  t={tstat(pnl):5.2f}  p={ttest_1samp(pnl,0,alternative='greater').pvalue:.4f}")

hdr("1. IS IT JUST LONG BIAS? unconditional 10:00->close drift, and the fade split by direction after removing that drift")
drift = (G['close'] - G['P_1000'])
print(f"  Unconditional 10:00->16:15 drift, all days: mean {drift.mean():+.2f} pts (t={tstat(drift):.2f}); up-gap days {int((G['gap_dir']>0).sum())}, down-gap days {int((G['gap_dir']<0).sum())}")
adj = G['fade_pnl'] - (-G['gap_dir']) * drift.mean()
summ('fade, drift-adjusted, gap UP (short)', adj[G['gap_dir']>0]); summ('fade, drift-adjusted, gap DOWN (long)', adj[G['gap_dir']<0])
# the fade is net short (more up gaps): what did an always-long 10:00->close position earn?
summ('always LONG 10:00->close (benchmark)', drift); summ('always SHORT 10:00->close', -drift)

hdr("2. COSTS AND DOLLAR TERMS (1 contract, entry 10:00, exit 16:15, no stop)")
slip = 0.50; comm_mes = 1.50; comm_es = 4.50   # 1 tick each side on ES; round-trip commissions incl. exchange fees (approx)
net = G['fade_pnl'] - slip
print(f"  Gross mean {G['fade_pnl'].mean():+.2f} pts/trade -> net of 2 ticks slippage {net.mean():+.2f} pts/trade (t={tstat(net):.2f})")
for name, mult, comm in [('MES', 5, comm_mes), ('ES', 50, comm_es)]:
    dollars = net*mult - comm
    eq = dollars.cumsum(); dd = (eq - eq.cummax()).min()
    print(f"  {name}: ${dollars.mean():+.0f}/trade  ${dollars.sum()/yrs:+,.0f}/yr  max drawdown ${dd:+,.0f}  worst day ${dollars.min():+,.0f}  best day ${dollars.max():+,.0f}")
sh = net.mean()/net.std()*np.sqrt(len(net)/yrs)
print(f"  Annualised Sharpe (net, per-trade mean/std x sqrt(trades/yr)): {sh:.2f}")

hdr("3. MONTHLY CONSISTENCY")
m = G['fade_pnl'].groupby([G.index.year, G.index.month]).agg(['sum','count'])
m.index = [f"{y}-{mo:02d}" for y, mo in m.index]
pos = (m['sum']>0).mean()
print(f"  Months positive: {int((m['sum']>0).sum())}/{len(m)} ({pos:.0%}).  Median month {m['sum'].median():+.0f} pts; worst {m['sum'].min():+.0f} ({m['sum'].idxmin()}); best {m['sum'].max():+.0f} ({m['sum'].idxmax()})")
print("  " + "  ".join(f"{k}:{v:+.0f}" for k, v in m['sum'].items()))

hdr("4. VIX FILTER (post-hoc hypothesis — the project already showed VIX predicts morning range)")
summ('VIX >= 15 (prior close)', G.loc[G['vix']>=15, 'fade_pnl']); summ('VIX < 15', G.loc[G['vix']<15, 'fade_pnl'])
summ('VIX >= 15 & |gap| >= 0.10%', G.loc[(G['vix']>=15)&(G['absgap']>=0.10), 'fade_pnl'])
summ('VIX >= 15, 2024 only', G.loc[(G['vix']>=15)&(G['year']==2024), 'fade_pnl'])
summ('VIX >= 15, 2025 only', G.loc[(G['vix']>=15)&(G['year']==2025), 'fade_pnl'])
summ('VIX >= 15, 2026 only', G.loc[(G['vix']>=15)&(G['year']==2026), 'fade_pnl'])
print(f"  Share of days with VIX>=15: {(G['vix']>=15).mean():.0%}")

hdr("5. CLASSIC GAP-FILL STATISTICS (did price touch yesterday's close at any point 09:30-16:15?)")
day_hi = np.fmax(G['hi30'], G['hi_after']); day_lo = np.fmin(G['lo30'], G['lo_after'])
filled = np.where(G['gap_dir']>0, day_lo <= G['prev_close'], day_hi >= G['prev_close'])
G['filled'] = filled
filled_by10 = np.where(G['gap_dir']>0, G['lo30'] <= G['prev_close'], G['hi30'] >= G['prev_close'])
print(f"  Gap filled same day (any time): {filled.mean():.1%}   filled already by 10:00: {filled_by10.mean():.1%}")
print("  By |gap| bin:")
for b, s in G.groupby('gap_bin', observed=True):
    fb = np.where(s['gap_dir']>0, np.fmin(s['hi30']*0+s['lo30'], s['lo_after']) <= s['prev_close'], np.fmax(s['hi30'], s['hi_after']) >= s['prev_close'])
    print(f"    {b:<10} N={len(s):>3}  filled={s['filled'].mean():5.1%}  fade mean={s['fade_pnl'].mean():+6.2f}")
# on days NOT yet filled by 10:00, does the fade do better (the gap is still 'open')?
nf = ~filled_by10
summ('fade when gap NOT yet filled by 10:00', G.loc[nf, 'fade_pnl']); summ('fade when gap already filled by 10:00', G.loc[~nf, 'fade_pnl'])

hdr("6. SIMPLE 'WHAT IF' — fade the gap from the 09:30 open (no waiting), all days")
open_fade = (G['close'] - G['open']) * (-G['gap_dir'])
summ('open->16:15 fade', open_fade)
summ('open->16:15 fade, |gap|>=0.10%', open_fade[G['absgap']>=0.10])

# chart data for the report
eq = G['fade_pnl'].cumsum()
chart = {
  'dates': [d.strftime('%Y-%m-%d') for d in G.index],
  'equity_fade': [round(float(v),1) for v in eq],
  'equity_momentum_prior_best': None,
  'yearly': {int(y): round(float(v),0) for y, v in G.groupby('year')['fade_pnl'].sum().items()},
  'gap_bins': [(str(b), int(len(s)), round(float(s['fade_pnl'].mean()),2), round(float(s['fade_pnl'].median()),2)) for b, s in G.groupby('gap_bin', observed=True)],
}
# equity of the old headline traded as futures (best-40 set) for contrast
D = pd.read_csv(f"{SP}/daytable.csv", parse_dates=['date']).set_index('date').sort_index()
D['wide'] = D['range_pct'] >= D['range_pct'].median()
D['prior_reversal'] = np.where(D['prior_init_dir']=='above', D['d10_pct'] < 0, D['d10_pct'] > 0)
old = D[D['wide'] & D['prior_reversal'] & (D['abs10']>0.30)]
chart['old_dates'] = [d.strftime('%Y-%m-%d') for d in old.index]
chart['equity_old_strong'] = [round(float(v),1) for v in old['fut_pnl'].cumsum()]
json.dump(chart, open(f"{SP}/chart.json", 'w'))
print("\n[chart data saved]")
