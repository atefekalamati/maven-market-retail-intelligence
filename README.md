# Maven Market Retail Intelligence

A portfolio project focused on retail sales, gross product profit, customer value, store performance, product performance, and returns.

## Progress

- [x] Business scenario and project scope
- [x] Business questions
- [x] Data audit
- [ ] Data cleaning
- [ ] Data modeling
- [ ] Exploratory data analysis
- [ ] KPI design
- [ ] Power BI dashboard
- [ ] Final insights and recommendations

## Project question

Maven Market has sales, customer, product, store, region, and return data stored in separate CSV files. The project combines those files into a reliable analytical model and answers practical management questions such as:

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
- [Data quality report](reports/data_quality_report.md)
- [Data dictionary](reports/data_dictionary.md)

## Data audit summary

The eight raw files contain 269,720 transaction rows, 7,087 return rows, 10,281 customers, 1,560 products, and 24 stores.

Core relationships are valid: no orphan product, customer, store, or region keys were found. Quantities, prices, costs, areas, and tested date rules also passed validation.

The main analytical risk is year-over-year comparability. Only 13 stores have transaction activity in 1997, compared with all 24 stores in 1998. The dashboard will therefore separate total-company growth from same-store growth.

The audit is reproducible through:

```powershell
python scripts/data_audit.py
```

or by running [`notebooks/03_data_audit.ipynb`](notebooks/03_data_audit.ipynb).

## Data

The project uses eight Maven Market CSV files. Raw files are stored locally in `data/raw/` and are not committed to GitHub. The expected filenames are listed in [`data/raw/README.md`](data/raw/README.md).

## Current metric definitions

- **Revenue** = Quantity × Retail Price
- **Product Cost** = Quantity × Product Cost
- **Gross Product Profit** = Revenue − Product Cost
- **Gross Profit Margin** = Gross Product Profit ÷ Revenue

The dataset does not include an order identifier. For that reason, transaction rows are not treated as orders and metrics such as Total Orders and Average Order Value are not reported.

## Repository structure

```text
maven-market-retail-intelligence/
├── data/
│   ├── raw/
│   └── processed/
├── dashboard/
├── docs/
│   ├── 01_project_definition.md
│   ├── 02_business_questions.md
│   └── 03_data_audit.md
├── images/
├── notebooks/
│   └── 03_data_audit.ipynb
├── reports/
│   ├── audit_summary.json
│   ├── column_profile.csv
│   ├── data_dictionary.csv
│   ├── data_dictionary.md
│   ├── data_quality_report.csv
│   ├── data_quality_report.md
│   └── table_profile.csv
├── scripts/
│   └── data_audit.py
├── requirements.txt
├── .gitignore
└── README.md
```
