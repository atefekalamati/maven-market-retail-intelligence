# KPI Framework and Baseline

## Scope

This stage defines the measures that will be used in Power BI. The framework keeps executive indicators separate from operational diagnostics and avoids metrics that the source data cannot support.

The model contains sales lines rather than customer orders. For that reason, `Total Orders` and `Average Order Value` are not included. The available profit measure is gross product profit, not net profit.

## Recommended executive scorecard

The first dashboard page should lead with five measures:

1. **Total Revenue** — overall business scale.
2. **Gross Product Profit** — value remaining after product cost.
3. **Gross Margin %** — unit-economics guardrail.
4. **Reported Revenue Growth %** — total network growth.
5. **Same-Store Revenue Growth %** — organic growth for the 13 comparable stores.

Quantity Sold, Active Customers and Return Quantity Rate should appear as secondary indicators. Reported growth and same-store growth should always be displayed together.

## Baseline values

| KPI | Overall | 1997 | 1998 |
|---|---:|---:|---:|
| Total Revenue | $1,764,546.44 | $565,238.13 | $1,199,308.31 |
| Gross Product Profit | $1,052,818.78 | $337,125.48 | $715,693.30 |
| Gross Margin | 59.67% | 59.64% | 59.68% |
| Reported Revenue Growth |  |  | 112.18% |
| Same-Store Revenue Growth |  |  | 8.40% |
| Quantity Sold | 833,489 | 266,773 | 566,716 |
| Active Customers | 8,842 | 5,581 | 8,060 |
| Return Quantity Rate | 0.99% | 0.99% | 1.00% |
| Revenue per Active Customer | $199.56 | $101.28 | $148.80 |
| Repeat Customer Rate | 86.15% | 73.64% | 75.36% |
| Revenue per Square Foot | $2.53 | $1.56 | $1.72 |
| Top 10% Customer Contribution | 39.89% | 36.25% | 43.12% |

## Key interpretation

The 1998 reported revenue increase was **112.18%**, while same-store revenue increased by **8.40%**. The difference is explained by the active store count increasing from **13** to **24**.

Gross margin stayed close to **59.67%**. The network expanded without a material change in product-level margin.

The top 10% of active customers generated **39.89%** of revenue. This is large enough to support a customer-concentration view, but the business is not dependent on only a handful of customers.

## KPI groups

### Executive KPIs

- Total Revenue
- Gross Product Profit
- Gross Margin %
- Reported Revenue Growth %
- Same-Store Revenue Growth %
- Quantity Sold
- Active Customers
- Return Quantity Rate %

### Operational KPIs

- Total Product Cost
- Sales Lines
- Revenue per Active Customer
- Repeat Customer Rate %
- Revenue per Active Store
- Revenue per Square Foot
- Gross Profit per Square Foot
- Average Revenue per Sales Line
- Top 10% Customer Revenue Contribution %
- Top Product Revenue Contribution %

The complete definitions, formulas, required fields, display guidance and limitations are stored in `reports/kpi_dictionary.csv`.

## Target policy

No target values are included at this stage. The source contains no budget, sales plan, store target or management threshold. Creating targets from historical values alone would produce arbitrary red or green status labels.

The dashboard can show current values and historical comparisons first. Targets should be added only after a business owner provides an approved plan or threshold.

## Usage limits

- `Sales Lines` must not be renamed `Total Orders`.
- `Average Revenue per Sales Line` must not be renamed `Average Order Value`.
- `Gross Product Profit` must not be labelled `Net Profit`.
- `Return Quantity Rate %` can be analysed by date, product and store, but not by customer.
- `Repeat Customer Rate %` depends on the selected time window and should be reviewed at month, quarter or year level.
