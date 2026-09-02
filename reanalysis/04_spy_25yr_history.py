"""Long-history test of 'fade the overnight gap, open -> close' on SPY daily data (Yahoo), 2000-2026.
Only needs Open, Close, prev Close. VIX prior close for regime split. Ex-dividend days excluded (gap contaminated)."""
import os
SP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"); os.makedirs(SP, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import warnings, json, numpy as np, pandas as pd
warnings.filterwarnings('ignore'); pd.set_option('display.width', 220)
import yfinance as yf

def tstat(x): x = pd.Series(x).dropna(); return x.mean()/(x.std()/np.sqrt(len(x)))
def summ(label, pnl):
    pnl = pd.Series(pnl).dropna(); n = len(pnl); w = int((pnl>0).sum())
    print(f"  {label:<40} N={n:>5}  win={w/n:6.1%}  mean={pnl.mean()*100:+6.1f} bp  med={pnl.median()*100:+6.1f} bp  std={pnl.std()*100:5.1f}  t={tstat(pnl):5.2f}")

spy = yf.download('SPY', start='1999-01-01', auto_adjust=False, progress=False)
if isinstance(spy.columns, pd.MultiIndex): spy.columns = spy.columns.get_level_values(0)
vix = yf.download('^VIX', start='1999-01-01', auto_adjust=False, progress=False)
if isinstance(vix.columns, pd.MultiIndex): vix.columns = vix.columns.get_level_values(0)
divs = yf.Ticker('SPY').dividends
print(f"SPY rows {len(spy)}  {spy.index.min().date()} -> {spy.index.max().date()};  VIX rows {len(vix)};  ex-div dates {len(divs)}")

s = spy[['Open','High','Low','Close']].copy()
s.index = pd.to_datetime(s.index).tz_localize(None)
s['prev_close'] = s['Close'].shift(1)
s['days_since'] = s.index.to_series().diff().dt.days
s['gap_pct'] = (s['Open'] - s['prev_close']) / s['prev_close'] * 100
s['gap_dir'] = np.sign(s['gap_pct'])
s['oc_pct'] = (s['Close'] - s['Open']) / s['Open'] * 100
s['fade'] = s['oc_pct'] * (-s['gap_dir'])
s['vix_prev'] = vix['Close'].reindex(s.index).shift(1)
exdiv = pd.to_datetime(divs.index).tz_localize(None)
s['exdiv'] = s.index.isin(exdiv)
s['year'] = s.index.year

# data-quality flag: years where many opens == prev close (Yahoo's early open data is unreliable)
zero = (s['gap_pct']==0).groupby(s['year']).mean()
bad_years = zero[zero > 0.10].index.tolist()
print(f"  Years with >10% zero gaps (suspect open data, excluded): {bad_years}")
S = s[(s['days_since']<=5) & (~s['exdiv']) & (s['gap_dir']!=0) & (~s['year'].isin(bad_years))].copy()
print(f"  Usable days: {len(S)}  ({S.index.min().date()} -> {S.index.max().date()})")

print("\n=== OVERALL: fade the gap, open -> close (returns in basis points of price; 10 bp on ES 5500 = 5.5 pts) ===")
summ('ALL days', S['fade'])
summ('2000-2009', S.loc[S['year']<=2009, 'fade']); summ('2010-2019', S.loc[(S['year']>=2010)&(S['year']<=2019), 'fade'])
summ('2020-2023', S.loc[(S['year']>=2020)&(S['year']<=2023), 'fade']); summ('2024-2026 (the ES sample period)', S.loc[S['year']>=2024, 'fade'])
print("\n=== BY YEAR ===")
yr = S.groupby('year')['fade'].agg(['count','mean','median', lambda x: (x>0).mean()])
yr.columns = ['N','mean_bp','median_bp','win']; yr['mean_bp']*=100; yr['median_bp']*=100
yr['t'] = S.groupby('year')['fade'].apply(tstat)
print(yr.round(2).to_string())
print(f"\n  Years positive: {int((yr['mean_bp']>0).sum())}/{len(yr)}")

print("\n=== BY |GAP| BIN (all years) ===")
S['gap_bin'] = pd.cut(S['gap_pct'].abs(), [0,0.10,0.20,0.30,0.50,0.80,1.5,99], labels=['<0.10','0.10-0.20','0.20-0.30','0.30-0.50','0.50-0.80','0.80-1.5','>1.5'])
for b, g in S.groupby('gap_bin', observed=True): summ(f'  |gap| {b}%', g['fade'])
print("\n=== BY DIRECTION ===")
summ('gap UP -> short', S.loc[S['gap_dir']>0,'fade']); summ('gap DOWN -> long', S.loc[S['gap_dir']<0,'fade'])
summ('always long open->close (benchmark)', S['oc_pct'])
print("\n=== BY VIX (prior close) ===")
S['vix_band'] = pd.cut(S['vix_prev'], [0,15,20,25,35,999], labels=['<15','15-20','20-25','25-35','>35'])
for b, g in S.groupby('vix_band', observed=True): summ(f'  VIX {b}', g['fade'])
summ('VIX >= 15', S.loc[S['vix_prev']>=15,'fade']); summ('VIX < 15', S.loc[S['vix_prev']<15,'fade'])
print("\n=== ROLLING: is the effect stable or decaying? 3-year windows ===")
for y0 in range(2000, 2025, 3):
    g = S[(S['year']>=y0)&(S['year']<=y0+2)]
    if len(g): summ(f'  {y0}-{y0+2}', g['fade'])
print("\n=== GAP-FILL RATE (price touched prev close during the day) ===")
filled = np.where(S['gap_dir']>0, S['Low']<=S['prev_close'], S['High']>=S['prev_close'])
print(f"  all: {filled.mean():.1%}")
for b, g in S.groupby('gap_bin', observed=True):
    f = np.where(g['gap_dir']>0, g['Low']<=g['prev_close'], g['High']>=g['prev_close']); print(f"    |gap| {b:<9} filled {f.mean():5.1%}  N={len(g)}")

# chart data
eq = S['fade'].cumsum()
json.dump({'dates': [d.strftime('%Y-%m-%d') for d in S.index], 'equity_pct': [round(float(v),2) for v in eq],
           'yearly_bp': {int(k): round(float(v),1) for k, v in yr['mean_bp'].items()},
           'yearly_t': {int(k): round(float(v),2) for k, v in yr['t'].items()},
           'yearly_n': {int(k): int(v) for k, v in yr['N'].items()}}, open(f"{SP}/spy_chart.json",'w'))
S.to_csv(f"{SP}/spy_table.csv")
print("\n[spy data saved]")
