# Stage 7 — KPI Design

## Goal

This stage turns the validated model and EDA findings into a consistent measure set for Power BI. The focus is not to create as many measures as possible. Each KPI must support a management decision, have a clear denominator and remain valid under dashboard filters.

## Input tables

- `FactSales`
- `FactReturns`
- `DimDate`
- `DimCustomer`
- `DimProduct`
- `DimStore`

## Main design decisions

### Reported growth and organic growth are separate

The store base changed between 1997 and 1998. Total revenue growth includes new stores, while same-store growth uses only the 13 stores with sales in both years. Both measures are required on the executive page.

### Profit terminology stays precise

The model supports gross product profit because product cost is available. It does not support net profit, operating profit or store contribution after labour and rent.

### Sales lines are not orders

The source does not include an order identifier. The number of rows can be measured as `Sales Lines`, but it cannot be presented as order count. Average Revenue per Sales Line is included as an operational measure and is not an order-value KPI.

### Return rate is a proxy

Returns share date, product and store dimensions with sales, but cannot be matched to the original sale or customer. Return Quantity Rate is suitable for product and store monitoring, not customer analysis.

### Targets are deferred

The dataset has no plan, budget or approved threshold. Stage 7 establishes baselines and measure definitions only. Target measures should be added after a business owner supplies the required values.

## Files created

- `notebooks/07_kpi_design.ipynb`
- `scripts/calculate_kpis.py`
- `dax/07_kpi_measures.dax`
- `reports/kpi_framework.md`
- `reports/kpi_dictionary.md`
- `reports/kpi_dictionary.csv`
- `reports/kpi_baseline_snapshot.csv`
- `reports/kpi_validation.json`

## How to run

From the project root:

```powershell
python scripts/calculate_kpis.py
```

The script reads `data/model` and rebuilds the KPI dictionary, baseline snapshot and validation file.

## Validation

Stage 7 is complete when `reports/kpi_validation.json` has a status of `passed`.
