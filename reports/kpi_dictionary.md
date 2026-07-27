# KPI Dictionary

This file records the business meaning and implementation notes for each dashboard measure.

## Executive KPIs

### Total Revenue

**Persian name:** درآمد کل

**Definition:** Sales value generated from units sold at retail price.

**Formula:** `SUM(FactSales[revenue])`

**Required fields:** `FactSales.revenue`

**Python check:** `sales['revenue'].sum()`

**Power BI measure:** `[Total Revenue]`

**Recommended display:** Primary KPI card; currency

**How to read it:** Shows business scale for the selected period and filters.

**Limitation:** Revenue is not cash collected and does not include tax information.

### Gross Product Profit

**Persian name:** سود ناخالص محصول

**Definition:** Revenue remaining after product cost.

**Formula:** `Total Revenue - Total Product Cost`

**Required fields:** `FactSales.gross_product_profit`

**Python check:** `sales['gross_product_profit'].sum()`

**Power BI measure:** `[Gross Product Profit]`

**Recommended display:** Primary KPI card; currency

**How to read it:** Tracks the value generated before store and corporate operating expenses.

**Limitation:** This is not net profit because payroll, rent, marketing and other operating costs are unavailable.

### Gross Margin %

**Persian name:** حاشیه سود ناخالص

**Definition:** Share of revenue retained after product cost.

**Formula:** `Gross Product Profit / Total Revenue`

**Required fields:** `FactSales.revenue; FactSales.gross_product_profit`

**Python check:** `sales['gross_product_profit'].sum() / sales['revenue'].sum()`

**Power BI measure:** `[Gross Margin %]`

**Recommended display:** Primary KPI card; percentage

**How to read it:** Separates growth in sales volume from improvement in unit economics.

**Limitation:** Stable gross margin does not imply stable net margin.

### Reported Revenue Growth %

**Persian name:** رشد گزارش‌شده درآمد

**Definition:** Change in total revenue versus the previous year using all active stores.

**Formula:** `(Current Revenue - Previous Year Revenue) / Previous Year Revenue`

**Required fields:** `FactSales.revenue; DimDate.date`

**Python check:** `revenue_1998 / revenue_1997 - 1`

**Power BI measure:** `[Revenue Growth %]`

**Recommended display:** KPI card beside same-store growth

**How to read it:** Shows total network growth, including the effect of newly active stores.

**Limitation:** The 1997 and 1998 store bases differ, so this is not an organic-growth measure.

### Same-Store Revenue Growth %

**Persian name:** رشد درآمد فروشگاه‌های همسان

**Definition:** Revenue growth for the 13 stores with sales in both years.

**Formula:** `(Comparable Revenue CY - Comparable Revenue PY) / Comparable Revenue PY`

**Required fields:** `FactSales.revenue; DimDate.date; DimStore.is_same_store_comparable`

**Python check:** `same_store_revenue_1998 / same_store_revenue_1997 - 1`

**Power BI measure:** `[Same-Store Revenue Growth %]`

**Recommended display:** Primary growth card; percentage

**How to read it:** Provides a cleaner view of organic performance than reported growth.

**Limitation:** The comparable-store flag is fixed for this two-year dataset and should be redesigned for longer histories.

### Quantity Sold

**Persian name:** تعداد کالای فروخته‌شده

**Definition:** Total units sold in the selected context.

**Formula:** `SUM(FactSales[quantity_sold])`

**Required fields:** `FactSales.quantity_sold`

**Python check:** `sales['quantity_sold'].sum()`

**Power BI measure:** `[Quantity Sold]`

**Recommended display:** Secondary KPI card or trend

**How to read it:** Helps distinguish volume growth from price and product-mix effects.

**Limitation:** Units from different products are counted equally regardless of value or weight.

### Active Customers

**Persian name:** مشتریان فعال

**Definition:** Distinct customers with at least one sales line in the selected period.

**Formula:** `DISTINCTCOUNT(FactSales[customer_key])`

**Required fields:** `FactSales.customer_key`

**Python check:** `sales['customer_key'].nunique()`

**Power BI measure:** `[Active Customers]`

**Recommended display:** Secondary KPI card

**How to read it:** Shows the size of the purchasing customer base.

**Limitation:** The dataset does not distinguish acquisition source or customer status outside observed purchases.

### Return Quantity Rate %

**Persian name:** نرخ مقداری مرجوعی

**Definition:** Returned units divided by sold units for the same visible product, store and date context.

**Formula:** `Returned Quantity / Quantity Sold`

**Required fields:** `FactReturns.return_quantity; FactSales.quantity_sold; shared dimensions`

**Python check:** `returns['return_quantity'].sum() / sales['quantity_sold'].sum()`

**Power BI measure:** `[Return Quantity Rate %]`

**Recommended display:** Guardrail KPI and alert visual

**How to read it:** Highlights products or stores that may require quality or process review.

**Limitation:** Returns cannot be matched to the original sale or customer; do not use this KPI by customer.

## Operational KPIs

### Total Product Cost

**Persian name:** هزینه کل محصول

**Definition:** Cost of units sold based on product unit cost.

**Formula:** `SUM(FactSales[product_cost_amount])`

**Required fields:** `FactSales.product_cost_amount`

**Python check:** `sales['product_cost_amount'].sum()`

**Power BI measure:** `[Total Product Cost]`

**Recommended display:** Supporting KPI or tooltip

**How to read it:** Explains the cost side of gross product profit.

**Limitation:** Excludes inventory carrying cost and operating expenses.

### Sales Lines

**Persian name:** ردیف‌های فروش

**Definition:** Number of sales records at the product-customer-store-date grain.

**Formula:** `COUNTROWS(FactSales)`

**Required fields:** `FactSales.sales_line_key`

**Python check:** `len(sales)`

**Power BI measure:** `[Sales Lines]`

**Recommended display:** Operational KPI or tooltip

**How to read it:** Measures transaction-line activity, not the number of customer orders.

**Limitation:** There is no order ID, so this must never be labelled Total Orders.

### Revenue per Active Customer

**Persian name:** درآمد به‌ازای مشتری فعال

**Definition:** Average revenue generated per purchasing customer.

**Formula:** `Total Revenue / Active Customers`

**Required fields:** `FactSales.revenue; FactSales.customer_key`

**Python check:** `sales['revenue'].sum() / sales['customer_key'].nunique()`

**Power BI measure:** `[Revenue per Active Customer]`

**Recommended display:** Customer KPI card or membership comparison

**How to read it:** Compares customer value across periods and segments.

**Limitation:** This is period revenue per active customer, not customer lifetime value.

### Repeat Customer Rate %

**Persian name:** نرخ مشتریان تکرارشونده

**Definition:** Share of active customers purchasing on more than one distinct date in the selected period.

**Formula:** `Repeat Customers / Active Customers`

**Required fields:** `FactSales.customer_key; FactSales.transaction_date_key`

**Python check:** `(sales.groupby('customer_key')['transaction_date_key'].nunique() > 1).mean()`

**Power BI measure:** `[Repeat Customer Rate %]`

**Recommended display:** Customer KPI; use at month, quarter or year level

**How to read it:** Indicates whether the active customer base returns within the measured period.

**Limitation:** The value is sensitive to the selected date window and will be zero at a single-day grain.

### Revenue per Active Store

**Persian name:** درآمد به‌ازای فروشگاه فعال

**Definition:** Average revenue across stores with sales in the selected period.

**Formula:** `Total Revenue / Active Stores`

**Required fields:** `FactSales.revenue; FactSales.store_key`

**Python check:** `sales['revenue'].sum() / sales['store_key'].nunique()`

**Power BI measure:** `[Revenue per Active Store]`

**Recommended display:** Store summary KPI

**How to read it:** Normalizes total revenue for changes in the number of active stores.

**Limitation:** Average store performance can hide large differences by format and location.

### Revenue per Square Foot

**Persian name:** درآمد به‌ازای فوت مربع

**Definition:** Revenue divided by total floor area of stores active in the selected period.

**Formula:** `Total Revenue / Active Store Area`

**Required fields:** `FactSales.revenue; DimStore.total_sqft`

**Python check:** `sales['revenue'].sum() / active_store_area`

**Power BI measure:** `[Revenue per Square Foot]`

**Recommended display:** Store efficiency KPI and ranked bar

**How to read it:** Compares how efficiently stores use their physical footprint.

**Limitation:** The available floor-area value is static and does not reflect temporary closures or layout changes within a period.

### Gross Profit per Square Foot

**Persian name:** سود ناخالص به‌ازای فوت مربع

**Definition:** Gross product profit divided by total floor area of active stores.

**Formula:** `Gross Product Profit / Active Store Area`

**Required fields:** `FactSales.gross_product_profit; DimStore.total_sqft`

**Python check:** `sales['gross_product_profit'].sum() / active_store_area`

**Power BI measure:** `[Gross Profit per Square Foot]`

**Recommended display:** Store efficiency KPI or scatter axis

**How to read it:** Balances store productivity with product margin.

**Limitation:** Does not include store operating expenses, so it is not store-level net profit per square foot.

### Average Revenue per Sales Line

**Persian name:** میانگین درآمد هر ردیف فروش

**Definition:** Average revenue per recorded product sales line.

**Formula:** `Total Revenue / Sales Lines`

**Required fields:** `FactSales.revenue; FactSales.sales_line_key`

**Python check:** `sales['revenue'].sum() / len(sales)`

**Power BI measure:** `[Average Revenue per Sales Line]`

**Recommended display:** Tooltip or detailed operational KPI

**How to read it:** Tracks changes in value at the available sales-line grain.

**Limitation:** This is not Average Order Value because the dataset has no order identifier.

### Top 10% Customer Revenue Contribution %

**Persian name:** سهم درآمد ۱۰٪ مشتریان برتر

**Definition:** Share of revenue generated by the highest-revenue 10% of active customers.

**Formula:** `Revenue from top 10% active customers / Total Revenue`

**Required fields:** `FactSales.customer_key; FactSales.revenue`

**Python check:** `top_10_percent_customer_revenue / total_revenue`

**Power BI measure:** `[Top 10% Customer Revenue Contribution %]`

**Recommended display:** Concentration KPI or Pareto view

**How to read it:** Shows how dependent revenue is on the highest-value customer group.

**Limitation:** The customer set changes with filters, so comparisons need the same period and segment definition.

### Top Product Revenue Contribution %

**Persian name:** سهم درآمد محصول برتر

**Definition:** Revenue share generated by the single highest-revenue product.

**Formula:** `Top Product Revenue / Total Revenue`

**Required fields:** `FactSales.product_key; FactSales.revenue`

**Python check:** `sales.groupby('product_key')['revenue'].sum().max() / sales['revenue'].sum()`

**Power BI measure:** `[Top Product Revenue Contribution %]`

**Recommended display:** Product concentration KPI or tooltip

**How to read it:** Identifies whether revenue depends heavily on one product.

**Limitation:** A low share does not prove a healthy assortment; category and brand concentration should also be reviewed.
