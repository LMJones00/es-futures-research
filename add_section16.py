import json

with open('analysis.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

def code_cell(lines):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': lines}

def md_cell(lines):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': lines}

# ── Cell 75: Section 16 markdown header ──────────────────────────────────────
c75 = md_cell([
    '## Section 16: Early Entry Signal — Can We Get In Before 10am?\n\n',
    'The Section 15 binary pricing analysis showed that by 10am most Wide+Reversal days have already\n',
    'moved past the contract location — pushing the estimated entry price to ~$68–$75.\n',
    'The only filters with positive EV (Strong + non-Q4 + not Thu) clear the breakeven line by just ~$2/trade.\n\n',
    'This section asks: **is the reversal already visible before 10am?** If price is already pulling back\n',
    'at 9:40 or 9:45, we could enter while the binary is fairly priced (~$45–$55) and still\n',
    'capture most of the directional edge.\n\n',
    '- **16a:** Build 9:40 and 9:45 price snapshots; compute early reversal flags and estimated binary prices\n',
    '- **16b:** Signal precision — how well does 9:40 reversal predict the 10am drift?\n',
    '- **16c:** P&L comparison — 9:40 entry vs 10am entry, with and without calendar filters',
])

# ── Cell 76: 16a ─────────────────────────────────────────────────────────────
c76_src = '''\
# Section 16a: Price snapshots at 9:40 and 9:45; early reversal flags and binary price tiers
# Requires: early (cell 39), dm with tight_open / early_reversal (cell 46)

import datetime

early_s = early.sort_values(["date", "time_parsed"])
cut_940 = datetime.time(9, 40, 0)
cut_945 = datetime.time(9, 45, 0)

snap_940 = (early_s[early_s["time_parsed"] <= cut_940]
            .groupby("date")["candle_close_price"].last()
            .rename("price_940").reset_index())
snap_945 = (early_s[early_s["time_parsed"] <= cut_945]
            .groupby("date")["candle_close_price"].last()
            .rename("price_945").reset_index())

dm16 = dm.merge(snap_940, on="date", how="left").merge(snap_945, on="date", how="left")

# Drift pct at 9:40 and 9:45 (same formula as drift_pct in cell 39)
_open = "market_open_09:30"
dm16["drift_pct_940"] = (dm16["price_940"] - dm16[_open]) / dm16[_open] * 100
dm16["drift_pct_945"] = (dm16["price_945"] - dm16[_open]) / dm16[_open] * 100

# Early reversal flag: sign of drift opposes initial_direction
for rev_col, pct_col in [("early_rev_940", "drift_pct_940"), ("early_rev_945", "drift_pct_945")]:
    dm16[rev_col] = np.where(
        dm16["initial_direction"] == "above",
        dm16[pct_col] < 0,
        dm16[pct_col] > 0,
    )

# Progress ratio at each time (same formula as Section 13c / 15a)
_gap = dm16["diff_open_conLoc"].abs()
dm16["progress_ratio_940"]  = (dm16["price_940"] - dm16[_open]).abs() / _gap
dm16["progress_ratio_945"]  = (dm16["price_945"] - dm16[_open]).abs() / _gap
dm16["progress_ratio_1000"] = (dm16["drift_pct"].abs() / 100 * dm16[_open]) / _gap

# Estimated binary price at each time using same 5-tier map as Section 15a
_bins   = [-np.inf, 0.25, 0.50, 1.0, 1.5, np.inf]
_labels = ["Deep OTM (<25%)", "OTM (25-50%)", "Near-money (50-100%)", "Mod ITM (100-150%)", "Deep ITM (>150%)"]
_pmap   = {"Deep OTM (<25%)": 28, "OTM (25-50%)": 38, "Near-money (50-100%)": 48,
           "Mod ITM (100-150%)": 62, "Deep ITM (>150%)": 75}

for ratio_col, price_col in [
    ("progress_ratio_940",  "binary_price_940"),
    ("progress_ratio_945",  "binary_price_945"),
    ("progress_ratio_1000", "binary_price_1000"),
]:
    dm16[price_col] = pd.cut(dm16[ratio_col], bins=_bins, labels=_labels).map(_pmap).astype(float)

# Wide-open subset with bar data at both cut times
wide_dm16 = dm16[
    (dm16["tight_open"] == False) &
    dm16["price_940"].notna() &
    dm16["price_945"].notna()
].copy()

# Calendar flags (same as Section 14a)
wide_dm16["date_parsed"] = pd.to_datetime(wide_dm16["date"])
wide_dm16["month_num"]   = wide_dm16["date_parsed"].dt.month
wide_dm16["dow_name"]    = wide_dm16["date_parsed"].dt.day_name()
wide_dm16["is_q4"]       = wide_dm16["month_num"].isin([10, 11, 12])
wide_dm16["is_thursday"] = wide_dm16["dow_name"] == "Thursday"

print(f"Wide-open days with 9:40 and 9:45 bar data: {len(wide_dm16)}")
print()

# Price tier distribution comparison
print("Estimated binary price tier distribution by entry time:")
for label, rev_col, ratio_col, price_col in [
    ("9:40 entry (early_rev_940 days)",  "early_rev_940",  "progress_ratio_940",  "binary_price_940"),
    ("9:45 entry (early_rev_945 days)",  "early_rev_945",  "progress_ratio_945",  "binary_price_945"),
    ("10am entry (early_reversal days)", "early_reversal", "progress_ratio_1000", "binary_price_1000"),
]:
    sub = wide_dm16[wide_dm16[rev_col]].dropna(subset=[price_col])
    tiers = pd.cut(sub[ratio_col], bins=_bins, labels=_labels).value_counts().reindex(_labels, fill_value=0)
    mean_p = sub[price_col].mean()
    print(f"  {label} (N={len(sub)}, mean ~${mean_p:.0f}):")
    for t, n in tiers.items():
        pct = n / len(sub) if len(sub) > 0 else 0
        bar = "#" * int(pct * 30)
        print(f"    {t:<26} {n:>3}  ({pct:.0%})  {bar}")
    print()
'''

c76 = code_cell([line + '\n' for line in c76_src.split('\n')])

# ── Cell 77: 16b — signal precision ──────────────────────────────────────────
c77_src = '''\
# Section 16b: Signal precision -- how well does early reversal at 9:40/9:45 predict 10am drift?

total_10am = int(wide_dm16["early_reversal"].sum())
total_wide = len(wide_dm16)

print("Signal Precision Analysis (wide-open days only)")
print("=" * 72)
print(f"Total wide-open days: {total_wide}  |  10am drift days (current signal): {total_10am}")
print()

rows = []
for label, col in [("9:40 reversal", "early_rev_940"), ("9:45 reversal", "early_rev_945")]:
    flagged   = wide_dm16[wide_dm16[col]]
    confirmed = flagged[flagged["early_reversal"]]
    false_pos = flagged[~flagged["early_reversal"]]
    precision = len(confirmed) / len(flagged) if len(flagged) > 0 else 0
    recall    = len(confirmed) / total_10am if total_10am > 0 else 0
    rows.append({
        "Entry signal":               label,
        "N flagged":                  len(flagged),
        "Precision (->10am drift)":   f"{precision:.1%}",
        "Recall (% of drift days)":   f"{recall:.1%}",
        "Win rate (all flagged)":     f"{flagged['won'].mean():.1%}",
        "Win rate (confirmed only)":  f"{confirmed['won'].mean():.1%}" if len(confirmed) > 0 else "N/A",
        "Win rate (false pos only)":  f"{false_pos['won'].mean():.1%}" if len(false_pos) > 0 else "N/A",
    })

rev_10am = wide_dm16[wide_dm16["early_reversal"]]
rows.append({
    "Entry signal":               "10am reversal (baseline)",
    "N flagged":                  total_10am,
    "Precision (->10am drift)":   "100.0%",
    "Recall (% of drift days)":   "100.0%",
    "Win rate (all flagged)":     f"{rev_10am['won'].mean():.1%}",
    "Win rate (confirmed only)":  f"{rev_10am['won'].mean():.1%}",
    "Win rate (false pos only)":  "N/A",
})

print(pd.DataFrame(rows).to_string(index=False))
print()

# Confusion matrix: 9:40 signal vs 10am drift
ct = pd.crosstab(
    wide_dm16["early_rev_940"].map({True: "Rev at 9:40", False: "No rev at 9:40"}),
    wide_dm16["early_reversal"].map({True: "Drift at 10am", False: "No drift at 10am"}),
    margins=True,
)
print("Confusion matrix -- 9:40 signal vs 10am drift:")
print(ct.to_string())
print()
print("Top-left  = true positives: entered early, drift held through 10am")
print("Top-right = false positives: entered early, drift reversed before 10am")
print("Bot-left  = missed trades:  drift only visible at 10am, not yet at 9:40")
'''

c77 = code_cell([line + '\n' for line in c77_src.split('\n')])

# ── Cell 78: 16c — P&L comparison ────────────────────────────────────────────
c78_src = '''\
# Section 16c: P&L comparison -- 9:40 early entry vs 10am entry with calendar filters

def ev_row(mask, signal_label, entry_label, price_col):
    sub = wide_dm16[mask].dropna(subset=[price_col])
    if len(sub) == 0:
        return None
    wr    = sub["won"].mean()
    avg_p = sub[price_col].mean()
    ev    = wr * 100 - avg_p
    total = sub.apply(lambda r: (100 - r[price_col]) if r["won"] == 1 else -r[price_col], axis=1).sum()
    return {
        "Signal":            signal_label,
        "Entry":             entry_label,
        "N":                 len(sub),
        "Win Rate":          f"{wr:.1%}",
        "Breakeven $":       f"${wr*100:.0f}",
        "Avg Price":         f"${avg_p:.0f}",
        "EV/trade":          f"${ev:+.1f}",
        "Total P&L (2.1yr)": f"${total:+.0f}",
    }

rows = [
    ev_row(wide_dm16["early_rev_940"],
           "9:40 rev (all wide days)",        "9:40", "binary_price_940"),
    ev_row(wide_dm16["early_rev_940"] & ~wide_dm16["is_q4"] & ~wide_dm16["is_thursday"],
           "9:40 rev + non-Q4 + not Thu",     "9:40", "binary_price_940"),
    ev_row(wide_dm16["early_reversal"],
           "10am rev (all wide days)",         "10am", "binary_price_1000"),
    ev_row(wide_dm16["early_reversal"] & ~wide_dm16["is_q4"] & ~wide_dm16["is_thursday"],
           "10am rev + non-Q4 + not Thu",      "10am", "binary_price_1000"),
]

print("P&L Comparison: 9:40 early entry vs 10am entry")
print("=" * 80)
print(pd.DataFrame([r for r in rows if r]).to_string(index=False))
print()
print("Breakeven $ = win_rate x 100. Need to enter BELOW this price for positive EV.")
print("Avg Price uses same 5-tier estimate as Section 15a, applied at the entry time.")
print()

# Chart: price tier distribution at 9:40 vs 10am
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
_tier_prices = [28, 38, 48, 62, 75]
_tier_short  = ["Deep\nOTM\n($28)", "OTM\n($38)", "Near\nmoney\n($48)", "Mod\nITM\n($62)", "Deep\nITM\n($75)"]
_colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#2980b9"]

for ax, rev_col, ratio_col, entry_label in [
    (axes[0], "early_rev_940",  "progress_ratio_940",  "9:40 entry"),
    (axes[1], "early_reversal", "progress_ratio_1000", "10am entry"),
]:
    sub   = wide_dm16[wide_dm16[rev_col]].dropna(subset=[ratio_col])
    tiers = pd.cut(sub[ratio_col], bins=_bins, labels=_labels).value_counts().reindex(_labels, fill_value=0)
    bars  = ax.bar(_tier_short, tiers.values, color=_colors)
    for bar, cnt, p in zip(bars, tiers.values, _tier_prices):
        if cnt > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"N={cnt}", ha="center", va="bottom", fontsize=9)
    ax.set_title(f"Binary Price Tier Distribution\\n{entry_label} (N={len(sub)})", fontsize=11)
    ax.set_xlabel("Progress toward contract")
    ax.set_ylabel("Days")
    ax.set_ylim(0, max(tiers.values) * 1.3 + 1)

plt.suptitle("Entering Earlier Shifts Price Tiers from Deep ITM to Near-Money/OTM", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.show()
'''

c78 = code_cell([line + '\n' for line in c78_src.split('\n')])

# Append all 4 cells
nb['cells'].extend([c75, c76, c77, c78])
print(f'New cell count: {len(nb["cells"])}')

with open('analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print('Saved.')
