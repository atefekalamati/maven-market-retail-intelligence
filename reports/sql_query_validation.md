# SQL Server query validation

All queries were run on SQL Server 2022 Express (`localhost\SQLEXPRESS`), database `MavenMarketDW`,
after loading `data/model` with `scripts/load_sql_server.py`. Expected values come from the comments in
each query and from the project's validated reports. No analysis number was changed.

**Result: 6/6 load checks, 10/10 analytical queries and 16/16 practice queries pass.**

## Load

| check | expected | actual | pass/fail |
|---|---|---|---|
| analytics.DimDate rows | 737 | 737 | Pass |
| analytics.DimCustomer rows | 10,281 | 10,281 | Pass |
| analytics.DimProduct rows | 1,560 | 1,560 | Pass |
| analytics.DimStore rows | 24 | 24 | Pass |
| analytics.FactSales rows | 269,720 | 269,720 | Pass |
| analytics.FactReturns rows | 7,087 | 7,087 | Pass |
| Total revenue | 1,764,546.44 | 1,764,546.44 | Pass |
| Total gross profit | 1,052,818.78 | 1,052,818.78 | Pass |

## 02_analytical_queries.sql

| query | expected | actual | pass/fail |
|---|---|---|---|
| Q1 Annual KPIs and YoY growth | 1997 revenue 565,238.13; 1998 1,199,308.31; growth +112.2%; margin ~59.6-59.7% both years | 565,238.13; 1,199,308.31; growth 112.18%; margin 59.64% / 59.68% | Pass |
| Q2 Same-store growth | 13 stores, 565,238.13 -> 612,718.31, +8.4% | 13 stores, 565,238.13 -> 612,718.31, +8.40% | Pass |
| Q3 Source of 1998 growth | Increase 634,070.18; comparable 47,480.18 (7.5%); new stores 586,590.00 (92.5%) | Comparable 13 stores 47,480.18 (7.5%); new 11 stores 586,590.00 (92.5%); total 634,070.18 | Pass |
| Q4 Monthly trend | 24 rows; December 1998 strongest month (120,160.84) | 24 rows; 1998-12 = 120,160.84 is the maximum; running total ends at 1,764,546.44 | Pass |
| Q5 Store productivity ranking | Store size barely relates to revenue; query ranks 1998 only; Store 13 = 6.15 per sq ft is the full-period figure | Query (1998 only) ranks 24 stores within country. Full-period check: Store 13 = 6.15, highest. Size vs 1998 revenue: r = -0.10 | Pass (see note 1) |
| Q6 Customer concentration | 8,842 active customers; top 10% (885) = 39.9% of revenue | 8,842; 885; 39.9% | Pass |
| Q7 Return rate by store | Store 8 highest at 1.17%; Stores 2, 5, 14, 22 show 0 | Store 8 = 1.17% (480 / 40,994 units); Stores 2, 5, 14, 22 = 0.00% | Pass |
| Q8 Revenue per customer by card | Golden 219.72 highest; Silver 178.35 lowest; Bronze 55.9% of revenue | Golden 219.72; Silver 178.35; Bronze 55.9% | Pass |
| Q9 Data-quality checks | 0 problems on the four integrity checks; 18 duplicate-candidate rows (9 pairs) | 0 / 0 / 0 / 0; 18 rows in 9 groups | Pass |
| Q10 Reporting view and covering index | View totals equal the model; index keys (transaction_date_key, store_key) include (revenue, gross_product_profit, quantity_sold) | View: 444 rows, revenue 1,764,546.44, profit 1,052,818.78; index definition as expected | Pass (see note 3) |

## 03_practice_queries.sql

Practice queries have no expected values in their comments. Each one was run and checked against an
independent count or total.

| query | expected | actual | pass/fail |
|---|---|---|---|
| P1 Top 5 products 1998 | 5 rows, ordered by revenue | 5 rows; Great Pumpernickel Bread first (1,742.84) | Pass |
| P2 Top 3 products per store | 24 stores x 3 = 72 rows | 72 rows | Pass |
| P3 Quarterly revenue by country 1998 | 3 countries; quarters add up to 1998 revenue 1,199,308.31 | Canada 107,674.34 + Mexico 478,915.66 + USA 612,718.31 = 1,199,308.31 | Pass |
| P4 YoY growth per store | 13 stores x 2 years + 11 new stores = 37 rows; new stores have no growth | 37 rows; e.g. Store 11 +9.5%, Store 13 -4.6% | Pass |
| P5 Lost customers | Fewer than the 5,581 customers of 1997 | 782 | Pass |
| P6 New customers per month | 24 months; adds up to 8,842 active customers | 24 rows; 8,842 first purchases | Pass |
| P7 Second highest store | Second store after Store 13 (170,398.94) | Store 17, 157,695.90 | Pass |
| P8 Brand share of revenue | 111 brands; shares add up to 100% | 111 rows; shares add up to 100.01% (rounding) | Pass |
| P9 Running total per store 1998 | 24 stores x 12 months = 288 rows | 288 rows; running totals increase within each store | Pass |
| P10 Stores above average 1998 | Average = 1,199,308.31 / 24 = 49,971.18 | 16 stores above 49,971.18 | Pass |
| P11 Suspected duplicates | 9 groups (the 18 flagged rows) | 9 groups, 2 copies each | Pass |
| P12 Dedupe with ROW_NUMBER | 269,720 - 9 = 269,711 | 269,711 | Pass |
| P13 Weekend vs weekday | Adds up to 1,764,546.44 | Weekday 1,262,450.75 (71.5%) + weekend 502,095.69 (28.5%) | Pass |
| P14 Products never returned | Same count with NOT EXISTS | 20 (NOT EXISTS: 20) | Pass |
| P15 Average days between purchases | 10 customers with at least 6 purchase days | 10 rows; 8.07 to 9.28 days | Pass |
| P16 Revenue per customer by income and card | 8 income bands x 4 cards = 32 rows | 32 rows | Pass |

## Notes

1. **Q5 scope.** The query ranks stores on 1998 revenue per square foot, where Store 19 (Canada, 3.69)
   is highest and Store 13 is first in the USA (3.00). The expected value 6.15 is Store 13 over the
   full 1997-1998 period, which a separate query confirmed. Both statements hold; they cover different periods.
   The Q5 comment in `02_analytical_queries.sql` now explains this difference.
2. **Q9 duplicate count.** The query counts rows and returns 18, as its comment states: 9 exact-looking
   pairs with both rows flagged and kept. This matches `reports/cleaning_validation.json`, and P11
   returns the same 9 groups.
3. **Q10 index.** `CREATE INDEX` fails if the index already exists. To rerun Q10, drop the index first:
   `DROP INDEX IF EXISTS IX_FactSales_Date_Store_Covering ON analytics.FactSales;`.
   The view uses `CREATE OR ALTER` and can be rerun safely.
