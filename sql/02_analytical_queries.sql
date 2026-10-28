/*  راهنمای فارسی: هر کوئری به یک سؤال مدیریتی جواب می‌دهد.
    در جلسه اول سؤال کسب‌وکار را بگو، بعد کوئری را خط‌به‌خط، بعد نتیجه را.
    عادت‌های مهم در همهٔ کوئری‌ها: NULLIF(x, 0) جلوی تقسیم بر صفر،
    100.0 * جلوی تقسیم صحیح، CAST(... AS DECIMAL) برای گرد کردن.   */

/* =====================================================================
   Maven Market Retail Intelligence - analytical T-SQL queries
   Target: SQL Server, schema "analytics" (sql/01_create_star_schema.sql)
   Each query answers one business question and states the expected
   result from the project's validated reports.
   ===================================================================== */


/* ---------------------------------------------------------------------
   Q1. Annual KPIs and year-over-year growth
   Question: did sales growth also improve gross profit?
   Expected: 1997 revenue 565,238.13 / 1998 1,199,308.31,
             revenue growth +112.2%, margin ~59.6-59.7% both years
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: فروش و سود هر سال چقدر بود و چقدر رشد کرد؟
    چطور کار می‌کند: CTE فروش هر سال را جمع می‌زند؛ LAG عدد سال قبل را کنار هر سال می‌آورد؛ NULLIF جلوی تقسیم بر صفر را می‌گیرد.
    در جلسه بگو: «فروش ۱۱۲٪ رشد کرد و حاشیهٔ سود هر دو سال حدود ۵۹٫۷٪ ماند.»
*/
WITH yearly AS (
    SELECT
        d.[year],
        SUM(f.revenue)              AS revenue,
        SUM(f.gross_product_profit) AS gross_profit,
        SUM(f.quantity_sold)        AS quantity_sold,
        COUNT(DISTINCT f.store_key) AS active_stores
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY d.[year]
)
SELECT
    [year],
    revenue,
    gross_profit,
    CAST(100.0 * gross_profit / NULLIF(revenue, 0) AS DECIMAL(6,2)) AS gross_margin_pct,
    active_stores,
    CAST(100.0 * (revenue - LAG(revenue) OVER (ORDER BY [year]))
         / NULLIF(LAG(revenue) OVER (ORDER BY [year]), 0) AS DECIMAL(8,2)) AS revenue_growth_pct
FROM yearly
ORDER BY [year];


/* ---------------------------------------------------------------------
   Q2. Same-store (comparable) growth
   Question: how much did stores that traded in BOTH years grow?
   A store is comparable if it has sales in 1997 and in 1998.
   Expected: 13 stores, 565,238.13 -> 612,718.31, growth +8.4%
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: فروشگاه‌هایی که هر دو سال باز بودند چقدر رشد کردند؟ (رشد هم‌سنج)
    چطور کار می‌کند: HAVING COUNT(DISTINCT year) = 2 فروشگاه‌های فعال در هر دو سال را پیدا می‌کند؛ بعد فقط فروش همین‌ها سالانه جمع و با LAG مقایسه می‌شود.
    در جلسه بگو: «رشد واقعی فقط ۸٫۴٪ بود؛ مهم‌ترین یافتهٔ پروژه.»
*/
WITH store_years AS (
    SELECT f.store_key
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY f.store_key
    HAVING COUNT(DISTINCT d.[year]) = 2
),
comparable AS (
    SELECT
        d.[year],
        SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    WHERE f.store_key IN (SELECT store_key FROM store_years)
    GROUP BY d.[year]
)
SELECT
    [year],
    revenue,
    (SELECT COUNT(*) FROM store_years) AS comparable_stores,
    CAST(100.0 * (revenue - LAG(revenue) OVER (ORDER BY [year]))
         / NULLIF(LAG(revenue) OVER (ORDER BY [year]), 0) AS DECIMAL(8,2)) AS same_store_growth_pct
FROM comparable
ORDER BY [year];


/* ---------------------------------------------------------------------
   Q3. Where did the 1998 growth come from?
   Splits the revenue increase into comparable stores vs new stores.
   Expected: total increase 634,070.18;
             comparable 47,480.18 (7.5%), new stores 586,590.00 (92.5%)
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: رشد بزرگ ۱۹۹۸ از کجا آمد؟
    چطور کار می‌کند: SUM(CASE…) فروش ۹۷ و ۹۸ هر فروشگاه را دو ستون می‌کند (pivot)؛ فروشگاه‌ها به قدیمی و جدید تقسیم می‌شوند؛ SUM(SUM()) OVER () جمع کل را می‌دهد تا سهم هر گروه حساب شود.
    در جلسه بگو: «۹۲٫۵٪ رشد از ۱۱ فروشگاه جدید آمد، نه از بهتر شدن کار.»
*/
WITH by_store_year AS (
    SELECT
        f.store_key,
        SUM(CASE WHEN d.[year] = 1997 THEN f.revenue ELSE 0 END) AS rev_1997,
        SUM(CASE WHEN d.[year] = 1998 THEN f.revenue ELSE 0 END) AS rev_1998
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY f.store_key
),
labelled AS (
    SELECT
        CASE WHEN rev_1997 > 0 THEN 'Comparable stores' ELSE 'New stores' END AS store_group,
        rev_1998 - rev_1997 AS revenue_change
    FROM by_store_year
)
SELECT
    store_group,
    COUNT(*)            AS stores,
    SUM(revenue_change) AS revenue_change,
    CAST(100.0 * SUM(revenue_change) / SUM(SUM(revenue_change)) OVER () AS DECIMAL(6,1)) AS share_of_growth_pct
FROM labelled
GROUP BY store_group;


/* ---------------------------------------------------------------------
   Q4. Monthly trend: month-over-month change, running total,
       3-month moving average
   Question: how did revenue move month by month?
   Expected: 24 rows; December 1998 is the strongest month (120,160.84)
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: روند ماه‌به‌ماه فروش چطور بود؟
    چطور کار می‌کند: LAG تغییر هر ماه نسبت به ماه قبل را می‌دهد؛ SUM OVER با ROWS UNBOUNDED PRECEDING جمع تجمعی است؛ AVG با ROWS BETWEEN 2 PRECEDING میانگین متحرک ۳ ماهه است.
    در جلسه بگو: «میانگین متحرک نوسان را صاف می‌کند تا روند دیده شود؛ بهترین ماه دسامبر ۱۹۹۸ بود.»
*/
WITH monthly AS (
    SELECT
        d.year_month_sort,
        d.year_month,
        SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY d.year_month_sort, d.year_month
)
SELECT
    year_month,
    revenue,
    revenue - LAG(revenue) OVER (ORDER BY year_month_sort)                       AS mom_change,
    SUM(revenue) OVER (ORDER BY year_month_sort ROWS UNBOUNDED PRECEDING)        AS running_total,
    AVG(revenue) OVER (ORDER BY year_month_sort ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3m
FROM monthly
ORDER BY year_month_sort;


/* ---------------------------------------------------------------------
   Q5. Store productivity ranking within each country (1998)
   Question: which stores use their floor space best?
   Expected: store size barely relates to revenue. Note: this query ranks
             1998 only; the 6.15 per sq ft for Store 13 quoted in the
             project is the full-period (1997+1998) figure
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: کدام فروشگاه از فضایش بهتر استفاده می‌کند؟
    چطور کار می‌کند: فروش تقسیم بر متراژ؛ RANK() OVER (PARTITION BY country) فروشگاه‌ها را داخل هر کشور جدا رتبه می‌دهد.
    در جلسه بگو: «فروشگاه بزرگ‌تر یعنی فروش بیشتر نیست؛ باید فروش هر فوت مربع را دید.»
*/
WITH store_1998 AS (
    SELECT
        s.store_name,
        s.store_country,
        s.store_type,
        s.total_sqft,
        SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key  = f.transaction_date_key
    JOIN analytics.DimStore  AS s ON s.store_key = f.store_key
    WHERE d.[year] = 1998
    GROUP BY s.store_name, s.store_country, s.store_type, s.total_sqft
)
SELECT
    store_country,
    store_name,
    store_type,
    revenue,
    CAST(revenue / NULLIF(total_sqft, 0) AS DECIMAL(10,2)) AS revenue_per_sqft,
    RANK() OVER (PARTITION BY store_country
                 ORDER BY revenue / NULLIF(total_sqft, 0) DESC) AS rank_in_country
FROM store_1998
ORDER BY store_country, rank_in_country;


/* ---------------------------------------------------------------------
   Q6. Customer concentration: share of revenue from the top 10%
   Question: how dependent is revenue on a small group of customers?
   Expected: 8,842 active customers; top 10% (885) = 39.9% of revenue
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: چقدر به مشتری‌های بزرگ وابسته‌ایم؟
    چطور کار می‌کند: ROW_NUMBER مشتری‌ها را بر اساس خرید مرتب می‌کند؛ COUNT(*) OVER () تعداد کل را کنار هر ردیف می‌آورد؛ CEILING ده درصد اول را گرد به بالا جدا می‌کند.
    در جلسه بگو: «۱۰٪ مشتری‌ها ۳۹٫۹٪ فروش را می‌سازند؛ وابستگی هست ولی خطرناک نیست.»
*/
WITH customer_revenue AS (
    SELECT customer_key, SUM(revenue) AS revenue
    FROM analytics.FactSales
    GROUP BY customer_key
),
ranked AS (
    SELECT
        customer_key,
        revenue,
        ROW_NUMBER() OVER (ORDER BY revenue DESC, customer_key) AS rn,
        COUNT(*)     OVER ()                                    AS customers
    FROM customer_revenue
)
SELECT
    MAX(customers)                                             AS active_customers,
    SUM(CASE WHEN rn <= CEILING(customers * 0.10) THEN 1 ELSE 0 END) AS top_10pct_customers,
    CAST(100.0 * SUM(CASE WHEN rn <= CEILING(customers * 0.10) THEN revenue ELSE 0 END)
         / SUM(revenue) AS DECIMAL(5,1))                       AS top_10pct_revenue_share
FROM ranked;


/* ---------------------------------------------------------------------
   Q7. Return-rate proxy by store, including stores with no returns
   Question: where are returns unusually high, and where are they missing?
   A LEFT JOIN keeps stores that never recorded a return (rate = 0).
   Expected: Store 8 highest at 1.17%; Stores 2, 5, 14, 22 show 0
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: نرخ مرجوعی هر فروشگاه چقدر است و کدام فروشگاه مرجوعی ثبت نمی‌کند؟
    چطور کار می‌کند: فروش و مرجوعی اول جدا جمع زده می‌شوند و بعد join (اگر دو Fact مستقیم join شوند عددها چندبرابر می‌شوند: fan-out)؛ LEFT JOIN فروشگاه‌های بدون مرجوعی را نگه می‌دارد؛ ISNULL نبود را صفر می‌کند.
    در جلسه بگو: «همین LEFT JOIN نشان داد ۴ فروشگاه در دو سال هیچ مرجوعی ثبت نکرده‌اند؛ احتمالاً خطای ثبت.»
*/
WITH sold AS (
    SELECT store_key, SUM(quantity_sold) AS units_sold
    FROM analytics.FactSales
    GROUP BY store_key
),
returned AS (
    SELECT store_key, SUM(return_quantity) AS units_returned
    FROM analytics.FactReturns
    GROUP BY store_key
)
SELECT
    s.store_name,
    s.store_type,
    so.units_sold,
    ISNULL(r.units_returned, 0) AS units_returned,
    CAST(100.0 * ISNULL(r.units_returned, 0) / NULLIF(so.units_sold, 0) AS DECIMAL(5,2)) AS return_rate_pct
FROM sold                    AS so
JOIN analytics.DimStore      AS s ON s.store_key = so.store_key
LEFT JOIN returned           AS r ON r.store_key = so.store_key
ORDER BY return_rate_pct DESC;


/* ---------------------------------------------------------------------
   Q8. Revenue per customer by membership tier
   Expected: Golden 219.72 (highest), Silver 178.35 (lowest);
             Bronze carries 55.9% of revenue
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: کدام سطح عضویت باارزش‌تر است؟
    چطور کار می‌کند: COUNT(DISTINCT) مشتری‌های هر سطح را می‌شمارد؛ فروش هر مشتری و سهم هر سطح از کل با SUM(SUM()) OVER () حساب می‌شود.
    در جلسه بگو: «طلایی‌ها نفری بیشترین خرید را دارند؛ نقره‌ای‌ها حتی از مشتری عادی کمتر.»
*/
SELECT
    c.member_card,
    COUNT(DISTINCT f.customer_key)                                    AS active_customers,
    SUM(f.revenue)                                                    AS revenue,
    CAST(SUM(f.revenue) / COUNT(DISTINCT f.customer_key) AS DECIMAL(10,2)) AS revenue_per_customer,
    CAST(100.0 * SUM(f.revenue) / SUM(SUM(f.revenue)) OVER () AS DECIMAL(5,1)) AS revenue_share_pct
FROM analytics.FactSales   AS f
JOIN analytics.DimCustomer AS c ON c.customer_key = f.customer_key
GROUP BY c.member_card
ORDER BY revenue_per_customer DESC;


/* ---------------------------------------------------------------------
   Q9. Data-quality checks (run after every load)
   Each row is one check; a passing check returns 0 problems.
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: داده‌ای که بارگذاری شد سالم است؟
    چطور کار می‌کند: پنج چک کیفیت داده با UNION ALL در یک خروجی؛ NOT EXISTS کلیدهای بی‌صاحب را پیدا می‌کند.
    در جلسه بگو: «بعد از هر بارگذاری اجرایش می‌کنم؛ اگر همه صفر باشند داده سالم است.»
*/
SELECT 'Sales with unknown product' AS check_name, COUNT(*) AS problems
FROM analytics.FactSales AS f
WHERE NOT EXISTS (SELECT 1 FROM analytics.DimProduct AS p WHERE p.product_key = f.product_key)
UNION ALL
SELECT 'Sales with unknown store', COUNT(*)
FROM analytics.FactSales AS f
WHERE NOT EXISTS (SELECT 1 FROM analytics.DimStore AS s WHERE s.store_key = f.store_key)
UNION ALL
SELECT 'Non-positive quantity', COUNT(*)
FROM analytics.FactSales
WHERE quantity_sold <= 0
UNION ALL
SELECT 'Revenue <> quantity x price', COUNT(*)
FROM analytics.FactSales
WHERE ABS(revenue - quantity_sold * unit_retail_price) > 0.01
UNION ALL
SELECT 'Duplicate-candidate sales lines', COUNT(*)
FROM analytics.FactSales
WHERE duplicate_candidate = 1;   -- expected 18: 9 exact-looking pairs, both rows flagged and kept


/* ---------------------------------------------------------------------
   Q10. A reporting view for Power BI
   Power BI reads a stable view instead of raw tables, so table changes
   do not break the report.
   --------------------------------------------------------------------- */
/*  [فارسی]
    برای چیست: یک منبع ثابت و سریع برای Power BI
    چطور کار می‌کند: View فروش ماهانهٔ هر فروشگاه را آماده نگه می‌دارد؛ Covering index با INCLUDE باعث می‌شود SQL Server به جدول اصلی برنگردد.
    در جلسه بگو: «Power BI به View وصل می‌شود، نه جدول خام؛ اگر جدول عوض شود گزارش نمی‌شکند.»
*/
GO
CREATE OR ALTER VIEW analytics.vw_StoreMonthlySales AS
SELECT
    d.year_month,
    d.[year],
    s.store_name,
    s.store_country,
    s.sales_region,
    s.is_same_store_comparable,
    SUM(f.revenue)              AS revenue,
    SUM(f.gross_product_profit) AS gross_profit,
    SUM(f.quantity_sold)        AS quantity_sold
FROM analytics.FactSales AS f
JOIN analytics.DimDate   AS d ON d.date_key  = f.transaction_date_key
JOIN analytics.DimStore  AS s ON s.store_key = f.store_key
GROUP BY d.year_month, d.[year], s.store_name, s.store_country,
         s.sales_region, s.is_same_store_comparable;
GO

/* Supporting index: a covering index for date-filtered store reports.
   The key columns serve the joins and filters; INCLUDE adds the summed
   columns so SQL Server does not go back to the table for them. */
CREATE NONCLUSTERED INDEX IX_FactSales_Date_Store_Covering
    ON analytics.FactSales (transaction_date_key, store_key)
    INCLUDE (revenue, gross_product_profit, quantity_sold);
