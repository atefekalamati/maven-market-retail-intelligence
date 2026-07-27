# Data Modeling Report

## Model choice

I used a star schema with two fact tables and four shared dimensions. The model keeps sales and returns separate because their grains differ and the return data cannot be linked to a customer or an original transaction.

The region attributes were flattened into `dim_store`. This avoids an extra snowflake relationship and keeps store filtering straightforward in Power BI.

## Model tables

| Table | Rows | Grain |
|---|---:|---|
| `dim_date` | 737 | One row per calendar date |
| `dim_customer` | 10,281 | One row per customer |
| `dim_product` | 1,560 | One row per product |
| `dim_store` | 24 | One row per store |
| `fact_sales` | 269,720 | One cleaned transaction line |
| `fact_returns` | 7,087 | One cleaned return line |

## Reconciliation

The modeled facts reconcile to the cleaned source tables:

| Check | Result |
|---|---:|
| Quantity sold | 833,489 |
| Return quantity | 8,289 |
| Revenue | $1,764,546.44 |
| Product cost | $711,727.66 |
| Gross product profit | $1,052,818.78 |
| Gross profit margin | 59.67% |

All primary keys are unique, all required foreign keys are populated, and every fact date is covered by `dim_date`.

## Important modeling decisions

- `transaction_date_key` is the active sales date relationship.
- `stock_date_key` uses an inactive relationship to the same date dimension.
- `fact_returns` shares Date, Product, and Store dimensions with sales.
- Customer filters do not apply to returns because the source return table has no customer key.
- `dim_store[is_same_store_comparable]` identifies the 13 stores active in both years.
- Duplicate candidates remain in the facts and can be filtered during sensitivity checks.
- No Order or Sales Channel dimension was created because the source does not contain those business entities.

## Power BI setup

Load the six CSV files from `data/model/`, create the relationships listed in `model_relationships.csv`, and keep all filter directions set to Single. Mark `dim_date[date]` as the date table using `dim_date[date_key]` as its unique key.

The inactive stock-date relationship can be used later with `USERELATIONSHIP` when a stock-date measure is needed.

## Validation

The build completed with all automated checks passing. Full results are stored in `model_validation.json`.
