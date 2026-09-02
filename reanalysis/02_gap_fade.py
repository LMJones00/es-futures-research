"""Stage 2: the prior best subset in futures terms; gap-fade lead tested properly."""
import os
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"); os.makedirs(SP, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import warnings, numpy as np, pandas as pd
from scipy.stats import binomtest, ttest_1samp
warnings.filterwarnings('ignore'); pd.set_option('display.width', 220); pd.set_option('display.max_columns', 60)

D = pd.read_csv(f"{SP}/daytable.csv", parse_dates=['date']).set_index('date').sort_index()
years_span = (D.index.max() - D.index.min()).days / 365.25
def hdr(t): print("\n" + "="*100 + f"\n{t}\n" + "="*100)
def tstat(x): x = pd.Series(x).dropna(); return x.mean()/(x.std()/np.sqrt(len(x))) if len(x) > 2 else np.nan
def summ(label, pnl):
    pnl = pd.Series(pnl).dropna(); n = len(pnl)
    if n == 0: print(f"  {label:<48} N=0"); return
    w = int((pnl > 0).sum()); r = binomtest(w, n, 0.5).proportion_ci(0.95)
    p = ttest_1samp(pnl, 0, alternative='greater').pvalue
    print(f"  {label:<48} N={n:>4} ({n/years_span:>4.0f}/yr)  win={w/n:6.1%} [{r.low:.0%}-{r.high:.0%}]  mean={pnl.mean():+6.2f}  med={pnl.median():+6.2f}  std={pnl.std():5.1f}  t={tstat(pnl):5.2f}  p={p:.4f}")

# ─────────────────────────────────────────────────────────────────────────────
hdr("A. THE PRIOR 'BEST' SUBSETS, RE-SCORED AS A FUTURES TRADE ENTERED AT 10:00")
D['wide'] = D['range_pct'] >= D['range_pct'].median()
D['prior_reversal'] = np.where(D['prior_init_dir']=='above', D['d10_pct'] < 0, D['d10_pct'] > 0)
sets = {
  'Wide + Reversal (prior 127 / 60.6%)':              D['wide'] & D['prior_reversal'],
  'Strong drift (prior 63 / 69.8%)':                  D['wide'] & D['prior_reversal'] & (D['abs10']>0.30),
  'Strong + nonQ4 (prior 46 / 76.1%)':                D['wide'] & D['prior_reversal'] & (D['abs10']>0.30) & ~D['is_q4'],
  'Strong + nonQ4 + notThu (prior 39 / 76.9%)':       D['wide'] & D['prior_reversal'] & (D['abs10']>0.30) & ~D['is_q4'] & ~D['is_thu'],
}
print(f"  {'subset':<48} {'N':>4}  {'prior money_made':>16}  {'already past strike @10am':>26}  {'fut win':>8}  {'mean pts':>9}  {'med':>6}  {'t':>5}")
for k, m in sets.items():
    s = D[m]
    print(f"  {k:<48} {len(s):>4}  {s['prior_won'].mean():>16.1%}  {(s['past_strike_at10']>0).mean():>26.1%}  {s['fut_win'].mean():>8.1%}  {s['fut_pnl'].mean():>+9.2f}  {s['fut_pnl'].median():>+6.1f}  {tstat(s['fut_pnl']):>5.2f}")
best = D[sets['Strong + nonQ4 + notThu (prior 39 / 76.9%)']]
print(f"\n  On the best-40 set: median distance already past the near-money strike at 10:00 = {best['past_strike_at10'].median():.1f} pts;")
print(f"  of the {int(best['prior_won'].sum())} 'wins', {int(((best['prior_won']==1)&(best['fut_pnl']<=0)).sum())} were days where the futures trade from 10:00 LOST money (price gave back some, but not all, of the head start).")

# ─────────────────────────────────────────────────────────────────────────────
hdr("B. GAP SANITY — consecutive-day gaps only; are the biggest gaps real events or contract-roll artifacts?")
D['days_since_prev'] = D.index.to_series().diff().dt.days
G = D[(D['days_since_prev'] <= 4) & D['gap_pct'].notna()].copy()
print(f"  Days with a consecutive prior trading day: {len(G)} of {len(D)}")
top = G['gap_pct'].abs().sort_values(ascending=False).head(14)
print("  Largest |gaps| (%):")
for d, v in top.items():
    r = G.loc[d]; print(f"    {d.date()}  gap={r['gap_pct']:+.2f}%  prev_close={r['prev_close']:.2f} open={r['open']:.2f}  vix={r['vix']:.1f}  dow={r['dow']}")
print("  |gap| percentiles (%):", G['gap_pct'].abs().quantile([.25,.5,.75,.9,.99]).round(3).to_dict())

# ─────────────────────────────────────────────────────────────────────────────
hdr("C. GAP FADE FROM 10:00 — at 10:00 trade AGAINST the overnight gap direction, hold to 16:15")
G['gap_dir'] = np.sign(G['gap_pct'])
G = G[G['gap_dir'] != 0]
G['fade_pnl'] = (G['close'] - G['P_1000']) * (-G['gap_dir'])
G['fade_win'] = G['fade_pnl'] > 0
G['absgap'] = G['gap_pct'].abs()
G['gap_bin'] = pd.cut(G['absgap'], [0,0.10,0.20,0.30,0.50,0.80,99], labels=['<0.10','0.10-0.20','0.20-0.30','0.30-0.50','0.50-0.80','>0.80'])
summ('ALL days (pre-specified, single test)', G['fade_pnl'])
print("\n  By |gap| bin:")
for b, s in G.groupby('gap_bin', observed=True): summ(f'  |gap| {b}%', s['fade_pnl'])
print("\n  Cumulative |gap| > X:")
for th in [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.75]: summ(f'  |gap| > {th:.2f}%', G.loc[G['absgap']>th, 'fade_pnl'])
print("\n  By gap direction:")
for dname, s in [('gap UP -> short from 10:00', G[G['gap_dir']>0]), ('gap DOWN -> long from 10:00', G[G['gap_dir']<0])]: summ(dname, s['fade_pnl'])
print("\n  By year:")
for y, s in G.groupby('year'): summ(f'  {y}', s['fade_pnl'])
h = len(G)//2
summ('  First half (chronological)', G['fade_pnl'].iloc[:h]); summ('  Second half', G['fade_pnl'].iloc[h:])
tariff = (G.index >= '2025-04-02') & (G.index <= '2025-04-11')
summ('  Excluding 2025-04-02..04-11 (tariff shock)', G.loc[~tariff, 'fade_pnl'])
summ('  Excluding all of April 2025', G.loc[~((G['year']==2025)&(G['month']==4)), 'fade_pnl'])
print("\n  By VIX band:")
G['vix_band'] = pd.cut(G['vix'], [0,15,20,25,35,999], labels=['<15','15-20','20-25','25-35','>35'])
for b, s in G.groupby('vix_band', observed=True): summ(f'  VIX {b}', s['fade_pnl'])
print("\n  By day of week:")
for dname in ['Monday','Tuesday','Wednesday','Thursday','Friday']: summ(f'  {dname}', G.loc[G['dow']==dname, 'fade_pnl'])
print("\n  Gap-and-go vs gap-fill at 10:00 (has price already reversed the gap by 10:00?)  x |gap| bin — mean pts (N):")
G['state10'] = np.where(G['dir10']==G['gap_dir'], 'gap-and-go', np.where(G['dir10']==-G['gap_dir'], 'gap-filling', 'flat'))
pt = G.pivot_table(index='state10', columns='gap_bin', values='fade_pnl', aggfunc=['mean','count'], observed=True)
print(pt.round(1).to_string())
for sname in ['gap-and-go','gap-filling']: summ(f'  {sname} (all gap sizes)', G.loc[G['state10']==sname, 'fade_pnl'])
srt = G['fade_pnl'].sort_values(ascending=False)
print(f"\n  Concentration: total={srt.sum():+.0f} | top5={srt.head(5).sum():+.0f} | bottom5={srt.tail(5).sum():+.0f} | total ex-top5={srt.sum()-srt.head(5).sum():+.0f} | total ex-top10={srt.sum()-srt.head(10).sum():+.0f}")
eq = G['fade_pnl'].cumsum(); dd = (eq - eq.cummax()).min()
print(f"  Equity: final {eq.iloc[-1]:+.0f} pts over {len(G)} days; max drawdown {dd:+.0f} pts; year-end cum: {[(int(y), round(float(v))) for y, v in G.groupby('year')['fade_pnl'].sum().cumsum().items()]}")
print(f"  Worst 5 days: {', '.join(f'{v:+.0f}' for v in srt.tail(5))} | Best 5: {', '.join(f'{v:+.0f}' for v in srt.head(5))}")
print(f"  Trimmed mean (drop top/bottom 2.5%): {G['fade_pnl'].sort_values().iloc[int(len(G)*.025):-int(len(G)*.025)].mean():+.2f}")

# permutation: sign-flip each day's (close - P10), search over |gap| thresholds AND entry-state splits
hdr("C2. SELECTION-ADJUSTED TEST — random sign flips, best t over the threshold family {0,.1,.2,.3,.4,.5} x {all, gap-and-go, gap-filling}")
rng = np.random.default_rng(1)
raw = (G['close'] - G['P_1000']).values; gd = -G['gap_dir'].values; ag = G['absgap'].values; st = G['state10'].values
fam = []
for th in [0.0,0.10,0.20,0.30,0.40,0.50]:
    for s in [None,'gap-and-go','gap-filling']:
        m = ag > th
        if s: m &= (st == s)
        if m.sum() >= 40: fam.append(m)
def best_t(pnl): return max(tstat(pnl[m]) for m in fam)
obs = best_t(raw*gd); single = tstat(raw*gd)
mx = np.array([best_t(raw*gd*rng.choice([-1,1], size=len(raw))) for _ in range(3000)])
print(f"  Family size {len(fam)}.  Pre-specified all-days t = {single:.2f}.  Best t in family = {obs:.2f}.")
print(f"  Null (random flips): median best-t {np.median(mx):.2f}, 95th {np.percentile(mx,95):.2f}, 99th {np.percentile(mx,99):.2f}.  P(best >= observed) = {(mx>=obs).mean():.4f}")
# also a time-block shuffle (preserves clustering): flip signs in blocks of 10 consecutive days
mxb = []
nb = int(np.ceil(len(raw)/10))
for _ in range(3000):
    f = np.repeat(rng.choice([-1,1], size=nb), 10)[:len(raw)]
    mxb.append(best_t(raw*gd*f))
mxb = np.array(mxb)
print(f"  Block-flip null (10-day blocks): 95th {np.percentile(mxb,95):.2f}, 99th {np.percentile(mxb,99):.2f}.  P(best >= observed) = {(mxb>=obs).mean():.4f}")

# ─────────────────────────────────────────────────────────────────────────────
hdr("D. ENTRY-TIME SWEEP for the gap fade (hold to 16:15) — is 10:00 special, or is this just 'fade the gap at the open'?")
print(f"  {'entry':>6} | {'all: N':>6} {'win':>6} {'mean':>7} {'t':>5} | {'|gap|>0.30%: N':>14} {'win':>6} {'mean':>7} {'t':>5} | {'|gap|>0.50%: N':>14} {'win':>6} {'mean':>7} {'t':>5}")
for t in ['open','0935','0940','0945','0950','1000','1015','1030','1045','1100','1130','1200','1300','1400','1500']:
    P = G['open'] if t == 'open' else G['P_'+t]
    pnl = (G['close'] - P) * (-G['gap_dir'])
    a = pnl.notna(); b = a & (G['absgap']>0.30); c = a & (G['absgap']>0.50)
    lbl = '09:30' if t=='open' else f'{t[:2]}:{t[2:]}'
    print(f"  {lbl:>6} | {a.sum():>6} {(pnl[a]>0).mean():>6.1%} {pnl[a].mean():>+7.2f} {tstat(pnl[a]):>5.2f} | {b.sum():>14} {(pnl[b]>0).mean():>6.1%} {pnl[b].mean():>+7.2f} {tstat(pnl[b]):>5.2f} | "
          f"{c.sum():>14} {(pnl[c]>0).mean():>6.1%} {pnl[c].mean():>+7.2f} {tstat(pnl[c]):>5.2f}")

hdr("E. EXIT-TIME SWEEP for the gap fade entered at 10:00 (all days)")
print(f"  {'exit':>6} {'N':>4} {'win':>7} {'mean':>7} {'med':>7} {'std':>6} {'t':>5}")
for x in ['1030','1100','1130','1200','1230','1300','1330','1400','1430','1500','1530','1600','1615']:
    pnl = (G['P_'+x] - G['P_1000']) * (-G['gap_dir']); ok = pnl.notna()
    print(f"  {x[:2]}:{x[2:]} {ok.sum():>4} {(pnl[ok]>0).mean():>7.1%} {pnl[ok].mean():>+7.2f} {pnl[ok].median():>+7.2f} {pnl[ok].std():>6.1f} {tstat(pnl[ok]):>5.2f}")

hdr("F. SINGLE-VARIABLE VERSION — fade the cumulative move since yesterday's close (prev_close -> 10:00)")
G['cum10'] = (G['P_1000'] - G['prev_close']) / G['prev_close'] * 100
G['cum_dir'] = np.sign(G['cum10'])
G['cum_fade'] = (G['close'] - G['P_1000']) * (-G['cum_dir'])
summ('ALL days', G['cum_fade'])
G['cum_bin'] = pd.cut(G['cum10'].abs(), [0,0.15,0.30,0.50,0.80,1.2,99], labels=['<0.15','0.15-0.30','0.30-0.50','0.50-0.80','0.80-1.2','>1.2'])
for b, s in G.groupby('cum_bin', observed=True): summ(f'  |move since prev close| {b}%', s['cum_fade'])
for th in [0.3, 0.5, 0.8]: summ(f'  cumulative |move| > {th}%', G.loc[G['cum10'].abs()>th, 'cum_fade'])
print("\n  vs. the pure gap fade on the same days:")
for th in [0.3, 0.5, 0.8]: summ(f'  gap fade where cumulative |move| > {th}%', G.loc[G['cum10'].abs()>th, 'fade_pnl'])

hdr("G. MAE / STOP SWEEP for the gap fade from 10:00 (all days; bar highs/lows sampled ~15-min -> MAE is a lower bound)")
G['mae'] = np.where(G['gap_dir']<0, G['P_1000'] - G['lo_after'], G['hi_after'] - G['P_1000']).clip(min=0)
G['mfe'] = np.where(G['gap_dir']<0, G['hi_after'] - G['P_1000'], G['P_1000'] - G['lo_after']).clip(min=0)
print("  MAE pct:", G['mae'].quantile([.25,.5,.75,.9]).round(1).to_dict(), " MFE pct:", G['mfe'].quantile([.25,.5,.75,.9]).round(1).to_dict())
print(f"  {'stop':>8} {'stopped':>8} {'win':>6} {'mean':>7} {'total':>7} {'worst':>6} {'t':>5}")
for S in [10,15,20,25,30,40,50,75,100,1e9]:
    stopped = G['mae'] >= S; pnl = np.where(stopped, -S, G['fade_pnl'])
    print(f"  {('none' if S>1e8 else f'{S:.0f} pts'):>8} {stopped.mean():>8.1%} {(pnl>0).mean():>6.1%} {pnl.mean():>+7.2f} {pnl.sum():>+7.0f} {pnl.min():>+6.0f} {tstat(pnl):>5.2f}")

hdr("H. ROBUSTNESS TO DEFINITIONS — 16:00 regular close instead of 16:15, for both the gap and the exit")
G['gap_reg'] = G['open'] - G['close_reg'].shift(1)
ok = G['gap_reg'].notna() & (np.sign(G['gap_reg'])!=0)
summ('gap vs 16:00 prev close, exit 16:15', ((G['close'] - G['P_1000']) * (-np.sign(G['gap_reg'])))[ok])
summ('gap vs 16:15 prev close, exit 16:00', (G['close_reg'] - G['P_1000']) * (-G['gap_dir']))
summ('gap vs 16:00 prev close, exit 16:00', ((G['close_reg'] - G['P_1000']) * (-np.sign(G['gap_reg'])))[ok])

hdr("I. NADEX FRAMING of the gap fade — binary bought at 10:00 in the fade direction, strike ladder = 12-pt steps anchored on 'below'")
step = 12
k = np.floor((G['P_1000'] - G['below']) / step)
lad0 = G['below'] + k*step            # strike at or just below P10
# fade direction: -gap_dir. If fading DOWN (gap up), a 'sell' binary wins if close < strike; nearest strike at-or-above P10 = lad0+step (or lad0 if equal)
for j, lbl in [(0,'nearest strike on the far side of 10:00 price (slightly ITM, ~$55-65)'), (1,'one strike further (OTM, ~$25-45)'), (2,'two strikes further (deep OTM, ~$10-25)')]:
    up_strike   = lad0 + step*(1+j)            # for fading UP  (long): need close > strike above P10
    down_strike = lad0 - step*j                # for fading DOWN (short): need close < strike below-or-at P10
    win = np.where(G['gap_dir']<0, G['close'] > up_strike, G['close'] < down_strike)
    dist = np.where(G['gap_dir']<0, up_strike - G['P_1000'], G['P_1000'] - down_strike)
    print(f"  {lbl:<68} win={win.mean():.1%}  (median distance from 10:00 price: {np.median(dist):.1f} pts)   N={len(G)}")
    m = G['absgap'] > 0.30
    print(f"      |gap|>0.30% only:  win={win[m.values].mean():.1%}   N={m.sum()}")
print("  Breakeven for a binary bought at price $P is win rate P%. A ~$40 OTM binary needs >40% (+fees ~1-2%).")

G.to_csv(f"{SP}/gaptable.csv")
print("\n[gap table saved]")
