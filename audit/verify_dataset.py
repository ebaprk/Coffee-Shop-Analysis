"""Independent Decimal-based workbook reconciliation plus diagnostic tables."""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit"
PATH = ROOT / "data/Coffee Shop Sales.xlsx"
workbook = openpyxl.load_workbook(PATH, read_only=True, data_only=True)
rows = workbook["Transactions"].iter_rows(values_only=True)
headers = next(rows)
records = [dict(zip(headers, row)) for row in rows]
groups = {key: defaultdict(Decimal) for key in ("store", "month", "weekday", "hour", "category", "detail", "type", "store_hour", "store_month", "store_product")}
quantities = Counter()
counts = Counter()
for row in records:
    revenue = Decimal(str(row["unit_price"])) * row["transaction_qty"]
    date = row["transaction_date"]
    store, hour = row["store_location"], row["transaction_time"].hour
    keys = {
        "store": store, "month": date.strftime("%Y-%m"), "weekday": date.strftime("%A"),
        "hour": hour, "category": row["product_category"], "detail": row["product_detail"],
        "type": row["product_type"], "store_hour": (store, hour),
        "store_month": (store, date.strftime("%Y-%m")), "store_product": (store, row["product_detail"]),
    }
    for key, value in keys.items():
        groups[key][value] += revenue
    quantities[row["product_detail"]] += row["transaction_qty"]
    counts[(store, hour)] += 1

df = pd.read_excel(PATH)
df["line_revenue"] = df.transaction_qty * df.unit_price
df["month"] = df.transaction_date.dt.strftime("%Y-%m")
df["weekday"] = df.transaction_date.dt.day_name()
df["hour"] = df.transaction_time.map(lambda x: x.hour)
mapping = {
    "store": "store_location", "month": "month", "weekday": "weekday", "hour": "hour",
    "category": "product_category", "detail": "product_detail", "type": "product_type",
    "store_hour": ["store_location", "hour"], "store_month": ["store_location", "month"],
    "store_product": ["store_location", "product_detail"],
}
checks = []
for name, columns in mapping.items():
    computed = df.groupby(columns).line_revenue.sum()
    assert set(computed.index) == set(groups[name])
    for key, expected in groups[name].items():
        assert abs(Decimal(str(computed.loc[key])) - expected) < Decimal("0.000001"), (name, key)
    checks.append({"aggregation": name, "groups": len(computed), "passed": True})
assert df.groupby("product_detail").transaction_qty.sum().to_dict() == dict(quantities)
assert df.groupby(["store_location", "hour"]).transaction_id.nunique().to_dict() == dict(counts)

store = df.groupby("store_location").agg(revenue=("line_revenue", "sum"), transactions=("transaction_id", "nunique"), units=("transaction_qty", "sum"), observed_days=("transaction_date", "nunique"))
store["atv"] = store.revenue / store.transactions
store["units_per_transaction"] = store.units / store.transactions
store["realized_revenue_per_unit"] = store.revenue / store.units
store.to_csv(OUT / "store_metrics.csv")
monthly = df.groupby("month").agg(revenue=("line_revenue", "sum"), transactions=("transaction_id", "nunique"), units=("transaction_qty", "sum"), observed_days=("transaction_date", "nunique"))
monthly["revenue_per_day"] = monthly.revenue / monthly.observed_days
monthly["atv"] = monthly.revenue / monthly.transactions
monthly["revenue_growth_pct"] = monthly.revenue.pct_change() * 100
monthly["daily_revenue_growth_pct"] = monthly.revenue_per_day.pct_change() * 100
monthly.to_csv(OUT / "monthly_metrics.csv")
daily = df.groupby("transaction_date").agg(revenue=("line_revenue", "sum"), transactions=("transaction_id", "nunique"))
weekdays = daily.groupby(daily.index.day_name()).agg(total_revenue=("revenue", "sum"), observed_days=("revenue", "size"), mean_daily_revenue=("revenue", "mean"), mean_daily_transactions=("transactions", "mean"))
weekdays.to_csv(OUT / "weekday_metrics.csv")
hourly = df.groupby(["store_location", "hour"]).agg(transactions=("transaction_id", "nunique"), units=("transaction_qty", "sum"), revenue=("line_revenue", "sum"), days_with_sales=("transaction_date", "nunique"))
hourly["transactions_per_calendar_day"] = hourly.transactions / 181
hourly.to_csv(OUT / "hourly_metrics.csv")
for name in ("detail", "type", "category"):
    pd.Series({k: float(v) for k,v in groups[name].items()}, name="revenue").sort_values(ascending=False).to_csv(OUT / f"revenue_by_{name}.csv")
coverage = df.groupby(["store_location", "transaction_date"]).agg(first_sale=("transaction_time", "min"), last_sale=("transaction_time", "max"), transactions=("transaction_id", "nunique"))
coverage.to_csv(OUT / "store_day_coverage.csv")
id_cols = ["product_detail", "product_type", "product_category", "unit_price"]
product_mappings = df.groupby("product_id")[id_cols].nunique()
all_dates = pd.date_range(df.transaction_date.min(), df.transaction_date.max(), freq="D")
store_dates = pd.MultiIndex.from_product([df.store_location.unique(), all_dates])
summary = {
    "dataset_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "rows": len(df), "columns_original": len(headers), "total_revenue_decimal": str(sum(groups["store"].values())),
    "total_units": int(df.transaction_qty.sum()), "transaction_ids": int(df.transaction_id.nunique()),
    "missing_cells": int(df[list(headers)].isna().sum().sum()),
    "duplicate_rows": int(df[list(headers)].duplicated().sum()),
    "duplicate_ids": int(df.transaction_id.duplicated().sum()),
    "nonpositive_quantities": int(df.transaction_qty.le(0).sum()), "fractional_quantities": int(df.transaction_qty.mod(1).ne(0).sum()),
    "nonpositive_prices": int(df.unit_price.le(0).sum()),
    "date_range": [str(df.transaction_date.min()), str(df.transaction_date.max())],
    "calendar_days": len(all_dates), "missing_store_dates": len(store_dates.difference(coverage.index)),
    "product_ids": int(df.product_id.nunique()), "product_details": int(df.product_detail.nunique()), "product_types": int(df.product_type.nunique()),
    "inconsistent_product_id_mappings": product_mappings.loc[product_mappings.gt(1).any(axis=1)].to_dict(orient="index"),
    "inconsistent_store_id_mapping": int(df.groupby("store_id").store_location.nunique().gt(1).sum()),
    "minimum_id": int(df.transaction_id.min()), "maximum_id": int(df.transaction_id.max()),
    "missing_sequential_ids": int(df.transaction_id.max()-df.transaction_id.min()+1-df.transaction_id.nunique()),
    "reconciliations": checks,
    "peak_to_11": {store: {"ten": counts[store,10], "eleven": counts[store,11], "decline": counts[store,10]-counts[store,11], "decline_pct": 100*(1-counts[store,11]/counts[store,10])} for store in df.store_location.unique()},
    "morning_share_8_to_11_exclusive": float(df.hour.between(8,10).mean()*100),
    "morning_share_7_to_11_exclusive": float(df.hour.between(7,10).mean()*100),
}
assert len(df) == 149116
assert summary["total_revenue_decimal"] == "698812.33"
(OUT / "verification_results.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
print('\nSTORES\n', store.to_string())
print('\nMONTHS\n', monthly.to_string())
print('\nWEEKDAYS\n', weekdays.sort_values("mean_daily_revenue", ascending=False).to_string())
print('\nHOUR COVERAGE\n',hourly.to_string())
