# Processed Data

The files in this folder are generated locally by:

```powershell
python scripts/data_cleaning.py
```

Expected outputs:

- `calendar_clean.csv`
- `customers_clean.csv`
- `products_clean.csv`
- `regions_clean.csv`
- `returns_clean.csv`
- `stores_clean.csv`
- `transactions_clean.csv`

The CSV files are excluded from Git because they can be reproduced from the raw Kaggle files. This README remains in the repository to document the pipeline.

## Import types for Power BI

Set these columns to **Text** after importing CSV files:

- `customer_acct_num`
- `customer_postal_code`
- `product_sku`
- `store_phone`
- `transaction_line_id`
- `return_line_id`

Set all date columns to **Date** and the `is_*`, `last_name_missing`, and `duplicate_candidate` columns to **True/False**.

The complete intended schema is stored in `reports/processed_schema.json`.
