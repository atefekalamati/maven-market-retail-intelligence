# Model-ready data

This folder is generated locally by:

```powershell
python scripts/build_star_schema.py
```

Expected files:

- `dim_date.csv`
- `dim_customer.csv`
- `dim_product.csv`
- `dim_store.csv`
- `fact_sales.csv`
- `fact_returns.csv`

These files are used as the Power BI import layer. They are not committed to GitHub because they can be rebuilt from the cleaned data.

## Power BI types to check

Set these fields to **Text** after import:

- `transaction_line_id`
- `return_line_id`
- `customer_acct_num`
- `customer_postal_code`
- `product_sku`

Set surrogate and date keys to **Whole number**, monetary fields to **Fixed decimal number**, and Boolean fields to **True/False**.
