# Maven Market Retail Intelligence

An end-to-end retail analytics portfolio project covering sales, gross product profit, customer value, store performance, product performance, and returns.

## Progress

- [x] Business scenario and project scope
- [x] Business questions
- [x] Data audit
- [x] Data cleaning
- [x] Data modeling
- [x] Exploratory data analysis
- [x] KPI design
- [x] Power BI dashboard
- [ ] Final insights and recommendations

## Project question

Maven Market stores its sales, customer, product, store, region, and return data in separate CSV files. This project turns those files into a reproducible analytical model and answers practical questions such as:

- Did sales growth also improve gross product profit?
- How much of the 1998 growth came from additional store coverage?
- Which stores and regions are growing or declining?
- Which products sell well but generate weaker margins?
- Which customer groups contribute the most value?
- Where are return rates unusually high?

## Documentation

- [Project definition](docs/01_project_definition.md)
- [Business questions](docs/02_business_questions.md)
- [Data audit](docs/03_data_audit.md)
- [Data cleaning](docs/04_data_cleaning.md)
- [Data modeling](docs/05_data_modeling.md)
- [Data quality report](reports/data_quality_report.md)
- [Data cleaning report](reports/data_cleaning_report.md)
- [Data modeling report](reports/data_modeling_report.md)
- [Processed-data dictionary](reports/data_dictionary.md)
- [Model dictionary](reports/data_model_dictionary.md)
- [Exploratory data analysis](docs/06_exploratory_data_analysis.md)
- [KPI design](docs/07_kpi_design.md)
- [Power BI dashboard](docs/08_power_bi_dashboard.md)

## Data audit summary

The eight raw files contain 269,720 transaction rows, 7,087 return rows, 10,281 customers, 1,560 products, and 24 stores.

The main analytical risk is year-over-year comparability. Only 13 stores have transaction activity in 1997, compared with all 24 stores in 1998. The dashboard will therefore separate total-company growth from same-store growth.

No orphan product, customer, store, or region keys were found. Quantities, prices, costs, store areas, and tested date rules passed validation.

## Data cleaning summary

The cleaning pipeline preserves all source rows and writes seven standardized files to `data/processed/`.

Key decisions:

- merge the two transaction files while keeping source lineage;
- add line IDs to transactions and returns;
- flag duplicate candidates rather than removing uncertain records;
- parse dates and standardize their export format;
- keep account numbers, postal codes, SKUs, phone numbers, and line IDs as identifiers;
- convert blank/1 product flags to booleans;
- preserve the one missing surname through a separate missing-value flag.

Run the cleaning stage from the repository root:

```powershell
python scripts/data_cleaning.py
```

## Data model

The Power BI import layer uses a star schema with two facts and four dimensions:

```text
DimDate       ─┬─> FactSales
               └─> FactReturns
DimCustomer   ───> FactSales
DimProduct    ─┬─> FactSales
               └─> FactReturns
DimStore      ─┬─> FactSales
               └─> FactReturns
```

`DimStore` includes the Region attributes to avoid an unnecessary snowflake. Sales and returns remain separate facts because return records cannot be linked to a customer or original transaction.

The model build produced:

| Table | Rows |
|---|---:|
| `dim_date` | 737 |
| `dim_customer` | 10,281 |
| `dim_product` | 1,560 |
| `dim_store` | 24 |
| `fact_sales` | 269,720 |
| `fact_returns` | 7,087 |

The model reconciles to **$1,764,546.44 revenue**, **$711,727.66 product cost**, and **$1,052,818.78 gross product profit**. All model validation checks passed.

Build the model after cleaning:

```powershell
python scripts/build_star_schema.py
```

The same workflow is documented in [`notebooks/05_data_modeling.ipynb`](notebooks/05_data_modeling.ipynb).

## Power BI report

`dashboard/MavenMarket.pbip` is a Power BI project with a TMDL semantic model and a PBIR report. It has six pages: Executive Overview, Sales Performance, Product & Profitability, Customer Analysis, Store & Geographic Performance, and Returns & Detailed Analysis. The project is generated from the Stage 8 design and the DAX files:

```powershell
python scripts/build_power_bi_report.py
```

The model reads `data/model` through the `DataFolder` parameter. After cloning, build the data, open the `.pbip` in Power BI Desktop, set **Transform data → Edit parameters → DataFolder** to your `data/model` path, and refresh.

Unfiltered card values:

| Card | Value |
|---|---:|
| Total revenue | $1.76M |
| Gross product profit | $1.05M |
| Reported growth, latest year (1998) | +112.2% |
| Same-store growth, latest year (1998) | +8.4% |
| Return rate (proxy) | 1.0% |
| Active customers | 8,842 |

All 63 measures were checked on the Power BI Desktop engine against the KPI snapshot and independent pandas calculations (`reports/power_bi_measure_validation.csv`).

One finding needs care: gross margin stayed close to 59.7% because each product has a single retail price and product cost for the whole period. Margin can only move with product mix, so its stability is a property of the data, not evidence of pricing performance.

## Tests

```powershell
python -m pytest
```

The suite checks pipeline reconciliation, the TMDL model (parsed with Power BI Desktop's Tabular Object Model), PBIR schemas and the report layout rules. Tests that need Power BI Desktop are skipped when it is not installed.

## Data

Raw Kaggle files are stored locally in `data/raw/` and are not committed. Their expected filenames are listed in [`data/raw/README.md`](data/raw/README.md).

Cleaned CSV files are generated in `data/processed/`. The Power BI-ready star-schema tables are generated in `data/model/`. Both folders keep only their README files in GitHub because the datasets can be rebuilt from the scripts.

## Current metric definitions

- **Revenue** = Quantity × Retail Price
- **Product Cost** = Quantity × Product Cost
- **Gross Product Profit** = Revenue − Product Cost
- **Gross Profit Margin** = Gross Product Profit ÷ Revenue

The dataset has no order identifier. Transaction rows are therefore not treated as orders, and metrics such as Total Orders and Average Order Value will not be reported.

## Repository structure

```text
maven-market-retail-intelligence/
├── data/
│   ├── raw/
│   │   └── README.md
│   ├── processed/
│   │   └── README.md
│   └── model/
│       └── README.md
├── dashboard/
│   ├── MavenMarket.pbip
│   ├── MavenMarket.SemanticModel/
│   └── MavenMarket.Report/
├── dax/
├── docs/
│   ├── 01_project_definition.md
│   ├── 02_business_questions.md
│   ├── 03_data_audit.md
│   ├── 04_data_cleaning.md
│   └── 05_data_modeling.md
├── images/
├── notebooks/
│   ├── 03_data_audit.ipynb
│   ├── 04_data_cleaning.ipynb
│   └── 05_data_modeling.ipynb
├── reports/
│   ├── data_quality_report.md
│   ├── data_cleaning_report.md
│   ├── data_modeling_report.md
│   ├── data_model_dictionary.md
│   ├── model_relationships.csv
│   ├── model_table_profile.csv
│   └── model_validation.json
├── scripts/
│   ├── data_audit.py
│   ├── data_cleaning.py
│   ├── build_star_schema.py
│   ├── exploratory_data_analysis.py
│   ├── calculate_kpis.py
│   ├── build_power_bi_report.py
│   ├── validate_power_bi_measures.py
│   └── power_bi_desktop_engine.ps1
├── sql/
│   └── 01_create_star_schema.sql
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```
