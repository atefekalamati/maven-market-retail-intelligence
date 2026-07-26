# Maven Market Retail Intelligence

A portfolio project focused on retail sales, gross profit, customer value, store performance, product performance, and returns.

## Progress

- [x] Business scenario and project scope
- [x] Business questions
- [ ] Data audit
- [ ] Data cleaning
- [ ] Data modeling
- [ ] Exploratory data analysis
- [ ] KPI design
- [ ] Power BI dashboard
- [ ] Final insights and recommendations

## Project question

Maven Market has sales, customer, product, store, region, and return data stored in separate CSV files. The goal of this project is to combine those files into a reliable analytical model and answer practical management questions such as:

- Did sales growth also improve gross profit?
- Which stores and regions are growing or declining?
- Which products sell well but generate weak margins?
- Which customer groups contribute the most value?
- Where are return rates unusually high?

## Documentation

- [Project definition](docs/01_project_definition.md)
- [Business questions](docs/02_business_questions.md)

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
│   └── 02_business_questions.md
├── images/
├── notebooks/
├── reports/
├── scripts/
├── .gitignore
└── README.md
```
