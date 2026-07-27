# Stage 6 — Exploratory Data Analysis

## Goal

The purpose of this stage is to answer the business questions defined earlier and identify which comparisons are useful enough to carry into the Power BI dashboard.

The analysis is intentionally focused. A chart is included only when it supports a management question or highlights a limitation that affects interpretation.

## Input tables

The analysis reads the six model tables created in Stage 5:

- `FactSales`
- `FactReturns`
- `DimDate`
- `DimCustomer`
- `DimProduct`
- `DimStore`

Run the cleaning and modeling stages before this notebook if the files in `data/model` are not available locally.

## Questions covered

1. How did revenue, gross product profit and quantity change over time?
2. How much of the 1998 increase was caused by adding stores?
3. Which stores produced the most revenue, and which used their floor area efficiently?
4. Is store size related to sales performance?
5. Which brands and products generated the largest contribution?
6. How concentrated is revenue across customers?
7. How does revenue per customer differ across membership levels?
8. Which stores and products have unusually high return-rate proxies?

## Important definitions

### Reported growth

Growth calculated using all active stores in each year.

### Same-store growth

Growth calculated only for the 13 stores with sales in both 1997 and 1998. This is the more useful measure of organic performance.

### Gross product profit

`Revenue - Product Cost`

This is not net profit because operating expenses are not available.

### Return-rate proxy

`Returned Quantity / Quantity Sold`

The return table does not contain a transaction ID, so this ratio cannot be matched to the original sale. It is used as a directional operational indicator.

## Outputs

The new files from this stage are stored in:

- `notebooks/06_exploratory_data_analysis.ipynb`
- `scripts/exploratory_data_analysis.py`
- `reports/eda_summary.md`
- `reports/*.csv`
- `images/eda/*.png`

## How to run

From the project root:

```powershell
python scripts/exploratory_data_analysis.py
```

Or open and run:

```text
notebooks/06_exploratory_data_analysis.ipynb
```

## Validation

The script reconciles its totals against the validated model and writes the result to:

```text
reports/eda_validation.json
```

The stage is complete only when the validation status is `passed`.
