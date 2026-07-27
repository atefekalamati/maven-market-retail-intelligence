# Data Cleaning Report

## Scope

This stage applies the cleaning rules defined during the data audit. The raw Maven Market files remain unchanged. Cleaned tables are generated in `data/processed/` by `scripts/data_cleaning.py`.

## Outcome

The pipeline completed successfully and preserved every source row:

| Table | Rows before | Rows after | Missing cells before | Missing cells after |
|---|---:|---:|---:|---:|
| Calendar | 730 | 730 | 0 | 0 |
| Customers | 10,281 | 10,281 | 1 | 0 |
| Products | 1,560 | 1,560 | 1,695 | 0 |
| Regions | 109 | 109 | 0 | 0 |
| Returns | 7,087 | 7,087 | 0 | 0 |
| Stores | 24 | 24 | 0 | 0 |
| Transactions | 269,720 | 269,720 | 0 | 0 |

The product blanks were source-encoded false values, not unresolved missing data.

## Changes applied

### Transactions

The 1997 and 1998 files were appended into one table. Each row now includes:

- `transaction_line_id`
- `source_year`
- `source_row_number`
- `duplicate_candidate`

Eighteen rows are marked as duplicate candidates. They represent nine exact-looking pairs. All rows were retained because the source has no receipt, transaction, or order identifier that would support safe deletion.

### Returns

Each return row now has a surrogate line ID and source row number. Ten rows are marked as duplicate candidates, representing five exact-looking pairs. They were retained for the same reason as the transaction candidates.

### Customers

- Account numbers and postal codes are treated as identifiers.
- Twenty four-digit postal codes were left-padded to five characters.
- One missing surname is displayed as `Unknown` and preserved through `last_name_missing = True`.
- Marital status and gender codes were decoded to readable labels.
- Home ownership was converted to `is_homeowner` with boolean values.

### Products

- Product SKU is treated as an identifier.
- Blank/1 source flags were converted to `is_recyclable` and `is_low_fat` booleans.

### Dates and text

Date fields were parsed with strict conversion and exported in ISO format. Text fields were trimmed without changing valid internal spacing.

## Validation result

The cleaning pipeline passed all required checks:

- row counts preserved;
- generated line IDs unique;
- dimension keys unique;
- no foreign-key orphans;
- no missing cells in processed tables;
- no invalid sales or return quantities;
- no stock date later than transaction date;
- no product price less than or equal to cost;
- postal codes standardized to five characters;
- identifier and boolean types correct in the in-memory pipeline.

The detailed validation output is stored in `cleaning_validation.json`.

## Processed outputs

| File | Rows |
|---|---:|
| `calendar_clean.csv` | 730 |
| `customers_clean.csv` | 10,281 |
| `products_clean.csv` | 1,560 |
| `regions_clean.csv` | 109 |
| `returns_clean.csv` | 7,087 |
| `stores_clean.csv` | 24 |
| `transactions_clean.csv` | 269,720 |

## CSV type note

CSV files do not carry a data-type schema. Account number, postal code, SKU, phone number, and line ID fields must therefore be assigned the Text type when imported into Power BI or SQL Server. The intended pandas schema is recorded in `processed_schema.json`.

## Reproducibility

Run from the repository root:

```powershell
python scripts/data_cleaning.py
```

The notebook `notebooks/04_data_cleaning.ipynb` uses the same pipeline and was executed successfully from top to bottom.
