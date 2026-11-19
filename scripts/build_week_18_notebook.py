import json
import nbformat as nbf
from nbclient import NotebookClient

nb = nbf.v4.new_notebook()

cells = []

# ==============================================================================
# Cell 1: Markdown - Title & KPI Architecture
# ==============================================================================
cell1_md = """# Week 18 — KPI Development & Metric Framework (Path B)
**Phase 5 — Predictive / Alt Track | Milestone 5**  
**Project:** MassKara Festival Google Trends Interest & MNL-BCD Travel Price Surge Tracker

---

## 1. Problem Statement & KPI Architecture

### Core Problem Statement
> *"Is there a correlation between an uptick in Google Trends' Interest Over Time metric and MNL-BCD flight/BCD hotel price surges leading up to the Bacolod MassKara Festival in October?"*

### Target Audiences & Decision Mandates
1. **Budget-Conscious Travelers:** Pinpoint the optimal booking cutoff before airline revenue management algorithms trigger non-linear fare ratchets.
2. **Local Bacolod Hospitality Vendors & Businesses:** Distinguish casual viral search curiosity from commercial booking intent to optimize staff, pricing, and event inventory.
3. **Data Researchers:** Construct a reproducible empirical framework evaluating multi-modal pricing dynamics and lagged consumer interest transmission.

---

### The 5 Core KPIs Framework

| KPI # | KPI Name | Target Domain | Calculation / Formula | Audience Decision Supported | KPI vs. Vanity Distinction |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **KPI 1** | **Festival Price Premium Ratio (FPPR)** | Flights & Hotels | $\\text{FPPR}_t = \\frac{\\text{Fest Median}_t - \\text{Rolling Median}_t}{\\text{Rolling Median}_t} \\times 100\\%$ | Quantifies the pure "festival surcharge" above off-peak operational baselines. | **Not a Vanity Metric:** Controls for inflation, day-of-week noise, and seasonal baseline drift. |
| **KPI 2** | **Lead-Time Booking Penalty Index (LBPI)** | Flights | $\\text{LBPI}_t = \\frac{\\text{Flight Fest Min Price}_t}{\\text{Baseline Min Price (>20d)}}$ | Establishes concrete multiplier thresholds (e.g., $1.5\\times$, $2.0\\times$) for travelers. | **Not a Vanity Metric:** Plain PHP ignores relative purchasing power; index reveals escalating delay penalties. |
| **KPI 3** | **Search-to-Surge Elasticity & Lag Response** | Multi-Modal | $\\text{Spearman } \\rho(\\text{Trend}_{t-k}, \\text{Price}_t)$ & $\\frac{\\%\\Delta \\text{Price}_{1\\text{d}}}{\\%\\Delta \\text{Trend}_{1\\text{d}, t-k}}$ | Reveals whether public curiosity moves airline/hotel prices within 24–72 hours. | **Not a Vanity Metric:** Raw search index (0–100) measures curiosity; elasticity measures commercial pricing transmission. |
| **KPI 4** | **Day-over-Day Flight Surge Velocity ($\\Delta\\text{Flight}_{1\\text{d}}$)** | Flights | $\\Delta\\text{Flight}_{1\\text{d}} = \\text{Flight Fest Median}_t - \\text{Flight Fest Median}_{t-1}$ (₱) | Flags acute inflection points and irreversible revenue-management ratchet steps. | **Not a Vanity Metric:** Cumulative price conceals daily acceleration; velocity flags active algorithm runs. |
| **KPI 5** | **Day-over-Day Hotel Price Velocity ($\\Delta\\text{Hotel}_{1\\text{d}}$)** | Hotels | $\\Delta\\text{Hotel}_{1\\text{d}} = \\text{Hotel Fest Median}_t - \\text{Hotel Fest Median}_{t-1}$ (₱) | Tracks accommodation rate volatility against flight surge dynamics. | **Not a Vanity Metric:** Proves hotel pricing stickiness vs. airline hyper-volatility. |

> [!NOTE]
> **Data Scope Exclusion Audit:** In Week 17 data auditing, scraper quote counts (`hotel_quote_count`, `flight_quote_count`) were confirmed to reflect the static 20-result pagination ceiling of the SerpApi/Apify queries, rather than physical room or seat inventory. An "Inventory Squeeze Ratio" based on quote counts would be an uninformative pipeline artifact. This framework instead tracks real, non-truncated price and search dynamics.
"""
cells.append(nbf.v4.new_markdown_cell(cell1_md))

# ==============================================================================
# Cell 2: Code - Imports & Visual Styling
# ==============================================================================
cell2_code = """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr

# Visual configuration
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 130
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 11

print("Environment initialized with specialized KPI visualization standards.")
"""
cells.append(nbf.v4.new_code_cell(cell2_code))

# ==============================================================================
# Cell 3: Code - Data Ingestion & KPI Metric Engineering
# ==============================================================================
cell3_code = """# Load the consolidated master analytical dataset
df = pd.read_csv('../data/processed/masskara/analysis/master.csv', parse_dates=['date_collected'])
df = df.sort_values('date_collected').reset_index(drop=True)

# Filter for the pre-festival observation window (days_to_festival > 0)
# Note: days_to_festival == 0 represents post-festival rolling scrapes, which lack festival flight quotes
pre_fest = df[df['days_to_festival'] > 0].copy().reset_index(drop=True)

# ---------------------------------------------------------
# KPI 1: Festival Price Premium Ratio (FPPR in %)
# ---------------------------------------------------------
pre_fest['flight_fppr_pct'] = (pre_fest['flight_fest_median_price'] - pre_fest['flight_rolling_median_price']) / pre_fest['flight_rolling_median_price'] * 100
pre_fest['hotel_fppr_pct'] = (pre_fest['hotel_fest_median_price'] - pre_fest['hotel_rolling_median_price']) / pre_fest['hotel_rolling_median_price'] * 100

# ---------------------------------------------------------
# KPI 2: Lead-Time Booking Penalty Index (LBPI)
# ---------------------------------------------------------
# Establish baseline: median minimum ticket price during Advance Window (> 20 days)
advance_mask = pre_fest['days_to_festival'] > 20
advance_min_flight_baseline = pre_fest.loc[advance_mask, 'flight_fest_min_price'].median()
pre_fest['flight_lbpi'] = pre_fest['flight_fest_min_price'] / advance_min_flight_baseline

# Define Lead-Time Cohorts (matching Week 17 segmentation)
cohort_bins = [-1, 7, 20, 100]
cohort_labels = ['Surge Window (<=7d)', 'Mid Window (8-20d)', 'Advance Window (>20d)']
pre_fest['lead_cohort'] = pd.cut(pre_fest['days_to_festival'], bins=cohort_bins, labels=cohort_labels)

# ---------------------------------------------------------
# KPI 3: Search Elasticity & Lag Dynamics
# ---------------------------------------------------------
# 1-day percentage movements
pre_fest['flight_pct_chg_1d'] = pre_fest['flight_fest_median_price'].pct_change() * 100
pre_fest['hotel_pct_chg_1d'] = pre_fest['hotel_fest_median_price'].pct_change() * 100
pre_fest['trend_pct_chg_1d'] = pre_fest['trend_search_score'].pct_change() * 100

# ---------------------------------------------------------
# KPIs 4 & 5: Day-over-Day Price Velocity (PHP)
# flight_median_change_1d and hotel_median_change_1d are natively in master.csv
# ---------------------------------------------------------

print(f"Pre-festival observation span: {len(pre_fest)} daily records")
print(f"Tracking period: {pre_fest['date_collected'].min().strftime('%Y-%m-%d')} to {pre_fest['date_collected'].max().strftime('%Y-%m-%d')}")
print(f"Baseline Advance Min Flight Price: ₱{advance_min_flight_baseline:,.2f}")
print("\\nSample engineered KPI columns:")
display(pre_fest[['date_collected', 'days_to_festival', 'lead_cohort', 'flight_fppr_pct', 'hotel_fppr_pct', 'flight_lbpi', 'flight_median_change_1d', 'hotel_median_change_1d']].head(5))
"""
cells.append(nbf.v4.new_code_cell(cell3_code))

# ==============================================================================
# Cell 4: Markdown - KPI 1 Deep Dive
# ==============================================================================
cell4_md = """## 2. KPI 1: Festival Price Premium Ratio (FPPR)

### Metric Formulation & Purpose
$$\\text{FPPR}_{t} = \\left( \\frac{\\text{Median Festival Price}_{t} - \\text{Median Rolling Baseline Price}_{t}}{\\text{Median Rolling Baseline Price}_{t}} \\right) \\times 100\\%$$

* **Traveler Decision:** Informs travelers of the exact percentage surcharge demanded purely due to festival congestion, separating festival markups from everyday airfare/hotel costs.
* **Why It Beats Vanity Metrics:** Simple spot prices (e.g., "flight costs ₱4,500") conflate normal seasonal ticket prices with festival price shocks. FPPR is baseline-adjusted, revealing pure event-driven inflation.
"""
cells.append(nbf.v4.new_markdown_cell(cell4_md))

# ==============================================================================
# Cell 5: Code - Plotting KPI 1
# ==============================================================================
cell5_code = """fig, ax = plt.subplots(figsize=(13, 5))

# Plot FPPR for flights and hotels
ax.plot(pre_fest['date_collected'], pre_fest['flight_fppr_pct'], 
        marker='o', markersize=5, linewidth=2, color='#2b5c8f', label='Flight Premium Ratio (FPPR %)')
ax.plot(pre_fest['date_collected'], pre_fest['hotel_fppr_pct'], 
        marker='s', markersize=5, linewidth=2, color='#e26d5c', linestyle='--', label='Hotel Premium Ratio (FPPR %)')

# Threshold lines
ax.axhline(0, color='gray', linestyle='-', linewidth=1, alpha=0.7, label='Baseline Parity (0% Markup)')
ax.axhline(20, color='#d9534f', linestyle=':', linewidth=1.5, alpha=0.8, label='Surge Threshold (+20%)')

# Annotation of peak surge
max_flight_fppr_idx = pre_fest['flight_fppr_pct'].idxmax()
if pd.notnull(max_flight_fppr_idx):
    peak_date = pre_fest.loc[max_flight_fppr_idx, 'date_collected']
    peak_val = pre_fest.loc[max_flight_fppr_idx, 'flight_fppr_pct']
    ax.annotate(f'Peak Flight FPPR: +{peak_val:.1f}%\\n({peak_date.strftime("%b %d")})',
                xy=(peak_date, peak_val), xytext=(peak_date - pd.Timedelta(days=8), peak_val - 15),
                arrowprops=dict(facecolor='#2b5c8f', shrink=0.08, width=1.5, headwidth=6),
                fontweight='bold', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#d8e2dc", alpha=0.9))

ax.set_title("KPI 1: Festival Price Premium Ratio (FPPR %) Over Time", pad=12)
ax.set_xlabel("Collection Date")
ax.set_ylabel("Price Premium over Rolling Baseline (%)")
ax.legend(loc='upper left', frameon=True)
plt.xticks(rotation=20)
plt.tight_layout()
plt.show()

# Cohort-level summary of FPPR
fppr_summary = pre_fest.groupby('lead_cohort', observed=False).agg(
    flight_fppr_median=('flight_fppr_pct', 'median'),
    flight_fppr_max=('flight_fppr_pct', 'max'),
    hotel_fppr_median=('hotel_fppr_pct', 'median'),
    hotel_fppr_max=('hotel_fppr_pct', 'max')
).reset_index()

print("--- FPPR COHORT SUMMARY ---")
display(fppr_summary)
"""
cells.append(nbf.v4.new_code_cell(cell5_code))

# ==============================================================================
# Cell 6: Markdown - KPI 1 Interpretation
# ==============================================================================
cell6_md = """### KPI 1 Key Takeaways
1. **Divergent Sector Pricing Mechanics:** 
   - **Hotels command a consistent, positive festival premium:** Median hotel FPPR remains positive across every single cohort (+6.00% in Advance, +10.14% in Mid, +5.29% in Surge, with peaks reaching **+41.16%**). Bacolod hotels price the festival as a premium destination event well in advance.
   - **Flights trade at a steep advance discount before surging late:** Median flight FPPR is negative during the Advance Window (-29.35%) and Mid Window (-53.88%) because rolling baseline quotes (booking flights for next-day travel) carried severe near-term booking penalties. However, in the final week before MassKara, advance discounts evaporate rapidly and flight FPPR surges from -53.88% up to a peak of **+19.98%**.
2. **Actionable Traveler Threshold:** 
   - When Flight $\\text{FPPR} < -20\\%$, travelers enjoy substantial advance-booking savings over typical short-lead travel.
   - Once Flight $\\text{FPPR}$ crosses above $0\\%$ into positive territory (as observed in the final 7 days), festival tickets become more expensive than standard non-event baseline fares.
"""
cells.append(nbf.v4.new_markdown_cell(cell6_md))

# ==============================================================================
# Cell 7: Markdown - KPI 2 Deep Dive
# ==============================================================================
cell7_md = """## 3. KPI 2: Lead-Time Booking Penalty Index (LBPI)

### Metric Formulation & Purpose
$$\\text{LBPI}_{t} = \\frac{\\text{Minimum Festival Flight Price}_{t}}{\\text{Baseline Minimum Price}_{\\tau > 20\\text{d}}}$$

* **Traveler Decision:** Answers the direct question: *"How many multiples of the budget fare am I paying if I wait until $N$ days before MassKara?"*
* **Why It Beats Vanity Metrics:** Airlines continuously pull cheaper fare buckets (saver seats) as the date approaches. Tracking the *minimum available fare* directly captures the exhaustion of budget capacity, whereas median fare tracks the middle of the cabin.
"""
cells.append(nbf.v4.new_markdown_cell(cell7_md))

# ==============================================================================
# Cell 8: Code - Plotting KPI 2
# ==============================================================================
cell8_code = """fig, ax = plt.subplots(figsize=(13, 5))

# Plot LBPI against Days to Festival (reversed x-axis to reflect countdown)
valid_lbpi = pre_fest.dropna(subset=['flight_lbpi', 'days_to_festival']).sort_values('days_to_festival', ascending=False)

ax.plot(valid_lbpi['days_to_festival'], valid_lbpi['flight_lbpi'], 
        marker='o', color='#386641', linewidth=2.5, label='Flight LBPI (Min Fare Multiplier)')

# Cohort Shading
ax.axvspan(20, max(valid_lbpi['days_to_festival']), color='#a7c957', alpha=0.18, label='Advance Window (>20d)')
ax.axvspan(7, 20, color='#f2e8cf', alpha=0.35, label='Mid Window (8-20d)')
ax.axvspan(0, 7, color='#bc4749', alpha=0.20, label='Surge Window (<=7d)')

# Critical penalty thresholds
ax.axhline(1.0, color='gray', linestyle='--', linewidth=1.2, label='Baseline Multiplier (1.0x)')
ax.axhline(1.5, color='#e07a5f', linestyle=':', linewidth=1.5, label='50% Penalty Gate (1.5x)')
ax.axhline(2.0, color='#9b2226', linestyle=':', linewidth=1.5, label='Double-Fare Gate (2.0x)')

ax.set_xlim(valid_lbpi['days_to_festival'].max() + 1, -0.5)  # Countdown: from 37 down to 0
ax.set_title("KPI 2: Lead-Time Booking Penalty Index (LBPI) vs. Days to Festival", pad=12)
ax.set_xlabel("Days Remaining to Festival (Countdown: Advance -> Surge)", fontweight='bold')
ax.set_ylabel("Minimum Fare Multiplier (LBPI)", fontweight='bold')
ax.legend(loc='upper right', frameon=True)

# Annotate the booking cliff
cliff_point = valid_lbpi[valid_lbpi['days_to_festival'] <= 7].iloc[0]
ax.annotate(f'The Booking Cliff:\\nPenalty escalates to {cliff_point["flight_lbpi"]:.2f}x (Peak: {valid_lbpi["flight_lbpi"].max():.2f}x)',
            xy=(cliff_point['days_to_festival'], cliff_point['flight_lbpi']),
            xytext=(cliff_point['days_to_festival'] + 6, cliff_point['flight_lbpi'] + 0.5),
            arrowprops=dict(facecolor='#9b2226', shrink=0.08, width=1.5, headwidth=6),
            fontweight='bold', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#fdf0d5", alpha=0.9))

plt.tight_layout()
plt.show()

# LBPI Statistics by Cohort
lbpi_stats = pre_fest.groupby('lead_cohort', observed=False)['flight_lbpi'].agg(
    median_multiplier='median',
    max_multiplier='max',
    min_multiplier='min',
    std_multiplier='std'
).reset_index()

print("--- LBPI MULTIPLIER BY COHORT ---")
display(lbpi_stats)
"""
cells.append(nbf.v4.new_code_cell(cell8_code))

# ==============================================================================
# Cell 9: Markdown - KPI 2 Interpretation
# ==============================================================================
cell9_md = """### KPI 2 Key Takeaways
1. **The 20-Day Golden Window:** In the Advance Window ($>20$ days), $\\text{LBPI} = 1.00\\times$ (with minimal variance, std: $0.016$), anchored to the baseline minimum fare of **₱1,915.00**.
2. **The 8–20 Day Buffer:** In the Mid Window ($8$–$20$ days), $\\text{LBPI}$ rises modestly to a median of **$1.05\\times$** (range: $1.03\\times$ to $1.47\\times$). Fares remain accessible, but cheap seat availability starts to tighten.
3. **The 7-Day Surge Cliff:** Once inside the $\\le 7$-day cutoff, $\\text{LBPI}$ jumps dramatically to a median of **$1.74\\times$** and peaks at **$4.74\\times$** (equivalent to fares reaching **₱9,080.00** for the cheapest seat). Budget travelers delaying their booking into the final week incur an average $+74\\%$ to $+374\\%$ monetary penalty.
4. **Actionable Decision Rule for Travelers:** **Hard booking cutoff at Day 14.** Beyond Day 14, budget saver inventory depletes rapidly and entry-level fares skyrocket.
"""
cells.append(nbf.v4.new_markdown_cell(cell9_md))

# ==============================================================================
# Cell 10: Markdown - KPI 3 Deep Dive
# ==============================================================================
cell10_md = """## 4. KPI 3: Search-to-Surge Elasticity & Lag Response

### Metric Formulation & Purpose
$$\\text{Lag Elasticity}_{k} = \\frac{\\%\\Delta \\text{Flight Median Price}_{t}}{\\%\\Delta \\text{Google Trends Score}_{t-k}} \\quad \\text{for } k \\in \\{0, 1, 2, 3\\} \\text{ days}$$

* **Vendor & Researcher Decision:** Tests whether viral spikes in search intent immediately shock travel prices, or whether there exists an empirical **24-to-72-hour lag** before airlines and hotels update rates.
* **Why It Beats Vanity Metrics:** A raw Google Trends score of 95 tells a business that people are searching, but nothing about whether they are buying. Elasticity measures whether commercial suppliers adjust pricing in response to that search wave.
"""
cells.append(nbf.v4.new_markdown_cell(cell10_md))

# ==============================================================================
# Cell 11: Code - Plotting KPI 3
# ==============================================================================
cell11_code = """# Compute cross-correlations across lag windows (0d, 1d, 2d, 3d)
lags = [0, 1, 2, 3]
corr_results = []

for lag in lags:
    if lag == 0:
        trend_col = 'trend_search_score'
    else:
        trend_col = f'trend_score_lag_{lag}d'
        
    sub = pre_fest.dropna(subset=['flight_fest_median_price', trend_col])
    rho, pval = spearmanr(sub[trend_col], sub['flight_fest_median_price'])
    
    sub_hotel = pre_fest.dropna(subset=['hotel_fest_median_price', trend_col])
    rho_hotel, pval_hotel = spearmanr(sub_hotel[trend_col], sub_hotel['hotel_fest_median_price'])
    
    corr_results.append({
        'Lag Window': f'{lag}-Day Lag',
        'Flight Spearman Rho': rho,
        'Flight p-value': pval,
        'Hotel Spearman Rho': rho_hotel,
        'Hotel p-value': pval_hotel
    })

lag_df = pd.DataFrame(corr_results)
print("--- LAGGED SEARCH-PRICE CORRELATION ANALYSIS ---")
display(lag_df)

# Dual-Axis Time Series Visualization of Search Velocity vs. Flight Surge
fig, ax1 = plt.subplots(figsize=(13, 5))

color_trend = '#457b9d'
color_flight = '#e63946'

ax1.set_xlabel('Collection Date', fontweight='bold')
ax1.set_ylabel('Google Trends 7-Day Velocity (%)', color=color_trend, fontweight='bold')
l1 = ax1.plot(pre_fest['date_collected'], pre_fest['trend_velocity_7d'], color=color_trend, 
              linewidth=2, marker='^', markersize=4, label='Search Velocity 7d (%)')
ax1.tick_params(axis='y', labelcolor=color_trend)
ax1.axhline(0, color=color_trend, linestyle=':', alpha=0.5)

ax2 = ax1.twinx()
ax2.set_ylabel('1-Day Flight Price Change (₱)', color=color_flight, fontweight='bold')
l2 = ax2.plot(pre_fest['date_collected'], pre_fest['flight_median_change_1d'], color=color_flight, 
              linewidth=2, marker='o', markersize=4, linestyle='-', label='Flight 1d Change (₱)')
ax2.tick_params(axis='y', labelcolor=color_flight)

# Combine legends
lines = l1 + l2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', frameon=True)

plt.title("KPI 3: Google Trends Search Velocity vs. Flight Price Reaction (Lag Analysis)", pad=12)
plt.tight_layout()
plt.show()
"""
cells.append(nbf.v4.new_code_cell(cell11_code))

# ==============================================================================
# Cell 12: Markdown - KPI 3 Interpretation
# ==============================================================================
cell12_md = """### KPI 3 Key Takeaways
1. **Contemporaneous vs. Lagged Correlation:** 
   - Spearman rank correlation between search interest and flight pricing is strongest at **Day 0 ($\\rho = 0.6103$, $p < 0.001$)**, and remains statistically significant and strong across forward lag windows (**Day 1:** $\\rho = 0.5653$; **Day 2:** $\\rho = 0.5175$; **Day 3:** $\\rho = 0.4996$).
   - In contrast, hotel pricing exhibits very low, statistically insignificant correlation with Google Trends across all lags ($\\rho = 0.03$ to $0.18$, $p > 0.25$), confirming that hotel rates are pre-set and decoupled from daily search curiosity.
2. **Behavioral Mechanism:** 
   - Flight search interest and ticket prices peak together in the final 7–10 days before MassKara. The high contemporaneous correlation reflects convergent consumer urgency: as departure nears, search frequency intensifies while airlines progressively deplete cheaper fare buckets.
3. **Vendor Implication:** 
   - Local Bacolod hospitality operators tracking search interest can use sustained high Google Trends scores ($\ge 75$) as a real-time proxy for airfare escalation and peak tourist arrival momentum.
"""
cells.append(nbf.v4.new_markdown_cell(cell12_md))

# ==============================================================================
# Cell 13: Markdown - KPIs 4 & 5 Deep Dive
# ==============================================================================
cell13_md = """## 5. KPIs 4 & 5: Daily Price Surge Velocity ($\\Delta\\text{Flight}_{1\\text{d}}$ vs. $\\Delta\\text{Hotel}_{1\\text{d}}$)

### Metric Formulation & Purpose
$$\\Delta\\text{Price}_{1\\text{d}} = \\text{Median Festival Price}_{t} - \\text{Median Festival Price}_{t-1} \\quad (\\text{in ₱})$$

* **Traveler & Business Decision:** Identifies the volatility structure of the travel market. Determines whether price escalations happen continuously or via discrete, irreversible upward jumps.
* **Why It Beats Vanity Metrics:** Tracking the absolute price level gives no clue about current price acceleration. Velocity isolates when algorithms enter high-escalation mode.
"""
cells.append(nbf.v4.new_markdown_cell(cell13_md))

# ==============================================================================
# Cell 14: Code - Plotting KPIs 4 & 5
# ==============================================================================
cell14_code = """fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

valid_daily = pre_fest.dropna(subset=['date_collected', 'flight_median_change_1d', 'hotel_median_change_1d'])

# Subplot 1: Flight 1-day Change
bar_colors_f = np.where(valid_daily['flight_median_change_1d'] > 500, '#d90429', '#2b2d42')
axes[0].bar(valid_daily['date_collected'], valid_daily['flight_median_change_1d'], color=bar_colors_f, width=0.8)
axes[0].axhline(0, color='gray', linestyle='-', linewidth=0.8)
axes[0].axhline(500, color='#d90429', linestyle='--', linewidth=1.2, label='High-Surge Alarm Threshold (+₱500/day)')
axes[0].set_title("KPI 4: Day-over-Day Flight Median Fare Velocity (₱/day)", pad=10)
axes[0].set_ylabel("Flight Change (₱)", fontweight='bold')
axes[0].legend(loc='upper left', frameon=True)

# Annotate extreme ratchet jump
max_flight_jump_idx = valid_daily['flight_median_change_1d'].idxmax()
if pd.notnull(max_flight_jump_idx):
    jump_row = valid_daily.loc[max_flight_jump_idx]
    axes[0].annotate(f'Algorithmic Ratchet Jump:\\n+₱{jump_row["flight_median_change_1d"]:,.0f} overnight',
                     xy=(jump_row['date_collected'], jump_row['flight_median_change_1d']),
                     xytext=(jump_row['date_collected'] - pd.Timedelta(days=10), jump_row['flight_median_change_1d'] - 800),
                     arrowprops=dict(facecolor='#d90429', shrink=0.08, width=1.5, headwidth=6),
                     fontweight='bold', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#fdf0d5", alpha=0.9))

# Subplot 2: Hotel 1-day Change
bar_colors_h = np.where(valid_daily['hotel_median_change_1d'] > 0, '#588157', '#3a5a40')
axes[1].bar(valid_daily['date_collected'], valid_daily['hotel_median_change_1d'], color=bar_colors_h, width=0.8)
axes[1].axhline(0, color='gray', linestyle='-', linewidth=0.8)
axes[1].set_title("KPI 5: Day-over-Day Hotel Median Rate Velocity (₱/day)", pad=10)
axes[1].set_xlabel("Collection Date", fontweight='bold')
axes[1].set_ylabel("Hotel Change (₱)", fontweight='bold')

plt.xticks(rotation=20)
plt.tight_layout()
plt.show()

# Velocity Statistical Comparison Table
velocity_comp = pd.DataFrame({
    'Metric Property': ['Mean Daily Velocity (₱)', 'Median Daily Velocity (₱)', 'Std Deviation (₱)', 'Max Single-Day Jump (₱)', 'Min Single-Day Drop (₱)'],
    'Flight Velocity (KPI 4)': [
        valid_daily['flight_median_change_1d'].mean(),
        valid_daily['flight_median_change_1d'].median(),
        valid_daily['flight_median_change_1d'].std(),
        valid_daily['flight_median_change_1d'].max(),
        valid_daily['flight_median_change_1d'].min()
    ],
    'Hotel Velocity (KPI 5)': [
        valid_daily['hotel_median_change_1d'].mean(),
        valid_daily['hotel_median_change_1d'].median(),
        valid_daily['hotel_median_change_1d'].std(),
        valid_daily['hotel_median_change_1d'].max(),
        valid_daily['hotel_median_change_1d'].min()
    ]
})

print("--- VELOCITY VOLATILITY COMPARISON ---")
display(velocity_comp.round(2))
"""
cells.append(nbf.v4.new_code_cell(cell14_code))

# ==============================================================================
# Cell 15: Markdown - Vanity vs Decision Metrics
# ==============================================================================
cell15_md = """## 6. Vanity vs. Decision Metric Analysis

A common failure mode in travel analytics is tracking high-visibility vanity numbers rather than actionable decision metrics. The table below formalizes this distinction for our project stakeholders:

| Domain | Vanity Metric (What to Avoid) | Flaw / Why It Fails | Actionable Decision KPI (What to Track) | Real Decision Supported |
| :--- | :--- | :--- | :--- | :--- |
| **Search Interest** | **Raw Google Trends Score (0–100)** | Measures ephemeral public browsing curiosity; a spike can represent casual news viewing without commercial purchasing intent. | **KPI 3: Lagged Search Elasticity ($\\rho$)** | Evaluates whether search curiosity coincides with actual travel fare movements across a multi-day horizon. |
| **Airfare** | **Absolute Spot Flight Fare (₱)** | Conflates macro inflation, day-of-week timing, and fuel surcharges with the actual festival surge. | **KPI 1: Festival Price Premium Ratio (FPPR)** | Isolates the true net festival surcharge relative to a rolling baseline. |
| **Lead Time** | **Days to Festival (Calendar Count)** | Calendar time is linear, but airline dynamic pricing behavior is non-linear and cliff-based. | **KPI 2: Lead-Time Booking Penalty Index (LBPI)** | Explicitly quantifies the cost multiplier of waiting ($1.00\\times \\to 4.74\\times$), establishing a clear financial cutoff date. |
| **Inventory** | **Scraper Listing Count (~20 quotes)** | Fixed by SerpApi API pagination settings; does not reflect actual room or seat capacity. | **KPI 4: Flight Daily Surge Velocity ($\\Delta\\text{Flight}_{1\\text{d}}$)** | Detects rapid fare acceleration caused by seat-tier depletion. |
"""
cells.append(nbf.v4.new_markdown_cell(cell15_md))

# ==============================================================================
# Cell 16: Code - Executive Master KPI Summary Table
# ==============================================================================
cell16_code = """# Build the Executive KPI Scorecard grouped by Lead-Time Cohorts
cohort_kpi_scorecard = pre_fest.groupby('lead_cohort', observed=False).agg(
    Observations=('date_collected', 'count'),
    Avg_Days_Out=('days_to_festival', 'mean'),
    Flight_FPPR_Median_Pct=('flight_fppr_pct', 'median'),
    Hotel_FPPR_Median_Pct=('hotel_fppr_pct', 'median'),
    Flight_LBPI_Median_Multiplier=('flight_lbpi', 'median'),
    Flight_LBPI_Max_Multiplier=('flight_lbpi', 'max'),
    Flight_Daily_Velocity_Avg_PHP=('flight_median_change_1d', 'mean'),
    Hotel_Daily_Velocity_Avg_PHP=('hotel_median_change_1d', 'mean'),
    Avg_Search_Score=('trend_search_score', 'mean')
).reset_index()

print("=========================================================================================")
print("                      EXECUTIVE KPI SCORECARD BY LEAD-TIME COHORT                        ")
print("=========================================================================================")
display(cohort_kpi_scorecard.round(2))
"""
cells.append(nbf.v4.new_code_cell(cell16_code))

# ==============================================================================
# Cell 17: Markdown - Executive Decision Rules & Action Matrix
# ==============================================================================
cell17_md = """## 7. Operational Decision Rules & Action Matrix

Synthesizing all 5 KPIs leads to concrete operating guidelines for our primary stakeholders:

### 1. For Budget-Conscious Travelers
* **The "Safe Zone" ($> 20$ Days to Festival):**
  * $\\text{LBPI} = 1.00\\times$, $\\text{Flight FPPR} \\approx -29\\%$.
  * **Action:** Book flights and accommodations in this window. Minimum airfares sit at baseline (**₱1,915.00**), capturing maximum advance discounts.
* **The "Warning Zone" ($8$ to $20$ Days to Festival):**
  * $\\text{LBPI} \\approx 1.05\\times$ (up to $1.47\\times$), $\\text{Hotel FPPR} \\approx +10\\%$.
  * **Action:** Finalize tickets immediately. Saver fare tiers begin depleting, though median flight fares remain stable around ₱2,695.
* **The "Surge Zone" ($\le 7$ Days to Festival):**
  * $\\text{LBPI} = 1.74\\times$ median (peaking at **$4.74\\times$**), $\\text{Flight FPPR}$ surges up to **$+19.98\\%$**, daily flight velocity spikes up to **+₱4,865.50 overnight**.
  * **Action:** Avoid booking flights. If travel is mandatory, consider alternative travel modes (e.g. ferry via Iloilo) to bypass extreme late-window airfare surges.

### 2. For Bacolod Hospitality Vendors & Local Businesses
* **Search Monitoring Trigger:**
  * When Google Trends scores cross $\\ge 75$ and contemporaneous flight velocity spikes past $+₱500$/day, trigger staffing expansion and inventory readiness.
* **Pricing Defense:**
  * Hotel rates remain remarkably steady throughout the pre-festival window (median daily change of $-₱18.00$, mean of $+₱16.29$). Because airfare absorbs the overwhelming majority of travel price volatility, accommodation providers can maintain their steady $+6\\%$ to $+10\\%$ festival premium without risking sudden cancellation waves.

### 3. Definition of Done Verification
- [x] Defined 5 core KPIs mapping directly to the MassKara travel price surge problem statement.
- [x] Explicitly eliminated invalid pipeline artifacts (scraper quote pagination limits).
- [x] Evaluated trend dynamics over time and lead-time reverse countdowns.
- [x] Documented the structural difference between vanity metrics and decision-driving metrics.
- [x] Provided actionable threshold gates ready to integrate into reporting and dashboard milestones.
"""
cells.append(nbf.v4.new_markdown_cell(cell17_md))

nb['cells'] = cells

output_path = 'notebooks/week_18_kpis.ipynb'
with open(output_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Successfully generated {output_path} with {len(cells)} cells.")

# Execute notebook so all figures and tables are computed and pre-rendered
print("Executing notebook with NotebookClient...")
client = NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': 'notebooks/'}})
client.execute()

with open(output_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Successfully executed and updated {output_path} with fresh pre-rendered outputs.")
