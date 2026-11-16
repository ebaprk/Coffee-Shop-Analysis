# Coffee Shop Analysis — portfolio readiness audit

Audit date: November 16, 2026. Scope: all three original notebooks, every populated cell, all five charts, all written findings and recommendations, the original Excel workbook, and repository packaging.

**Assessment: the calculations provide a sound foundation, but fix the product chart and misleading written interpretations before using this as a Deloitte internship portfolio sample.** All three notebooks run independently from clean kernels. The largest weaknesses are consistency between the question, aggregation, and conclusion; normalization of comparisons; and turning descriptive findings into testable business actions. This is an independent assessment of analytical portfolio quality, not an official Deloitte hiring rubric or a prediction of recruitment outcomes.

The original notebooks and workbook were left unchanged. All additions are inside `audit/`. Nothing was committed or pushed.

## Verification performed

| Notebook | Nonempty code cells | Fresh kernel execution | Independent reconciliation |
|---|---:|---|---|
| `01_exploration.ipynb` | 3 | Passed | Row count, IDs, units, quality summary |
| `02_sales_analysis.ipynb` | 14 | Passed | Revenue, ATV, product/category rankings, monthly/weekday/hourly series |
| `03_visualization.ipynb` | 6 | Passed | All five chart data series, including category percentages |

Each notebook ran in its own new IPython kernel using the project's Python 3.12.13 environment, with its working directory set to `notebook/` and standard inline plotting enabled. No previous notebook's variables were available. The audit also read the original workbook directly with openpyxl and aggregated monetary values with Python Decimal, independently of the notebooks' pandas calculations. Ten aggregation families, covering 449 groups, reconciled within $0.000001; quantities and transaction counts reconciled exactly. All five freshly generated charts were visually inspected. The replacement code was executed and its two replacement charts inspected.

The saved numerical results reproduced. A text display difference in exploration cell 5 consists of additional pandas Series name/type metadata, not changed data. Original notebook hashes are recorded in `execution_results.json`; the workbook SHA-256 is `287d06d19f7a832d48f1deea7b149836fb32d591010f060bdcf8d1959653bfe1`.

This verifies internal agreement with the supplied workbook. It cannot establish whether that workbook captures every original business transaction. I did not install a new environment from scratch; dependency versions below describe the environment that passed.

## Verified baseline

| Measure | Correct value |
|---|---:|
| Original dimensions | 149,116 rows × 11 columns |
| Date range | January 1–June 30, 2023 |
| Calendar coverage | All 181 dates at each of 3 stores |
| Unique transaction IDs | 149,116 |
| Units sold | 214,470 |
| Calculated sales revenue, quantity × recorded unit price | $698,812.33 |
| Average recorded transaction value | $4.686367… → $4.69 |
| Highest-revenue store | Hell's Kitchen, $236,511.17 |
| Highest average transaction value | Lower Manhattan, $4.81 |
| Highest-revenue individual product | Sustainably Grown Organic Lg, $21,151.75 |
| Highest-unit individual product | Earl Grey Rg, 4,708 units |
| Coffee category | $269,952.45; 38.63% |
| Coffee + Tea categories | 66.74% |

There are no missing cells, duplicate rows, duplicate transaction IDs, nonpositive prices or quantities, or fractional quantities. The date/time checks pass. Product IDs map consistently to product descriptions, types and categories; store IDs map consistently to locations. These are valuable strengths.

## Critical errors — correct before sharing

There are no execution-blocking failures in the intended notebook directory. The following are P1 errors because they change the answer a reviewer would take away.

### P1-1. “Top 10 Products” answers a different question

**Location:** notebook 03, Task 3, cell 10; its findings in cell 11. Cell references throughout this report count every notebook cell from 1, including Markdown cells, rather than using execution counts.

The code groups by `product_type` and never selects ten rows. It draws **all 29 product types**, while the text calls the winner an individual product. Barista Espresso is a product type aggregating several products; its approximately $91,406 is not an individual product's revenue. Notebook 02 correctly uses `product_detail`, so the two notebooks contradict each other. The chart also lacks a title/axis labels and its long labels overlap even at 40 × 30 inches.

**Correct result:** Sustainably Grown Organic Lg leads at **$21,151.75**. Brazilian Lg ranks tenth at **$15,109.50**. Their difference is **$6,042.25**, not approximately $60,000. The current $60,000 comparison is broadly consistent with *product types*, but answers the wrong question.

Replace the aggregation and chart with:

```python
top10 = (
    df.groupby(["product_id", "product_detail"])["line_revenue"]
      .sum().nlargest(10).sort_values()
)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(top10.index.get_level_values("product_detail"), top10.values)
ax.bar_label(bars, labels=[f"${v:,.2f}" for v in top10], padding=4)
ax.set(title="Top 10 Individual Products by Revenue | Jan–Jun 2023",
       xlabel="Revenue ($)", ylabel="")
ax.xaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
ax.set_xlim(0, top10.max() * 1.2)
fig.tight_layout()
plt.show()
```

Grouping by product ID makes the grain explicit; descriptions provide readable labels. Product descriptions are one-to-one with product IDs in this workbook, so notebook 02's existing description grouping is numerically valid.

**Tested implementation:** `corrections.py`, section C. **Preview:** `corrected_charts/top10_individual_products.png`.

### P1-2. The monthly narrative incorrectly describes uninterrupted growth

**Location:** notebook 03, Task 1 findings, cell 5. Notebook 02's final discussion already acknowledges the February decline and is more accurate.

“There is a continuous trend of increasing revenue” conflicts with the plotted totals:

| Month | Total revenue | Revenue per calendar day | Total revenue change |
|---|---:|---:|---:|
| January | $81,677.74 | $2,634.77 | — |
| February | $76,145.19 | $2,719.47 | −6.77% |
| March | $98,834.68 | $3,188.22 | +29.80% |
| April | $118,941.08 | $3,964.70 | +20.34% |
| May | $156,727.76 | $5,055.73 | +31.77% |
| June | $166,485.88 | $5,549.53 | +6.23% |

**Replacement finding:** “Monthly revenue increased overall from January to June, with a February decline in total revenue. February's revenue per calendar day was 3.21% above January's, showing that the shorter month matters. The largest month-to-month increase in total revenue occurred from April to May, at 31.77%.”

Keep the monthly chart chronological. In notebook 02, Task 1/cell 13, change `by_month.sort_values(ascending=False)` to `by_month.sort_index()`. Revenue ranking is a valid separate view, but it should not be the primary presentation of a time trend. Its current chart in notebook 03 is already chronological.

**Tested implementation:** `corrections.py`, section D. Use `pct_change() * 100` on the chronologically ordered totals and daily rates. Six months support a description of this period; they do not establish annual seasonality or its causes.

### P1-3. The hourly interpretation describes a decline that does not continue

**Location:** notebook 03, Task 4 findings, cell 14.

There is a large drop from the 10:00–10:59 bucket to 11:00–11:59. The statement that activity then keeps falling through the end of the day is false. Astoria has an afternoon plateau and records 3,599 transactions at 16:00 versus 3,413 at 11:00. Lower Manhattan rises to 3,051 at 15:00 versus 2,755 at 11:00; Hell's Kitchen also has afternoon rebounds.

Lower Manhattan **does** have the sharpest immediate post-peak drop, so retain that conclusion with a defined comparison:

| Store | 10:00 bucket, six-month total | 11:00 bucket | Decline | Decline % |
|---|---:|---:|---:|---:|
| Lower Manhattan | 6,297 | 2,755 | 3,542 | 56.25% |
| Hell's Kitchen | 6,957 | 3,598 | 3,359 | 48.28% |
| Astoria | 5,291 | 3,413 | 1,878 | 35.49% |

**Replacement finding:** “All three stores have their highest aggregate hourly transaction count in the 10:00–10:59 bucket. Activity drops sharply at 11:00, followed by location-specific afternoon patterns. Lower Manhattan has the largest 10:00-to-11:00 decline, at 56.25%.”

Do not present 6,957 as transactions occurring in one hour on a typical day: it is a sum across six months. Hell's Kitchen's corresponding mean is 38.44 transactions per calendar day in that one-hour bucket. Its 10:00 total is only 48 transactions above 08:00 over the entire period, so avoid treating 10:00 as a uniquely dominant staffing slot.

**Tested implementation:** `corrections.py`, sections F/G.

## Recommended improvements — strengthen the analysis and recommendations

### P2-1. Normalize weekday comparisons before inferring typical demand

**Location:** notebook 02, weekday revenue, cell 14.

The current totals are correct, but this period includes **25 Saturdays and 26 of every other weekday**. Saturday ranks last in total revenue but third in revenue per day. Monday remains highest by mean daily revenue ($3,910.66); Sunday is lowest ($3,781.94). The spread is only about 3.40% of Sunday's mean, so avoid overstating the weekday effect. Friday, not Monday, has the highest mean daily transaction count: 834.65 versus 832.42.

Use one observation per date before comparing weekdays:

```python
daily = df.groupby("transaction_date").agg(
    revenue=("line_revenue", "sum"),
    transactions=("transaction_id", "nunique")
)
weekday_metrics = daily.groupby(daily.index.day_name()).agg(
    days=("revenue", "size"),
    total_revenue=("revenue", "sum"),
    revenue_per_day=("revenue", "mean"),
    transactions_per_day=("transactions", "mean")
)
```

All dates have sales here. Investigate missing dates before assuming they represent zero sales in a different dataset. For stronger claims, show daily variability and examine month-by-weekday patterns: the strong growth trend can affect pooled comparisons. A staffing decision needs more than a small difference between six-month weekday averages.

**Tested implementation:** `corrections.py`, section E; `weekday_metrics.csv` contains the independent results.

### P2-2. Store-hour coverage prevents a simple demand or staffing conclusion

**Location:** notebook 02, cells 15–18; notebook 03, cells 13–14.

At 10:00, Hell's Kitchen and Lower Manhattan have sales on 181 dates each, but Astoria has sales on only 145. Early and late hours vary more: Hell's Kitchen has 06:00 sales on 98 dates, and Lower Manhattan has 19:00 sales on only 16. This can reflect operating schedules or data capture; it does not prove lower customer demand or closure. Opening schedules are absent.

At 10:00, recorded transactions divided by dates **with sales** are 38.44 for Hell's Kitchen, 36.49 for Astoria, and 34.79 for Lower Manhattan. Astoria and Lower Manhattan switch order relative to their aggregate counts. This diagnostic illustrates the denominator issue; excluding zero-sale dates is not a validated operating-hour adjustment.

Keep both total workload and coverage visible:

```python
hourly = df.groupby(["store_location", "time_of_day"]).agg(
    transactions=("transaction_id", "nunique"),
    days_with_sales=("transaction_date", "nunique")
)
calendar_days = (df.transaction_date.max() - df.transaction_date.min()).days + 1
hourly["transactions_per_calendar_day"] = hourly.transactions / calendar_days
```

For operational planning, obtain scheduled open hours and existing staffing, then compare transactions per confirmed open hour, by month and weekday. Use medians and upper percentiles of daily hourly volume as well as means. Do not infer queueing or staffing requirements directly from counts: drink preparation times and existing capacity are unknown. Lower Manhattan's 07:00 workload is also substantial, so a universal 08:00 start misses relevant preparation/coverage.

Notebook 02's “busiest hours” uses **units**, while its store comparison and notebook 03 use **transaction IDs**. Both peak at 10:00 in this file, so this is a metric-definition problem rather than a wrong ranking. Rename `by_hour` to `units_by_hour`, or use `.nunique()` on transaction IDs if the question is transaction workload.

**Tested implementation:** `corrections.py`, section F; `hourly_metrics.csv` and `store_day_coverage.csv` provide the evidence.

### P2-3. Explain store performance using its components

**Location:** notebook 02, store comparison/cell 7; notebook 03, location findings/cell 8.

| Store | Revenue | Transactions | Units | ATV | Units/transaction | Revenue/unit |
|---|---:|---:|---:|---:|---:|---:|
| Hell's Kitchen | $236,511.17 | 50,735 | 71,737 | $4.66 | 1.414 | $3.297 |
| Astoria | $232,243.91 | 50,599 | 70,991 | $4.59 | 1.403 | $3.271 |
| Lower Manhattan | $230,057.25 | 47,782 | 71,742 | $4.81 | 1.501 | $3.207 |

The store revenue gap is **$6,453.92**, or 2.81% of Lower Manhattan's revenue. Hell's Kitchen also has the most transactions in this dataset; answer that observed question before discussing the general principle that revenue and transaction rankings need not coincide.

“Differences may arise from differences in quantity sold” is insufficient: Lower Manhattan actually sells five more units than Hell's Kitchen while producing less revenue. Lower Manhattan's higher ATV is associated with more units per transaction, despite lower realized revenue per unit. The latter incorporates product mix and observed prices; it is not a pure pricing effect.

The useful identity is:

`Revenue = Transactions × Units per transaction × Realized revenue per unit`

Replace the repeated manual filters with one grouped table. The current code reuses a variable called `lower_manhattan` for all three stores; printed values are correct, but the naming invites later mistakes. Summing three hardcoded stores also silently excludes any future location. Section B of `corrections.py` groups all stores and reconciles to total revenue.

### P2-4. Extend the quality assessment and investigate price variation

**Location:** notebook 01, cell 5.

The existing tests pass, but “zero issues found” means zero failures among those checks, not fully verified source completeness. Additional findings:

- **15 of 80 product IDs have multiple recorded prices.** Organic Decaf Blend has prices of $12.00, $22.50, $23.00 and $28.00; Ginger Scone has $2.65, $3.25 and $4.06. These may be valid discounts, different configurations, or source inconsistencies. Investigate by store/date before making pricing claims. Revenue correctly uses the price on each record; replacing these prices with one catalog price would introduce an unsupported adjustment.
- IDs span 1–149,456, with **340 absent sequential IDs**. Gaps do not establish missing transactions, cancellations or data loss. Document them and request source reconciliation if completeness matters; do not fabricate the missing rows or replace the row count with the maximum ID.
- The current label-count comparison catches normalization collisions, but does not detect every lone whitespace variant, misspelling, blank string, or unexpected label. Inspect actual label sets and review mappings. `Coffee`, `Coffee beans`, `Tea`, and `Loose Tea` are distinct supplied categories; do not merge them as capitalization errors.
- Add finite numeric and integer quantity checks, column schema checks, and store/product identifier mapping checks. Run shared validation when loading notebooks 02 and 03, since they do not inherit notebook 01's state.

**Tested implementation:** `corrections.py`, section A. `price_variation_review.csv` lists the products requiring review. Price variation is a review flag, not a confirmed corruption error.

### P2-5. Define transaction grain and limits on basket analysis

The workbook contains one product ID per unique transaction ID. Your denominator of 149,116 and resulting ATV are mathematically correct for the supplied IDs. There is no separate receipt/basket or customer identifier proving that several different products belonged to one customer purchase. Matching store/date/timestamps do not establish a basket.

Define ATV as “calculated revenue per distinct recorded transaction ID.” Do not call the count unique customers, calculate repeat visits, or claim beverage–bakery attachment rates from this table. Collect receipt-level data before evaluating existing cross-purchase behavior. Also state that quantity × unit price is calculated sales revenue; profit, taxes, discounts outside the recorded price, refunds, and net sales are not separately identifiable.

### P2-6. Add reproducibility and an executive entry point

The tracked project consists of the workbook and three notebooks. It has no README, requirements file, data dictionary, or concise executive summary. A reviewer currently has to work through practice-task questions to find the argument.

Add a README describing the business question, fictional case context, source, period, workflow, verified KPIs, two or three recommendations, limitations, and run instructions. Include a dictionary defining the row grain and each metric. Maven describes the source as a fictional three-location NYC coffee business; present it as a portfolio case study, not real client work. Source: [Maven Coffee Shop Sales](https://mavenanalytics.io/data-playground/coffee-shop-sales). Maven's [guided project page](https://mavenanalytics.io/guided-projects/coffee-shop-dashboard) also describes the 149,116-record, 11-field dataset. Local workbook contents determine this audit's actual dimensions.

Record tested Python/package versions and declare the notebook working directory. The existing `../data/...` path works from `notebook/` and fails from the project root. A notebook-friendly alternative supporting either location is:

```python
from pathlib import Path
roots = (Path.cwd(), Path.cwd().parent)
data_path = next(
    (root / "data" / "Coffee Shop Sales.xlsx" for root in roots
     if (root / "data" / "Coffee Shop Sales.xlsx").is_file()),
    None
)
if data_path is None:
    raise FileNotFoundError("Open from the project root or notebook folder.")
df = pd.read_excel(data_path, sheet_name="Transactions")
```

Verified environment: Python 3.12.13, pandas 3.1.1, numpy 2.5.4, openpyxl 3.1.5, matplotlib 3.11.2, seaborn 0.13.2, and ipykernel 7.4.0. These versions were observed locally; a fresh dependency installation was not tested. Do not list local paths or the `.venv` directory as portable setup instructions.

## Business recommendation evaluation

| Existing recommendation | Assessment | More decision-ready version |
|---|---|---|
| Increase staff around 08:00–11:00, especially Hell's Kitchen | Reasonable pilot hypothesis. Existing caution about costs, staffing and wait times is appropriate. Volume alone cannot establish understaffing or incremental revenue. | Obtain store schedules, rosters and queue/wait observations. Pilot a shift reallocation or extra coverage in confirmed busy windows, with comparable weekday/hour observations and a control where feasible. Track upper-percentile wait time, transactions per staff-hour, labor cost and incremental contribution. Account for the period's strong growth trend. |
| Prioritize Coffee/Tea availability | Supported as a revenue exposure to monitor: those exact categories supply 66.74%. Sales do not reveal stockouts, unmet demand, inventory turnover or supplier risk. | Review unit demand by SKU/store/day and combine it with on-hand inventory, waste, stockout logs and supplier lead times before changing order quantities. Track availability and waste together. |
| Bundle beverages with Bakery products to increase ATV | Sensible experiment, not a demonstrated cross-selling opportunity. Existing caution about margins/purchasing patterns is useful. | Obtain receipt IDs and costs. Pilot a clearly priced bundle; measure incremental contribution after discounts and waste, as well as uptake and ATV. Compare with an appropriate baseline/control to check cannibalization. |
| Allocate more resources to top revenue categories | Too broad to specify an investment decision. Revenue ranking is not margin, capacity productivity or return on investment. | Identify the constraint first: availability, queueing, equipment or promotion. Require cost and capacity evidence before choosing a resource change. |

A useful decision calculation is `incremental contribution from sales − incremental labor − extra waste − promotion cost`. Inputs are unavailable here, so present it as the proposed evaluation, not a computed benefit. Choose success thresholds with management before a pilot; avoid inventing savings, revenue uplift, staffing headcount or ROI.

An additional supported insight is that January-to-June revenue grew **103.83%**, recorded transactions grew **104.18%**, and ATV changed **−0.17%**. Growth is associated primarily with recorded transaction volume rather than a higher average transaction value. This strengthens the rationale for investigating operating capacity, while leaving the cause of demand growth unresolved.

## Optional polish

- Standardize spellings and product names: Lower Manhattan, Hell's Kitchen, Barista Espresso, Sustainably Grown Organic Lg, Earl Grey Rg. Correct “continuous,” “decline,” “manhatten,” and “organic log.”
- Replace practice-task question headings with a short business narrative: question → evidence → implication → limitation → proposed action. Retain exploratory detail below the executive findings.
- Use consistent chart dimensions around 10 × 5–6 inches, readable labels and date coverage. The category share chart is accurate but unnecessarily large at 20 × 16 inches. Keep a zero baseline for bars; the monthly line's nonzero baseline is acceptable if clearly labeled.
- Add currency formatting to the store chart's y-axis, use consistent decimal precision, and format ATV to two decimals. Tiny binary floating-point tails in outputs are a presentation issue, not a revenue discrepancy. Section B shows a validated integer-cent implementation for this workbook.
- Use descriptive variable names instead of `temp`; remove the empty visualization cell, unnecessary printed Matplotlib object lists and repeated tutorial comments. End plotting cells with explicit layout/show calls for clarity.
- Use consistent store colors and export a small set of readable figures for the README. Avoid adding a dashboard or complex forecasting model solely for appearance; the corrected descriptive analysis should tell a complete story first.

## Artifacts and suggested order

1. Correct notebook 03's product chart and the monthly/hourly prose (P1-1 to P1-3).
2. Add calendar/coverage context, transaction-grain limitations, the price review and the store-performance decomposition.
3. Rewrite the recommendations as specific pilots with missing inputs and measurable outcomes.
4. Add the README, metric definitions and tested environment information, then apply the optional visual polish.

`corrections.py` contains executable replacement sections A–G and targeted checks. It does not edit your notebooks. Run it from the project root with `.venv/bin/python audit/corrections.py`. `verify_dataset.py` regenerates the independent baseline and evidence tables. `run_clean_kernels.py` executes each original from a new kernel and compares completed kernel variables with that baseline; run the baseline script first. Its generated notebook copies retain the original `../data` paths, so reopen copies with the working directory set to the original `notebook/` folder, or use the runner to regenerate them.

Execution results are in `execution_results.json`; independent results are in `verification_results.json`; tested correction values are in `correction_results.json`. Original executed copies are in `executed/`, original chart renders in `charts/`, and the two corrected chart previews in `corrected_charts/`. Only `audit/` was added to the working tree.
