"""Tested replacement calculations and charts; originals are left unchanged.

Run from the project root: .venv/bin/python audit/corrections.py
Sections can be copied into the corresponding notebooks after their imports.
"""
from pathlib import Path
import os

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/coffee-audit-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit" / "corrected_charts"
OUT.mkdir(parents=True, exist_ok=True)
df = pd.read_excel(ROOT / "data" / "Coffee Shop Sales.xlsx", sheet_name="Transactions")

# A. Extend notebook 01's checks. Flag price variation; do not overwrite it.
required = {"transaction_id", "transaction_date", "transaction_time", "transaction_qty", "store_id", "store_location", "product_id", "unit_price", "product_category", "product_type", "product_detail"}
assert required.issubset(df.columns), "Required columns missing"
assert not df[list(required)].isna().any().any(), "Missing required values"
assert df.transaction_id.is_unique, "Duplicate transaction IDs: investigate grain"
for column in ("transaction_qty", "unit_price"):
    df[column] = pd.to_numeric(df[column], errors="raise")
    assert np.isfinite(df[column]).all() and df[column].gt(0).all(), column
assert df.transaction_qty.mod(1).eq(0).all(), "Fractional quantities"
df["transaction_date"] = pd.to_datetime(df.transaction_date, errors="raise")
parsed_time = pd.to_datetime(df.transaction_time.astype(str), format="%H:%M:%S", errors="raise")
df["hour"] = parsed_time.dt.hour
for column in ("store_location", "product_category", "product_type", "product_detail"):
    labels = df[column].astype("string")
    assert labels.str.strip().ne("").all(), f"Blank {column} labels"
    variants = pd.DataFrame({"raw": labels, "normalized": labels.str.strip().str.casefold()}).drop_duplicates()
    collisions = variants.groupby("normalized").raw.nunique()
    assert not collisions.gt(1).any(), f"Naming variants in {column}"
assert df.groupby("store_id").store_location.nunique().eq(1).all()
assert df.groupby("store_location").store_id.nunique().eq(1).all()
assert df.groupby("product_id")[["product_detail", "product_type", "product_category"]].nunique().eq(1).all().all()
assert df.groupby("product_detail").product_id.nunique().eq(1).all()
price_review = df.groupby(["product_id", "product_detail"]).unit_price.agg(price_count="nunique", minimum="min", maximum="max")
price_review = price_review.loc[price_review.price_count.gt(1)]
price_review.to_csv(ROOT / "audit" / "price_variation_review.csv")

# B. Calculate store metrics once, for every location (not three manual filters).
assert np.allclose(df.unit_price * 100, (df.unit_price * 100).round(), rtol=0, atol=1e-8)
df["line_revenue_cents"] = (df.unit_price * 100).round().astype("int64") * df.transaction_qty.astype("int64")
df["line_revenue"] = df.line_revenue_cents / 100
total_revenue = df.line_revenue_cents.sum() / 100
transactions = df.transaction_id.nunique()
average_transaction_value = total_revenue / transactions
store_metrics = df.groupby("store_location").agg(revenue_cents=("line_revenue_cents", "sum"), transactions=("transaction_id", "nunique"), units=("transaction_qty", "sum"))
store_metrics["revenue"] = store_metrics.revenue_cents / 100
store_metrics["atv"] = store_metrics.revenue / store_metrics.transactions
store_metrics["units_per_transaction"] = store_metrics.units / store_metrics.transactions
store_metrics["realized_revenue_per_unit"] = store_metrics.revenue / store_metrics.units
store_metrics = store_metrics.sort_values("revenue", ascending=False)
assert store_metrics.revenue_cents.sum() == df.line_revenue_cents.sum()

# C. Replace notebook 03's Task 3 with ten individual product IDs/details.
top10 = (df.groupby(["product_id", "product_detail"])["line_revenue"].sum().nlargest(10).sort_values())
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top10.index.get_level_values("product_detail"), top10.values)
ax.bar_label(bars, labels=[f"${value:,.2f}" for value in top10], padding=4, fontsize=9)
ax.set(title="Top 10 Individual Products by Revenue | Jan–Jun 2023", xlabel="Revenue ($)", ylabel="")
ax.xaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
ax.set_xlim(0, top10.max() * 1.2)
fig.tight_layout()
fig.savefig(OUT / "top10_individual_products.png", dpi=150)
plt.close(fig)

# D. Keep monthly time order and compare both totals and revenue per day.
df["month"] = df.transaction_date.dt.to_period("M")
monthly = df.groupby("month").agg(revenue=("line_revenue", "sum"), transactions=("transaction_id", "nunique"), observed_days=("transaction_date", "nunique"))
monthly = monthly.sort_index()
monthly["revenue_per_day"] = monthly.revenue / monthly.observed_days
monthly["revenue_growth_pct"] = monthly.revenue.pct_change() * 100
monthly["daily_revenue_growth_pct"] = monthly.revenue_per_day.pct_change() * 100
monthly["atv"] = monthly.revenue / monthly.transactions

# E. Weekday comparisons: make one observation per calendar date first.
dates = pd.date_range(df.transaction_date.min(), df.transaction_date.max(), freq="D")
daily = df.groupby("transaction_date").agg(revenue=("line_revenue", "sum"), transactions=("transaction_id", "nunique"))
# Every date has sales in this workbook. Investigate gaps before zero-filling a new dataset.
assert daily.index.equals(dates.rename("transaction_date")), "Investigate missing dates before daily normalization"
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_metrics = daily.groupby(daily.index.day_name()).agg(days=("revenue", "size"), total_revenue=("revenue", "sum"), revenue_per_day=("revenue", "mean"), transactions_per_day=("transactions", "mean")).reindex(weekday_order)
weekday_metrics.to_csv(ROOT / "audit" / "corrected_weekday_metrics.csv")

# F. Hourly observations: report the denominator explicitly; opening hours unknown.
hourly = df.groupby(["store_location", "hour"]).agg(transactions=("transaction_id", "nunique"), days_with_sales=("transaction_date", "nunique"))
hourly["transactions_per_calendar_day"] = hourly.transactions / len(dates)
hourly["transactions_per_day_with_sales"] = hourly.transactions / hourly.days_with_sales
# Days with sales are NOT known operating days. The second rate is diagnostic only.
hourly.to_csv(ROOT / "audit" / "corrected_hourly_metrics.csv")
fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=hourly.reset_index(), x="hour", y="transactions_per_calendar_day", hue="store_location", marker="o", ax=ax)
ax.set(title="Hourly Recorded Transactions per Calendar Day | Jan–Jun 2023", xlabel="Hour of day (10 = 10:00–10:59)", ylabel="Transactions / 181 calendar days")
ax.set_xticks(range(int(df.hour.min()), int(df.hour.max()) + 1))
ax.grid(alpha=0.25)
fig.text(0.02, 0.01, "Opening hours unavailable; no-sale hours do not prove closure or low demand.", fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "hourly_calendar_day.png", dpi=150)
plt.close(fig)

# G. Calculate exact narrative values instead of typing approximations.
product_gap = top10.iloc[-1] - top10.iloc[0]
store_gap = store_metrics.revenue.max() - store_metrics.revenue.min()
peak_to_11 = (hourly.transactions.unstack("hour")[[10, 11]].assign(decline=lambda x: x[10]-x[11], decline_pct=lambda x: (1-x[11]/x[10])*100))
summary = {
    "total_revenue": float(total_revenue), "transactions": int(transactions), "atv": float(average_transaction_value),
    "top_product": top10.index[-1][1], "top_product_revenue": float(top10.iloc[-1]),
    "tenth_product": top10.index[0][1], "tenth_product_revenue": float(top10.iloc[0]),
    "first_tenth_gap": float(product_gap), "highest_lowest_store_gap": float(store_gap),
    "variable_price_products": len(price_review),
}

# Targeted checks for the actual problems the replacement code addresses.
assert len(top10) == 10
assert summary["top_product"] == "Sustainably Grown Organic Lg"
assert abs(summary["first_tenth_gap"] - 6042.25) < 1e-8
assert abs(total_revenue - 698812.33) < 1e-8
assert weekday_metrics.revenue_per_day.rank(ascending=False).loc["Saturday"] == 3
assert monthly.loc[pd.Period("2023-02"), "revenue_growth_pct"] < 0
assert monthly.loc[pd.Period("2023-02"), "daily_revenue_growth_pct"] > 0
import json
(ROOT / "audit" / "correction_results.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
print("All targeted correction checks passed.")
