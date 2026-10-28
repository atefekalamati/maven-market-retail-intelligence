/*  راهنمای فارسی: اول هر سؤال را خودت بدون نگاه به جواب بنویس، بعد مقایسه کن.
    ۵ الگوی کلیدی:
    ۱. نفر N‌ام هر گروه:  ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)   (P2, P12)
    ۲. مقایسه با قبل:     LAG(...) OVER (ORDER BY ...)                         (P4, P15)
    ۳. سهم از کل:         x / SUM(x) OVER ()                                   (P8, P13)
    ۴. چیزی که نیست:      NOT EXISTS  یا  LEFT JOIN ... IS NULL                (P5, P14)
    ۵. ستون کردن ردیف‌ها:  SUM(CASE WHEN ...)                                  (P3)      */

/* =====================================================================
   Maven Market - live practice: questions an interviewer may ask
   "write a query for ...". Try each one yourself first, then compare
   with the solution. Schema: analytics (sql/01_create_star_schema.sql)
   ===================================================================== */


/* P1. Top 5 products by revenue in 1998 */
/*  [فارسی] سؤال: ۵ کالای پرفروش ۱۹۹۸
    الگو: TOP + ORDER BY (در SQL Server به‌جای LIMIT).  */
SELECT TOP 5
    p.product_name,
    p.product_brand,
    SUM(f.revenue) AS revenue
FROM analytics.FactSales  AS f
JOIN analytics.DimDate    AS d ON d.date_key    = f.transaction_date_key
JOIN analytics.DimProduct AS p ON p.product_key = f.product_key
WHERE d.[year] = 1998
GROUP BY p.product_name, p.product_brand
ORDER BY revenue DESC;


/* P2. Top 3 products in EACH store (top-N per group) */
/*  [فارسی] سؤال: ۳ کالای پرفروش هر فروشگاه
    الگو: نفر N‌ام هر گروه: ROW_NUMBER() OVER (PARTITION BY …) و بعد WHERE rn <= 3. پرتکرارترین سؤال مصاحبه.  */
WITH product_store AS (
    SELECT
        f.store_key,
        f.product_key,
        SUM(f.revenue) AS revenue,
        ROW_NUMBER() OVER (PARTITION BY f.store_key ORDER BY SUM(f.revenue) DESC, f.product_key) AS rn
    FROM analytics.FactSales AS f
    GROUP BY f.store_key, f.product_key
)
SELECT s.store_name, p.product_name, ps.revenue, ps.rn
FROM product_store        AS ps
JOIN analytics.DimStore   AS s ON s.store_key   = ps.store_key
JOIN analytics.DimProduct AS p ON p.product_key = ps.product_key
WHERE ps.rn <= 3
ORDER BY s.store_name, ps.rn;


/* P3. Quarterly revenue by country in 1998 as columns (pivot) */
/*  [فارسی] سؤال: فروش فصلی هر کشور به شکل ستون
    الگو: Pivot با SUM(CASE WHEN …).  */
SELECT
    s.store_country,
    SUM(CASE WHEN d.quarter_number = 1 THEN f.revenue ELSE 0 END) AS q1,
    SUM(CASE WHEN d.quarter_number = 2 THEN f.revenue ELSE 0 END) AS q2,
    SUM(CASE WHEN d.quarter_number = 3 THEN f.revenue ELSE 0 END) AS q3,
    SUM(CASE WHEN d.quarter_number = 4 THEN f.revenue ELSE 0 END) AS q4
FROM analytics.FactSales AS f
JOIN analytics.DimDate   AS d ON d.date_key  = f.transaction_date_key
JOIN analytics.DimStore  AS s ON s.store_key = f.store_key
WHERE d.[year] = 1998
GROUP BY s.store_country
ORDER BY s.store_country;


/* P4. Year-over-year growth for each store (LAG per store) */
/*  [فارسی] سؤال: رشد سالانهٔ هر فروشگاه
    الگو: LAG با PARTITION BY store تا سال قبلِ همان فروشگاه کنار هر سال بیاید.  */
WITH store_year AS (
    SELECT f.store_key, d.[year], SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY f.store_key, d.[year]
)
SELECT
    s.store_name,
    sy.[year],
    sy.revenue,
    LAG(sy.revenue) OVER (PARTITION BY sy.store_key ORDER BY sy.[year]) AS prev_revenue,
    CAST(100.0 * (sy.revenue - LAG(sy.revenue) OVER (PARTITION BY sy.store_key ORDER BY sy.[year]))
         / NULLIF(LAG(sy.revenue) OVER (PARTITION BY sy.store_key ORDER BY sy.[year]), 0) AS DECIMAL(8,1)) AS growth_pct
FROM store_year         AS sy
JOIN analytics.DimStore AS s ON s.store_key = sy.store_key
ORDER BY s.store_name, sy.[year];


/* P5. Customers who bought in 1997 but not in 1998 (lost customers) */
/*  [فارسی] سؤال: مشتری‌هایی که ۹۷ خریدند ولی ۹۸ نه (ریزش)
    الگو: Anti-join با NOT EXISTS.  */
SELECT COUNT(*) AS lost_customers
FROM (
    SELECT DISTINCT f.customer_key
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    WHERE d.[year] = 1997
) AS c97
WHERE NOT EXISTS (
    SELECT 1
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    WHERE d.[year] = 1998
      AND f.customer_key = c97.customer_key
);


/* P6. New customers per month (month of first purchase) */
/*  [فارسی] سؤال: تعداد مشتری جدید هر ماه
    الگو: اولین خرید هر مشتری با MIN(date)، بعد گروه‌بندی بر اساس ماه.  */
WITH first_purchase AS (
    SELECT f.customer_key, MIN(d.[date]) AS first_date
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    GROUP BY f.customer_key
)
SELECT
    YEAR(first_date)  AS [year],
    MONTH(first_date) AS [month],
    COUNT(*)          AS new_customers
FROM first_purchase
GROUP BY YEAR(first_date), MONTH(first_date)
ORDER BY [year], [month];


/* P7. The store with the SECOND highest revenue (ties handled) */
/*  [فارسی] سؤال: فروشگاه با دومین فروش بالا
    الگو: DENSE_RANK و WHERE rnk = 2؛ مقدارهای مساوی درست حساب می‌شوند.  */
WITH ranked AS (
    SELECT
        s.store_name,
        SUM(f.revenue) AS revenue,
        DENSE_RANK() OVER (ORDER BY SUM(f.revenue) DESC) AS rnk
    FROM analytics.FactSales AS f
    JOIN analytics.DimStore  AS s ON s.store_key = f.store_key
    GROUP BY s.store_name
)
SELECT store_name, revenue
FROM ranked
WHERE rnk = 2;


/* P8. Each brand's share of total revenue */
/*  [فارسی] سؤال: سهم هر برند از کل فروش
    الگو: SUM(SUM()) OVER () برای جمع کل در همان کوئری.  */
SELECT
    p.product_brand,
    SUM(f.revenue) AS revenue,
    CAST(100.0 * SUM(f.revenue) / SUM(SUM(f.revenue)) OVER () AS DECIMAL(5,2)) AS share_pct
FROM analytics.FactSales  AS f
JOIN analytics.DimProduct AS p ON p.product_key = f.product_key
GROUP BY p.product_brand
ORDER BY revenue DESC;


/* P9. Running total of 1998 revenue inside each store, by month */
/*  [فارسی] سؤال: جمع تجمعی ماهانهٔ هر فروشگاه
    الگو: SUM OVER (PARTITION BY store ORDER BY month ROWS UNBOUNDED PRECEDING).  */
WITH store_month AS (
    SELECT f.store_key, d.year_month_sort, d.year_month, SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    WHERE d.[year] = 1998
    GROUP BY f.store_key, d.year_month_sort, d.year_month
)
SELECT
    s.store_name,
    sm.year_month,
    sm.revenue,
    SUM(sm.revenue) OVER (PARTITION BY sm.store_key ORDER BY sm.year_month_sort
                          ROWS UNBOUNDED PRECEDING) AS running_total
FROM store_month        AS sm
JOIN analytics.DimStore AS s ON s.store_key = sm.store_key
ORDER BY s.store_name, sm.year_month_sort;


/* P10. Stores whose 1998 revenue is above the average store */
/*  [فارسی] سؤال: فروشگاه‌های بالاتر از میانگین
    الگو: AVG() OVER () کنار هر ردیف، بعد فیلتر.  */
WITH store_1998 AS (
    SELECT f.store_key, SUM(f.revenue) AS revenue
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
    WHERE d.[year] = 1998
    GROUP BY f.store_key
)
SELECT s.store_name, x.revenue, x.avg_revenue
FROM (
    SELECT store_key, revenue, AVG(revenue) OVER () AS avg_revenue
    FROM store_1998
) AS x
JOIN analytics.DimStore AS s ON s.store_key = x.store_key
WHERE x.revenue > x.avg_revenue
ORDER BY x.revenue DESC;


/* P11. Find suspected duplicate sales lines (same day, product,
        customer, store and quantity more than once) */
/*  [فارسی] سؤال: پیدا کردن ردیف‌های تکراری
    الگو: GROUP BY روی همهٔ ستون‌ها و HAVING COUNT(*) > 1.  */
SELECT
    transaction_date_key, product_key, customer_key, store_key, quantity_sold,
    COUNT(*) AS copies
FROM analytics.FactSales
GROUP BY transaction_date_key, product_key, customer_key, store_key, quantity_sold
HAVING COUNT(*) > 1
ORDER BY copies DESC;


/* P12. Keep one row of each duplicate group (dedupe with ROW_NUMBER) */
/*  [فارسی] سؤال: حذف تکراری‌ها و نگه داشتن یکی
    الگو: ROW_NUMBER و نگه داشتن rn = 1؛ سؤال کلاسیک.  */
WITH numbered AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY transaction_date_key, product_key, customer_key, store_key, quantity_sold
               ORDER BY sales_line_key) AS rn
    FROM analytics.FactSales
)
SELECT COUNT(*) AS rows_after_dedupe
FROM numbered
WHERE rn = 1;


/* P13. Weekend vs weekday share of revenue */
/*  [فارسی] سؤال: سهم فروش آخر هفته در برابر روزهای کاری
    الگو: CASE داخل GROUP BY و ستون is_weekend جدول تاریخ.  */
SELECT
    CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    SUM(f.revenue) AS revenue,
    CAST(100.0 * SUM(f.revenue) / SUM(SUM(f.revenue)) OVER () AS DECIMAL(5,1)) AS share_pct
FROM analytics.FactSales AS f
JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
GROUP BY CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END;


/* P14. Products that were sold but never returned (anti-join) */
/*  [فارسی] سؤال: کالاهایی که هیچ‌وقت مرجوع نشدند
    الگو: LEFT JOIN … WHERE r.key IS NULL؛ روش دوم anti-join.  */
SELECT COUNT(DISTINCT f.product_key) AS products_never_returned
FROM analytics.FactSales   AS f
LEFT JOIN analytics.FactReturns AS r ON r.product_key = f.product_key
WHERE r.product_key IS NULL;


/* P15. Average days between purchase days for each customer */
/*  [فارسی] سؤال: میانگین فاصلهٔ خریدهای هر مشتری
    الگو: LAG روی تاریخ + DATEDIFF(DAY, …).  */
WITH customer_days AS (
    SELECT DISTINCT f.customer_key, d.[date]
    FROM analytics.FactSales AS f
    JOIN analytics.DimDate   AS d ON d.date_key = f.transaction_date_key
),
gaps AS (
    SELECT
        customer_key,
        DATEDIFF(DAY, LAG([date]) OVER (PARTITION BY customer_key ORDER BY [date]), [date]) AS days_since_prev
    FROM customer_days
)
SELECT TOP 10
    customer_key,
    AVG(CAST(days_since_prev AS DECIMAL(10,2))) AS avg_days_between,
    COUNT(*) + 1 AS purchase_days
FROM gaps
WHERE days_since_prev IS NOT NULL
GROUP BY customer_key
HAVING COUNT(*) >= 5
ORDER BY avg_days_between;


/* P16. Revenue per customer by income band and membership card */
/*  [فارسی] سؤال: خرید هر مشتری بر اساس درآمد و سطح عضویت
    الگو: گروه‌بندی دوبعدی + COUNT(DISTINCT).  */
SELECT
    c.yearly_income,
    c.member_card,
    COUNT(DISTINCT f.customer_key) AS customers,
    CAST(SUM(f.revenue) / COUNT(DISTINCT f.customer_key) AS DECIMAL(10,2)) AS revenue_per_customer
FROM analytics.FactSales   AS f
JOIN analytics.DimCustomer AS c ON c.customer_key = f.customer_key
GROUP BY c.yearly_income, c.member_card
ORDER BY c.yearly_income, revenue_per_customer DESC;
