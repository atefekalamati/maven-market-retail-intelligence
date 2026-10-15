# Stage 9 — Insights and Recommendations

## Scope

These findings summarise the 1997–1998 Maven Market data. Every number comes from the validated reports in `reports/`, and the source file is named under each finding. "Revenue" means quantity × retail price; "gross product profit" excludes operating costs and is not net profit.

## 1. Most of the 1998 growth came from new stores, not from existing ones

**Finding.** Reported revenue grew **+112.2%** in 1998, from $565,238.13 to $1,199,308.31. The 13 stores trading in both years grew only **+8.4%**, to $612,718.31. Of the $634,070.18 increase, $47,480.18 (**7.5%**) came from comparable stores. The other **92.5%** ($586,590.00) came from the 11 stores that first traded in 1998. Comparable stores kept almost the same customer count (5,581 in 1997, 5,575 in 1998), so their growth came from higher spend per customer, not from more customers.

*Source: `reports/annual_performance.csv`, `reports/same_store_performance.csv`.*

**Business implication.** The headline growth rate describes network expansion, not organic performance. Measured on its own, the existing estate grew in single digits.

**Recommendation.** Report reported and same-store growth together in every management pack, as the dashboard does. Set 1999 targets for the existing estate from the 8.4% same-store rate, and evaluate the 11 new stores separately once they have a full year of comparable sales.

## 2. The stable gross margin is a feature of the price list, not a business result

**Finding.** Gross margin was **59.64%** in 1997 and **59.68%** in 1998. Every month stayed between **59.54%** and **59.80%**. Each of the 1,559 products sold has exactly one retail price and one product cost for the whole period. Product unit margins range from 49.0% to 70.7%, and the blended margin moves only when the product mix changes.

*Source: `reports/eda_summary.json`, `reports/annual_performance.csv`.*

**Business implication.** The data cannot show pricing, discount or supplier-cost effects. A stable margin here only shows that the sales mix did not shift toward lower-margin products. It does not show pricing discipline.

**Recommendation.** Use gross margin as a product-mix check, not as a pricing KPI. Collect transaction-level selling prices, promotions and cost changes before running any pricing or margin-improvement analysis.

## 3. Revenue is concentrated, but not dependent on a few customers

**Finding.** The top **10%** of the 8,842 active customers (885 customers) generated **39.9%** of revenue, and the top 20% generated **58.1%**. The repeat customer rate, meaning customers who bought on more than one day, was **86.1%**.

*Source: `reports/eda_summary.json`, `reports/kpi_baseline_snapshot.csv`.*

**Business implication.** Losing a small group of high-value customers would have a visible effect on revenue. Still, no single customer or handful of customers dominates, and most customers return.

**Recommendation.** Create a top-decile retention list with spend and visit-frequency alerts, and track the top-10% revenue share each quarter. If it rises, dependency is growing.

## 4. Golden members spend the most per head, but Bronze carries the business

**Finding.** Golden members averaged **$219.72** of revenue per active customer, 23.2% more than Silver members (**$178.35**, the lowest). Bronze averaged $200.88 and Normal $195.05. Bronze members are 55.5% of active customers and generate **55.9%** of revenue ($986,502.65).

*Source: `reports/customer_segment_performance.csv`.*

**Business implication.** Tier differences in spend per customer are modest. Silver members spend less than Normal (non-premium) customers. The data shows association only: programme costs, benefits and the reasons customers join each tier are not available.

**Recommendation.** Review the Silver tier's benefits and qualification rules, since its customers spend the least. Test upgrade offers from Bronze to Golden with a control group before scaling, so the effect on spend can be measured.

## 5. Store size does not predict revenue; productivity varies widely

**Finding.** The correlation between total store area and 1998 revenue was **−0.10**. Store 22, at 35,918 sq ft, generated $5,250.88 in 1998. Store 11, at 20,319 sq ft, generated $60,275.83. Over the full period, revenue per square foot ranged from **$0.20 to $6.15**. Store 13 led on both total revenue ($170,398.94) and revenue per square foot ($6.15). By format, Supermarkets averaged $3.80 per sq ft and Small Groceries $0.31.

*Source: `reports/eda_summary.json`, `reports/store_performance.csv`, `reports/store_performance_1998.csv`.*

**Business implication.** Floor space is not the constraint on sales. Store format, location and local demand matter more, and some large stores are underused.

**Recommendation.** Rank stores by revenue per square foot rather than total revenue. Review the low-productivity Small Grocery and Mid-Size Grocery sites (format, range, local demand) before investing in more floor space.

## 6. Returns are low overall; a few products stand out, and four stores report none

**Finding.** The return-rate proxy (returned units ÷ units sold) was **0.99%** overall: 8,289 units returned out of 833,489 sold. Store rates ranged from 0.91% to **1.17%**, the highest being Store 8. Among products with at least 300 units sold, the highest proxy was Shady Lake Spaghetti at **2.93%** (14 units returned out of 478 sold). Four Small Grocery stores (Stores 2, 5, 14 and 22) have no return records at all.

*Source: `reports/eda_summary.json`, `reports/store_return_rates.csv`, `reports/product_return_rates.csv`.*

**Business implication.** Returns are not a material cost problem at network level. The product outliers rest on small absolute counts, so a few units move the rate. Zero returns over two years at four stores more likely reflects a recording gap than perfect quality.

**Recommendation.** Use the dashboard's flags (≥ 0.5 pp above the network rate = review) as an operational alert, not a target. Check how Stores 2, 5, 14 and 22 record returns. Investigate the top products only if their rates persist as volume grows.

## Limitations

- **No order identifier.** Transactions are product lines without a receipt or order ID, so order count, basket size and average order value cannot be measured.
- **Return-rate proxy.** Returns cannot be linked to a customer or the original sale. The rate compares returned and sold units in the same period and filter context. It is directional, not a matched return rate.
- **Fixed price list.** Each product has one price and one cost for the whole period, so margin analysis only measures product mix. No discount, promotion or cost-change data is available.
- **Two years only.** Seasonality and trend claims rest on 24 months, and 11 of the 24 stores have only one year of sales.
- **Gross, not net.** Gross product profit excludes operating, labour and occupancy costs; store profitability cannot be assessed.
- **Data quality.** 9 transaction rows and 5 return rows look like exact duplicates; they are flagged but kept, because no source ID can confirm them (`reports/data_quality_report.md`).
- **Association, not causation.** Membership-tier and store-format differences describe the data; they do not prove that the tier or format causes the difference.
