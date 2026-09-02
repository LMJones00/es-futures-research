"""
Exploratory re-analysis of the ES mean-reversion project.
Builds a fresh day-level table from cleaning.csv (all bars, incl. the 09:30 bar and 'equal' rows),
replicates the prior headline numbers, then tests a reframed signal and several new angles.
"""
import os
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"); os.makedirs(SP, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, warnings
import numpy as np
import pandas as pd
from scipy.stats import binomtest, ttest_1samp

warnings.filterwarnings('ignore')
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 50)


cl = pd.read_csv(f"{ROOT}/cleaning.csv")
clean = pd.read_csv(f"{ROOT}/clean.csv")

def hdr(t):
    print("\n" + "=" * 100 + f"\n{t}\n" + "=" * 100)

def ci(w, n):
    if n == 0: return (np.nan, np.nan)
    r = binomtest(int(w), int(n), 0.5).proportion_ci(0.95)
    return r.low, r.high

def wr_line(label, mask, col='mom_win'):
    sub = D[mask]
    n = len(sub); w = int(sub[col].sum())
    lo, hi = ci(w, n)
    p = binomtest(w, n, 0.5, alternative='greater').pvalue if n else np.nan
    print(f"  {label:<55} N={n:>4}  win={w/n if n else np.nan:6.1%}  CI=[{lo:5.1%},{hi:5.1%}]  p={p:.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Build day table
# ─────────────────────────────────────────────────────────────────────────────
cl['date'] = pd.to_datetime(cl['date'])
piv_close = cl.pivot_table(index='date', columns='time', values='candle_close_price', aggfunc='first')
piv_open  = cl.pivot_table(index='date', columns='time', values='candle_open_price',  aggfunc='first')

D = pd.DataFrame(index=piv_close.index)
D['open']  = piv_open['09:30:00']
day_first = cl.groupby('date').first()
D['above'] = day_first['above']; D['below'] = day_first['below']
D['close'] = piv_close['16:15:00']
D['close_reg'] = piv_close['16:00:00']

TIMES = ['09:30:01','09:31:00','09:35:00','09:40:00','09:45:00','09:50:00','09:55:00','10:00:00',
         '10:15:00','10:30:00','10:45:00','11:00:00','11:30:00','12:00:00','12:30:00','13:00:00',
         '13:30:00','14:00:00','14:30:00','15:00:00','15:30:00','16:00:00','16:15:00']
for t in TIMES:
    D['P_'+t[:5].replace(':','')] = piv_close[t] if t in piv_close.columns else np.nan
# the 09:30:01 "bar" is a tick snapshot; use its open (identical to close for tick rows)
D['P_0930tick'] = piv_open['09:30:01']

# first-30-min window (09:30 .. 10:00 inclusive) high/low, matching the prior analysis
tt = pd.to_datetime(cl['time'], format='%H:%M:%S').dt.time
import datetime as dt
w30 = cl[(tt >= dt.time(9,30)) & (tt <= dt.time(10,0))]
D['hi30'] = w30.groupby('date')['candle_high_price'].max()
D['lo30'] = w30.groupby('date')['candle_low_price'].min()
after10 = cl[tt > dt.time(10,0)]
D['hi_after'] = after10.groupby('date')['candle_high_price'].max()
D['lo_after'] = after10.groupby('date')['candle_low_price'].min()

# calendar
D['dow']  = D.index.day_name()
D['year'] = D.index.year
D['month']= D.index.month
D['dom']  = D.index.day
D['is_q4'] = D['month'].isin([10,11,12])
D['is_thu'] = D['dow'] == 'Thursday'

# VIX from clean.csv
vix = clean.groupby('date')['vix_close'].first(); vix.index = pd.to_datetime(vix.index)
D['vix'] = vix

# Replicate the prior day-level fields exactly: first row of clean.csv per day
clean['date'] = pd.to_datetime(clean['date'])
cf = clean.sort_values(['date','time']).groupby('date').first()
D['prior_init_dir'] = cf['initial_direction']
D['prior_won']      = (cf['money_made'] == 'yes').astype(float)
D['prior_philo']    = (cf['philo_result'] == 'correct').astype(float)
D['prior_open_used']= cf['market_open_09:30']
D['prior_first_time'] = cf['time']
D['prior_contract'] = cf['contract_location']

# previous close / gap
D = D.sort_index()
D['prev_close'] = D['close'].shift(1)
D['gap'] = D['open'] - D['prev_close']
D['gap_pct'] = D['gap'] / D['prev_close'] * 100

# Core derived
D['range_pct'] = (D['hi30'] - D['lo30']) / D['open'] * 100
D['d10']     = D['P_1000'] - D['open']
D['d10_pct'] = D['d10'] / D['open'] * 100
D['dir10']   = np.sign(D['d10'])
D['abs10']   = D['d10_pct'].abs()
D['co']      = D['close'] - D['open']
D['mom_win'] = (np.sign(D['co']) == D['dir10']) & (D['dir10'] != 0)          # close on same side of open as 10am
D['fut_pnl'] = (D['close'] - D['P_1000']) * D['dir10']                        # points, enter 10:00 hold to 16:15
D['fut_win'] = D['fut_pnl'] > 0
D['fut_pnl_reg'] = (D['close_reg'] - D['P_1000']) * D['dir10']
# near-money binary on the 10am side (the strike just past the open in the 10am direction)
D['strike10'] = np.where(D['dir10'] > 0, D['above'], D['below'])
D['bin_win']  = np.where(D['dir10'] > 0, D['close'] > D['strike10'], D['close'] < D['strike10'])
D['past_strike_at10'] = (D['P_1000'] - D['strike10']) * D['dir10']          # >0 means already ITM at 10am
D['otm_win']  = np.where(D['dir10'] > 0, D['close'] > D['strike10'] + 12, D['close'] < D['strike10'] - 12)

# tick-direction consistency
D['tick_dir'] = np.sign(D['P_0930tick'] - D['open'])
D['m1_dir']   = np.sign(D['P_0931'] - D['open'])
D['m5_dir']   = np.sign(D['P_0935'] - D['open'])

valid = D.dropna(subset=['open','close','P_1000','above','below','hi30','lo30']).copy()
valid = valid[valid['dir10'] != 0]
D = valid
years_span = (D.index.max() - D.index.min()).days / 365.25
print(f"Day table: {len(D)} days, {D.index.min().date()} -> {D.index.max().date()}  ({years_span:.2f} yrs)")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Replication of the prior headline numbers
# ─────────────────────────────────────────────────────────────────────────────
hdr("2. REPLICATION — does my table reproduce the prior findings?")
Dp = D.dropna(subset=['prior_won'])
print(f"  Prior 'tradeable' win rate (money_made)  : {Dp['prior_won'].mean():.1%}   (reported 37.0%)  N={len(Dp)}")
print(f"  Prior 'philosophical' win rate           : {Dp['prior_philo'].mean():.1%}   (reported 41.8%)")
med_range = D['range_pct'].median()
print(f"  Median first-30-min range                : {med_range:.3f}%   (reported 0.351%)")
D['wide'] = D['range_pct'] >= med_range
# prior 'reversal' = drift at 10am is against the prior initial direction
D['prior_reversal'] = np.where(D['prior_init_dir']=='above', D['d10_pct'] < 0, D['d10_pct'] > 0)
wr = D['wide'] & D['prior_reversal']
print(f"  Wide + Reversal                          : N={wr.sum()}  win={D.loc[wr,'prior_won'].mean():.1%}   (reported 127 / 60.6%)")
strong = wr & (D['abs10'] > 0.30)
print(f"  + Strong drift (>0.30%)                  : N={strong.sum()}  win={D.loc[strong,'prior_won'].mean():.1%}   (reported 63 / 69.8%)")
s2 = strong & ~D['is_q4']
print(f"  + non-Q4                                 : N={s2.sum()}  win={D.loc[s2,'prior_won'].mean():.1%}   (reported 46 / 76.1%)")
s3 = s2 & ~D['is_thu']
print(f"  + not Thursday                           : N={s3.sum()}  win={D.loc[s3,'prior_won'].mean():.1%}   (reported 39 / 76.9%)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Data-quality check: which bar defined the 'initial direction'?
# ─────────────────────────────────────────────────────────────────────────────
hdr("3. DATA QUALITY — what bar actually defined each day's 'initial direction'?")
print(D['prior_first_time'].value_counts().to_string())
bad = D[D['prior_open_used'] != D['open']]
print(f"\n  Days where the day-level reference open != the real 09:30 open: {len(bad)}")
if len(bad):
    print("  (these days' outcomes were computed against the PREVIOUS day's open — forward-fill bug on pre-market bars)")
    print(bad[['prior_first_time','prior_open_used','open','prior_init_dir']].head(8).to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 4. Is the 'initial direction' informative at all?
# ─────────────────────────────────────────────────────────────────────────────
hdr("4. IS THE FIRST TICK A SIGNAL OR NOISE?")
close_dir = np.sign(D['co'])
for name, col in [('first tick (09:30:01)', 'tick_dir'), ('first 1-min (09:31)', 'm1_dir'),
                  ('first 5-min (09:35)', 'm5_dir'), ('10:00 position', 'dir10')]:
    m = D[col].notna() & (D[col] != 0)
    agree_close = (D.loc[m, col] == close_dir[m]).mean()
    agree_10 = (D.loc[m, col] == D.loc[m, 'dir10']).mean()
    print(f"  {name:<24} agrees with 10:00 dir {agree_10:5.1%}   agrees with CLOSE dir {agree_close:5.1%}   N={m.sum()}")
print("\n  -> If the first tick agreed with the close only ~50% of the time, 'reversal of the initial move' carries no")
print("     information by itself; the informative half of the definition is where price sits at 10:00.")

# Prior reversal split on WIDE days, but scoring the trade by the 10am direction
hdr("4b. WIDE days — does it matter whether the first tick 'reversed' or 'confirmed'? (scoring by 10:00 direction)")
for lbl, m in [('Wide + first tick REVERSED  (prior signal set)', D['wide'] & D['prior_reversal']),
               ('Wide + first tick CONFIRMED (prior discarded set)', D['wide'] & ~D['prior_reversal'])]:
    sub = D[m]
    print(f"  {lbl:<52} N={len(sub):>3}  10am-momentum win={sub['mom_win'].mean():.1%}  futures win={sub['fut_win'].mean():.1%}  "
          f"mean pts={sub['fut_pnl'].mean():+.1f}")
for lbl, m in [('Wide + Strong(>0.30%) + first tick REVERSED', D['wide'] & D['prior_reversal'] & (D['abs10']>0.30)),
               ('Wide + Strong(>0.30%) + first tick CONFIRMED', D['wide'] & ~D['prior_reversal'] & (D['abs10']>0.30))]:
    sub = D[m]
    print(f"  {lbl:<52} N={len(sub):>3}  10am-momentum win={sub['mom_win'].mean():.1%}  futures win={sub['fut_win'].mean():.1%}  "
          f"mean pts={sub['fut_pnl'].mean():+.1f}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. The reframed signal: trade the 10:00 direction, all days
# ─────────────────────────────────────────────────────────────────────────────
hdr("5. REFRAMED SIGNAL — 'at 10:00, trade in the direction price sits vs the open' — ALL days")
print(f"  Overall: N={len(D)}  close-same-side-as-10am={D['mom_win'].mean():.1%}  futures(close vs 10am price) win={D['fut_win'].mean():.1%}  "
      f"mean pts={D['fut_pnl'].mean():+.2f}")
bins = [0, 0.05, 0.15, 0.30, 0.50, 0.80, 99]
labels = ['<0.05', '0.05-0.15', '0.15-0.30', '0.30-0.50', '0.50-0.80', '>0.80']
D['abs10_bin'] = pd.cut(D['abs10'], bins=bins, labels=labels)
g = D.groupby('abs10_bin', observed=True).agg(N=('mom_win','size'), close_same_side=('mom_win','mean'),
        fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean'), median_pts=('fut_pnl','median'),
        std_pts=('fut_pnl','std'), bin_win=('bin_win','mean'), otm_win=('otm_win','mean'))
g['t_stat'] = g['mean_pts'] / (g['std_pts'] / np.sqrt(g['N']))
print("\n  By |10:00 move| (% of open):")
print(g.round(3).to_string())

print("\n  Cumulative thresholds (|move| > X):")
print(f"  {'threshold':>10} {'N':>5} {'per yr':>7} {'same-side':>10} {'fut win':>8} {'mean pts':>9} {'med pts':>8} {'std':>6} {'t':>5} {'CI low':>7} {'CI high':>7}")
for th in [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60]:
    sub = D[D['abs10'] > th]
    n = len(sub); w = int(sub['fut_win'].sum()); lo, hi = ci(w, n)
    t = sub['fut_pnl'].mean() / (sub['fut_pnl'].std()/np.sqrt(n)) if n > 2 else np.nan
    print(f"  {th:>9.2f}% {n:>5} {n/years_span:>7.0f} {sub['mom_win'].mean():>10.1%} {w/n:>8.1%} {sub['fut_pnl'].mean():>+9.2f} "
          f"{sub['fut_pnl'].median():>+8.2f} {sub['fut_pnl'].std():>6.1f} {t:>5.2f} {lo:>7.1%} {hi:>7.1%}")

hdr("5b. Does the 30-min RANGE add anything once |10:00 move| is known?  (futures win rate / mean pts)")
D['range_q'] = pd.qcut(D['range_pct'], 3, labels=['tight','mid','wide'])
D['abs10_q'] = pd.cut(D['abs10'], bins=[0,0.15,0.30,99], labels=['<0.15','0.15-0.30','>0.30'])
ct_n  = pd.crosstab(D['range_q'], D['abs10_q'])
ct_wr = D.pivot_table(index='range_q', columns='abs10_q', values='fut_win', aggfunc='mean', observed=True)
ct_pt = D.pivot_table(index='range_q', columns='abs10_q', values='fut_pnl', aggfunc='mean', observed=True)
print("  N:\n", ct_n.to_string()); print("\n  futures win rate:\n", ct_wr.round(3).to_string()); print("\n  mean pts:\n", ct_pt.round(2).to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 6. Robustness of the reframed rule
# ─────────────────────────────────────────────────────────────────────────────
TH = 0.30
R = D[D['abs10'] > TH].copy()
hdr(f"6. ROBUSTNESS — rule: |10:00 move| > {TH}%  (N={len(R)})")
print("  By year:")
print(R.groupby('year').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean'),
                             total_pts=('fut_pnl','sum')).round(2).to_string())
half = len(R)//2
print(f"\n  First half : N={half}  win={R['fut_win'].iloc[:half].mean():.1%}  mean pts={R['fut_pnl'].iloc[:half].mean():+.2f}")
print(f"  Second half: N={len(R)-half}  win={R['fut_win'].iloc[half:].mean():.1%}  mean pts={R['fut_pnl'].iloc[half:].mean():+.2f}")
print("\n  By direction (up-days = long, down-days = short):")
print(R.groupby('dir10').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean')).round(3).to_string())
print("\n  By day of week:")
print(R.groupby('dow').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean'))
       .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday']).round(3).to_string())
print("\n  Q4 vs not:")
print(R.groupby('is_q4').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean')).round(3).to_string())
print("\n  By VIX band:")
R['vix_band'] = pd.cut(R['vix'], [0,15,20,25,35,999], labels=['<15','15-20','20-25','25-35','>35'])
print(R.groupby('vix_band', observed=True).agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean')).round(3).to_string())
# concentration
srt = R['fut_pnl'].sort_values(ascending=False)
print(f"\n  P&L concentration: total={srt.sum():+.0f} pts | top 5 days={srt.head(5).sum():+.0f} | bottom 5 days={srt.tail(5).sum():+.0f} | "
      f"total excluding top 5 = {srt.sum()-srt.head(5).sum():+.0f}")
print(f"  Worst 5 days (pts): {', '.join(f'{v:+.0f}' for v in srt.tail(5))}   Best 5: {', '.join(f'{v:+.0f}' for v in srt.head(5))}")
print(f"  Mean {R['fut_pnl'].mean():+.2f}, median {R['fut_pnl'].median():+.2f}, std {R['fut_pnl'].std():.1f}, "
      f"t={R['fut_pnl'].mean()/(R['fut_pnl'].std()/np.sqrt(len(R))):.2f}, p(one-sided)={ttest_1samp(R['fut_pnl'],0,alternative='greater').pvalue:.4f}")
eq = R['fut_pnl'].cumsum()
dd = (eq - eq.cummax()).min()
print(f"  Equity curve: final {eq.iloc[-1]:+.0f} pts, max drawdown {dd:+.0f} pts")
print("  Year-end cumulative:", {int(y): round(float(v),0) for y, v in R.groupby('year')['fut_pnl'].sum().cumsum().items()})

# ─────────────────────────────────────────────────────────────────────────────
# 7. Entry-time sweep
# ─────────────────────────────────────────────────────────────────────────────
hdr("7. ENTRY-TIME SWEEP — at time T, trade the direction of (P_T - open); hold to 16:15")
print(f"  {'T':>6} | {'all days: N':>11} {'win':>6} {'pts':>6} | {'|move|>0.30%: N':>15} {'win':>6} {'pts':>6} {'t':>5} | {'|move|>0.50%: N':>15} {'win':>6} {'pts':>6}")
for t in ['0935','0940','0945','0950','1000','1015','1030','1045','1100','1130','1200','1300','1400','1500']:
    P = D['P_'+t]; m = P.notna()
    mv = (P - D['open']) / D['open'] * 100; dr = np.sign(mv)
    pnl = (D['close'] - P) * dr; win = pnl > 0
    ok = m & (dr != 0)
    a = ok; b = ok & (mv.abs() > 0.30); c = ok & (mv.abs() > 0.50)
    tb = pnl[b].mean()/(pnl[b].std()/np.sqrt(b.sum())) if b.sum()>2 else np.nan
    print(f"  {t[:2]}:{t[2:]:>2} | {a.sum():>11} {win[a].mean():>6.1%} {pnl[a].mean():>+6.2f} | {b.sum():>15} {win[b].mean():>6.1%} {pnl[b].mean():>+6.2f} {tb:>5.2f} | "
          f"{c.sum():>15} {win[c].mean():>6.1%} {pnl[c].mean():>+6.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Exit-time sweep for entry at 10:00 (|move|>0.30%)
# ─────────────────────────────────────────────────────────────────────────────
hdr(f"8. EXIT-TIME SWEEP — enter 10:00 in 10:00 direction when |move|>{TH}%, exit at time X")
print(f"  {'exit':>6} {'N':>4} {'win':>7} {'mean pts':>9} {'median':>7} {'std':>6} {'t':>5}")
for x in ['1030','1100','1130','1200','1230','1300','1330','1400','1430','1500','1530','1600','1615']:
    P = R['P_'+x]; pnl = (P - R['P_1000']) * R['dir10']; ok = pnl.notna()
    t = pnl[ok].mean()/(pnl[ok].std()/np.sqrt(ok.sum()))
    print(f"  {x[:2]}:{x[2:]} {ok.sum():>4} {(pnl[ok]>0).mean():>7.1%} {pnl[ok].mean():>+9.2f} {pnl[ok].median():>+7.2f} {pnl[ok].std():>6.1f} {t:>5.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Overnight gap interaction
# ─────────────────────────────────────────────────────────────────────────────
hdr("9. OVERNIGHT GAP — does the gap direction interact with the 10:00 signal?")
G = D.dropna(subset=['gap_pct']).copy()
G['gap_dir'] = np.sign(G['gap_pct'])
G['gap_agree'] = np.where(G['gap_dir']==0, 'flat', np.where(G['gap_dir']==G['dir10'], 'gap-and-go (10am continues gap)', 'gap-fill (10am reverses gap)'))
G['gap_size'] = pd.cut(G['gap_pct'].abs(), [-1,0.10,0.30,0.60,99], labels=['<0.10','0.10-0.30','0.30-0.60','>0.60'])
print("  All days, by gap agreement:")
print(G.groupby('gap_agree').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean')).round(3).to_string())
print(f"\n  |10:00 move|>{TH}% only, by gap agreement:")
Gs = G[G['abs10']>TH]
print(Gs.groupby('gap_agree').agg(N=('fut_win','size'), fut_win=('fut_win','mean'), mean_pts=('fut_pnl','mean')).round(3).to_string())
print(f"\n  |10:00 move|>{TH}% — gap agreement x gap size (mean pts / N):")
print(Gs.pivot_table(index='gap_agree', columns='gap_size', values='fut_pnl', aggfunc=['mean','count'], observed=True).round(2).to_string())
# does the gap itself predict the day (gap fill rate)?
print("\n  Gap-fill base rate (close moves back toward prev close vs open) by gap size, all days:")
G['gap_filled_dir'] = np.sign(G['co']) == -G['gap_dir']
print(G[G['gap_dir']!=0].groupby('gap_size', observed=True).agg(N=('gap_filled_dir','size'), close_against_gap=('gap_filled_dir','mean')).round(3).to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 10. MAE / MFE and stop sweep (Section 20 proxy)  — caveat: bars are sampled ~every 15 min after 10:00
# ─────────────────────────────────────────────────────────────────────────────
hdr(f"10. MAE/MFE + STOP SWEEP — entry 10:00, |move|>{TH}%, hold to 16:15  (bar highs/lows sampled ~15-min: MAE is a LOWER bound)")
R['mae'] = np.where(R['dir10']>0, R['P_1000'] - R['lo_after'], R['hi_after'] - R['P_1000']).clip(min=0)
R['mfe'] = np.where(R['dir10']>0, R['hi_after'] - R['P_1000'], R['P_1000'] - R['lo_after']).clip(min=0)
print("  MAE (pts) percentiles:", R['mae'].quantile([.25,.5,.75,.9]).round(1).to_dict())
print("  MFE (pts) percentiles:", R['mfe'].quantile([.25,.5,.75,.9]).round(1).to_dict())
print("  MAE on winners vs losers:", R.groupby('fut_win')['mae'].median().round(1).to_dict())
print("  MAE as % of open — median:", (R['mae']/R['open']*100).median().round(3), "%")
print(f"\n  {'stop (pts)':>10} {'stopped %':>9} {'win %':>6} {'mean pts':>9} {'total pts':>9} {'worst':>6} {'t':>5}")
for S in [8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 1e9]:
    stopped = R['mae'] >= S
    pnl = np.where(stopped, -S, R['fut_pnl'])
    t = pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
    lbl = 'none' if S >= 1e8 else f'{S:.0f}'
    print(f"  {lbl:>10} {stopped.mean():>9.1%} {(pnl>0).mean():>6.1%} {pnl.mean():>+9.2f} {pnl.sum():>+9.0f} {pnl.min():>+6.0f} {t:>5.2f}")
print("\n  Stop as % of open (scales with price level):")
for Sp in [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
    S = Sp/100 * R['open']
    stopped = R['mae'] >= S
    pnl = np.where(stopped, -S, R['fut_pnl'])
    t = pnl.mean()/(pnl.std()/np.sqrt(len(pnl)))
    print(f"  {Sp:>9.2f}% {stopped.mean():>9.1%} {(pnl>0).mean():>6.1%} {pnl.mean():>+9.2f} {pnl.sum():>+9.0f} {pnl.min():>+6.0f} {t:>5.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# 11. Permutation test on the 76.9% headline
# ─────────────────────────────────────────────────────────────────────────────
hdr("11. HONESTY CHECK — how often does random relabeling of the 127 Wide+Reversal days produce a >=76.9% subset (N>=35)?")
W = D[D['wide'] & D['prior_reversal']].dropna(subset=['prior_won']).copy()
W['drift_bin'] = pd.cut(W['abs10'], [0,0.05,0.15,0.30,99], labels=[0,1,2,3]).astype(int)
dows = ['Monday','Tuesday','Wednesday','Thursday','Friday']
# family of filters actually searched in Sections 13-14: drift bin (4, or top bin), x Q4-excluded (2), x DOW-excluded (6)
masks = []
for db in [None, 0, 1, 2, 3]:
    for q4 in [False, True]:
        for dx in [None] + dows:
            m = np.ones(len(W), bool)
            if db is not None: m &= (W['drift_bin'] == db).values
            if q4: m &= (~W['is_q4']).values
            if dx: m &= (W['dow'] != dx).values
            if m.sum() >= 35: masks.append(m)
print(f"  Filter family size (N>=35): {len(masks)}   base rate in the 127-day set: {W['prior_won'].mean():.1%}")
rng = np.random.default_rng(0)
y = W['prior_won'].values.copy()
obs = max(y[m].mean() for m in masks)
hits = 0; NPERM = 3000
maxes = np.empty(NPERM)
for i in range(NPERM):
    rng.shuffle(y)
    maxes[i] = max(y[m].mean() for m in masks)
print(f"  Observed best subset win rate: {obs:.1%}")
print(f"  Under random relabeling, best-subset win rate: median {np.median(maxes):.1%}, 95th pct {np.percentile(maxes,95):.1%}")
print(f"  P(best subset >= 76.9% by chance) = {(maxes >= 0.769).mean():.3f}")
print("  -> This is the selection-adjusted p-value for the headline number.")

# Same honesty check for the reframed rule (threshold search only: 10 thresholds)
hdr("11b. Same check for the reframed rule — is |move|>0.30% cherry-picked among thresholds?")
ths = [0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.50,0.60]
def best_t(pnl, abs10):
    best = -1e9
    for th in ths:
        m = abs10 > th
        if m.sum() >= 40:
            best = max(best, pnl[m].mean()/(pnl[m].std()/np.sqrt(m.sum())))
    return best
obs_t = best_t(D['fut_pnl'].values, D['abs10'].values)
# permutation: randomly flip the sign of each day's direction (keeps the |move| structure, destroys the direction info)
pnl_raw = (D['close'] - D['P_1000']).values; abs10 = D['abs10'].values
maxt = np.empty(2000)
for i in range(2000):
    flips = rng.choice([-1,1], size=len(pnl_raw))
    maxt[i] = best_t(pnl_raw * flips, abs10)
print(f"  Observed best t-stat over {len(ths)} thresholds: {obs_t:.2f}")
print(f"  Under random direction flips: median {np.median(maxt):.2f}, 95th pct {np.percentile(maxt,95):.2f}, 99th {np.percentile(maxt,99):.2f}")
print(f"  P(best t >= observed by chance) = {(maxt >= obs_t).mean():.4f}")

# save the day table for follow-up
D.to_csv(f"{SP}/daytable.csv")
print("\n[day table saved]")
