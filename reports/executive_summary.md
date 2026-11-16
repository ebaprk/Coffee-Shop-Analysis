# Coffee Shop Sales: Executive Summary

**Coverage:** January-June 2023 | **Business:** Three fictional Maven Roasters locations

## Business question and approach

Which products, stores, and time periods drive sales, and what should management investigate to improve inventory and service planning? The analysis uses 149,116 recorded transaction IDs from the Maven Analytics Coffee Shop Sales workbook. Pandas calculates revenue as quantity multiplied by recorded unit price; monthly, weekday, store, and product comparisons are checked against an independent workbook reconciliation.

## Findings

1. **Sales totaled $698,812.33 across 214,470 units.** Average recorded transaction value was $4.69. Hell's Kitchen led store revenue at $236,511.17, while Lower Manhattan had the highest average recorded transaction value at $4.81. Management should consider both transaction volume and transaction value when comparing locations.
2. **February's total revenue fell 6.77%, while daily revenue rose 3.21%.** January generated $81,677.74 across 31 days; February generated $76,145.19 across 28. Monthly totals then increased through June. Daily rates provide essential context for interpreting totals.
3. **Coffee and Tea contributed 66.74% of revenue.** Sustainably Grown Organic Lg was the highest-revenue individual product at $21,151.75. These results identify sales priorities, while profitability and stockout risk require cost and inventory data.
4. **All stores peaked at 10 AM in aggregate recorded transactions.** Counts fell sharply at 11 AM, then fluctuated by location. Lower Manhattan's immediate decline was 56.25%. The counts summarize six months; they do not describe one typical day or prove a staffing shortage.
5. **Saturday's ranking changed after adjusting for observed days.** It ranked last in total revenue but third per day, averaging $3,875.78 across 25 Saturdays. Other weekdays had 26 observations. Saturday and Thursday differed by approximately $0.10 per day, limiting the practical significance of their ranking.

## Recommendations

- **Review morning service capacity by store.** Confirm opening schedules, current staffing, service times, and queues. If bottlenecks are observed, test a limited staffing adjustment and measure wait times and labor costs before making permanent changes.
- **Prioritize inventory review for leading beverages.** Combine sales patterns with stockouts, replenishment lead times, and margins to set appropriate inventory levels. Treat beverage-and-bakery bundles as an experiment requiring suitable basket data and a measured trial.
- **Report totals alongside daily rates.** Use consistent date coverage and metric definitions before comparing months or weekdays or allocating resources.

## Limitations

The dataset does not establish costs, profit, confirmed operating hours, staffing capacity, or complete customer baskets through a separate receipt ID. Recorded price variation was retained. Six months of descriptive data cannot establish annual seasonality, causal effects, or the expected financial impact of a proposed intervention.

**Source:** [Maven Analytics - Coffee Shop Sales](https://mavenanalytics.io/data-playground/coffee-shop-sales). Supporting calculations are in the three project notebooks and `audit/` reference tables.
