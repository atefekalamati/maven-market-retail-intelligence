# Power BI Build Guide

## 1. Load the model

Load the CSV files produced in `data/model`:

- dim_date.csv
- dim_customer.csv
- dim_product.csv
- dim_store.csv
- fact_sales.csv
- fact_returns.csv

Set dimension keys to whole numbers, dates to Date, monetary fields to fixed decimal numbers and Boolean fields to True/False.

## 2. Confirm relationships

Create these single-direction, one-to-many relationships:

- DimDate[date_key] → FactSales[transaction_date_key] — active
- DimDate[date_key] → FactSales[stock_date_key] — inactive
- DimDate[date_key] → FactReturns[return_date_key] — active
- DimCustomer[customer_key] → FactSales[customer_key] — active
- DimProduct[product_key] → FactSales[product_key] — active
- DimProduct[product_key] → FactReturns[product_key] — active
- DimStore[store_key] → FactSales[store_key] — active
- DimStore[store_key] → FactReturns[store_key] — active

Do not enable bidirectional filtering.

## 3. Date table

Mark `DimDate` as the date table using `DimDate[date]`. Sort:

- month_short_name by month_number
- year_month by year_month_sort
- quarter by quarter_number

## 4. Measures table

Create an empty table named `_Measures` and store all report measures there. Add display folders:

- 01 Base
- 02 Time Intelligence
- 03 Customer
- 04 Product
- 05 Store
- 06 Returns
- 07 Display

## 5. Page construction

Build pages in this order:

1. Executive Overview
2. Sales Performance
3. Product & Profitability
4. Customer Analysis
5. Store & Geographic Performance
6. Returns & Detailed Analysis

The wireframes are design references, not pixel-perfect screenshots of the final report. Keep the hierarchy and relative sizes, then adjust labels based on the final Power BI rendering.

## 6. Tooltips

Create two tooltip pages:

### Product tooltip

- Product name and brand
- Revenue
- Gross Product Profit
- Gross Margin %
- Quantity Sold
- Returned Quantity
- Return Quantity Rate %

### Store tooltip

- Store name, type, city and country
- Revenue
- Gross Product Profit
- Gross Margin %
- Revenue per Square Foot
- Return Quantity Rate %

## 7. Drill-through

Use the Returns & Detailed Analysis page as a drill-through target for:

- store_key
- product_key

Keep all filters enabled so the originating context is retained.

## 8. Formatting

- Currency cards: `$0.00M` or `$0.0K` based on scale.
- Percentages: one decimal place.
- Quantities: whole numbers with thousand separators.
- Long product names: use horizontal bars and tooltips rather than small axis text.
- Use dark red only for return-risk emphasis; it does not automatically mean a target has been missed.

## 9. Validation

Before publishing, compare the unfiltered report with `reports/kpi_baseline_snapshot.csv`. Check that filtering by year, country, region, store, product and membership tier produces reasonable totals without duplicate expansion.
