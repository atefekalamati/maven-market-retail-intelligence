# Data Quality Report

## Scope

This audit covers the eight raw Maven Market CSV files. The raw files were profiled without editing them. The two transaction files were also combined in memory to test cross-year coverage and integrity.

## Dataset summary

| table             |   rows |   columns |   missing_cells |   missing_cell_rate_pct |   exact_duplicate_rows |   exact_duplicate_rate_pct |
|:------------------|-------:|----------:|----------------:|------------------------:|-----------------------:|---------------------------:|
| calendar          |    730 |         1 |               0 |                  0      |                      0 |                     0      |
| customers         |  10281 |        20 |               1 |                  0.0005 |                      0 |                     0      |
| products          |   1560 |         9 |            1695 |                 12.0726 |                      0 |                     0      |
| regions           |    109 |         3 |               0 |                  0      |                      0 |                     0      |
| returns           |   7087 |         4 |               0 |                  0      |                      5 |                     0.0706 |
| stores            |     24 |        13 |               0 |                  0      |                      0 |                     0      |
| transactions_1997 |  86837 |         6 |               0 |                  0      |                      1 |                     0.0012 |
| transactions_1998 | 182883 |         6 |               0 |                  0      |                      8 |                     0.0044 |

## Audit result

The data is suitable for the next stage, but a few rules need to be carried into cleaning and analysis:

- Overall 1997–1998 growth is not a like-for-like comparison because store coverage expands from 13 to 24 stores.
- Transaction and return rows have no source-level unique identifier.
- Exact-looking duplicate rows should be flagged, not removed automatically.
- Blank product flags represent the false state and should be converted explicitly.
- Postal codes and other identifiers need text data types.

## Findings

| severity   | dataset                 | column_or_rule                             | issue                                                                                   | impact                                                                                                                                              | recommended_action                                                                                                      |
|:-----------|:------------------------|:-------------------------------------------|:----------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------|
| High       | returns                 | Missing return and transaction identifiers | Returns cannot be linked to a customer or a specific sales row.                         | Customer-level return analysis and exact return-to-sale matching are not supported.                                                                 | Create a surrogate return row ID and limit return analysis to date, product, store, and aggregate rates.                |
| High       | transactions            | Comparable store coverage by year          | Only 13 stores have transactions in 1997, compared with 24 in 1998.                     | A direct total-company YoY comparison mixes business growth with a change in store coverage.                                                        | Report total growth and same-store growth separately. Use the 13 stores present in both years as the comparable cohort. |
| High       | transactions            | Missing transaction-row identifier         | The fact files do not contain a transaction ID, receipt ID, or order ID.                | Rows cannot be uniquely traced to an order, and exact-looking duplicates cannot be confirmed as errors.                                             | Create a surrogate row ID during cleaning. Do not report Total Orders or Average Order Value.                           |
| Medium     | calendar / transactions | Dates with no transaction rows             | 57 calendar dates have no sales rows: 42 in 1997 and 15 in 1998.                        | The gaps may represent legitimate zero-sales days or missing extracts. Imputing sales would create unsupported values.                              | Keep the complete calendar, show zero activity through the date dimension, and document the source uncertainty.         |
| Medium     | customers               | customer_postal_code data type             | 20 postal codes are four digits because the field was loaded as an integer.             | Leading zeros are lost and postal codes may display incorrectly or join incorrectly to external geography data.                                     | Convert the field to text and left-pad four-digit values to five characters.                                            |
| Medium     | multiple tables         | Raw schema types                           | Date fields are text, and account number, SKU, and postal code are numeric identifiers. | Incorrect data types can break date intelligence, formatting, sorting, and identifier preservation.                                                 | Apply explicit types during cleaning and validate failed casts before exporting processed data.                         |
| Medium     | returns                 | Exact-looking duplicate rows               | 5 rows repeat all available return fields.                                              | The return quantity may be slightly overstated if these are duplicate records, but identical return events are also possible.                       | Flag and review; do not deduplicate automatically.                                                                      |
| Medium     | transactions            | Exact-looking duplicate rows               | 9 rows repeat all available transaction fields.                                         | Removing them without a true transaction ID could undercount legitimate repeated purchases; keeping true duplicates could slightly overstate sales. | Flag the rows but retain them until a source-level uniqueness rule is available.                                        |
| Low        | customers               | last_name completeness                     | One customer record has no last name.                                                   | Customer display labels may be incomplete, but analytical joins and measures are unaffected.                                                        | Keep the source value and use 'Unknown' only in the presentation layer if a full name is required.                      |
| Low        | customers               | Age at account opening                     | 570 customers were under 16 on the recorded account-open date.                          | The records may represent household accounts or synthetic data. Age-at-account-open analysis would be unreliable without context.                   | Retain the dates, document the limitation, and avoid using age at account opening as a management KPI.                  |
| Low        | dimensions              | Dimension members without sales activity   | 1439 customers and 1 product have no transaction rows in the two-year fact data.        | Counting all customer dimension rows would overstate active customers.                                                                              | Keep dimension members, but define Active Customers and Active Products from the transaction fact.                      |
| Low        | products                | recyclable binary encoding                 | 687 blank values coexist with 1 values; the source uses blank as the false state.       | Treating these blanks as unknown would overstate missingness and make the field harder to use.                                                      | Map blank to False and 1 to True, then store as boolean.                                                                |
| Low        | products                | low_fat binary encoding                    | 1008 blank values coexist with 1 values; the source uses blank as the false state.      | Treating these blanks as unknown would overstate missingness and make the field harder to use.                                                      | Map blank to False and 1 to True, then store as boolean.                                                                |

## Referential and business-rule checks

| Check | Failed rows |
|---|---:|
| `transaction_product_orphans` | 0 |
| `transaction_customer_orphans` | 0 |
| `transaction_store_orphans` | 0 |
| `return_product_orphans` | 0 |
| `return_store_orphans` | 0 |
| `store_region_orphans` | 0 |
| `transaction_quantity_nonpositive` | 0 |
| `return_quantity_nonpositive` | 0 |
| `stock_date_after_transaction_date` | 0 |
| `transaction_before_store_open` | 0 |
| `transaction_before_account_open` | 0 |
| `product_price_not_above_cost` | 0 |
| `grocery_sqft_above_total_sqft` | 0 |
| `children_at_home_above_total_children` | 0 |


All foreign-key coverage checks passed. Quantities, prices, costs, store areas, date ordering, and customer-child count rules also passed the tested constraints.

## Decisions for the cleaning stage

1. Keep the raw files unchanged.
2. Append the two transaction files and add a `source_year` column.
3. Add surrogate row identifiers for transactions and returns.
4. Do not automatically remove exact-looking duplicates.
5. Convert date fields to datetime.
6. Convert account numbers, SKUs, and postal codes to text.
7. Convert blank/1 product flags to False/True.
8. Use an active-customer measure based on transaction activity.
9. Build both total-company and same-store year-over-year comparisons.
10. Keep the full calendar and show dates with no sales as zero rather than imputing sales.

## Known analytical limits

- The transaction files do not include an order or receipt identifier.
- Returns cannot be joined to a customer or a specific sales row.
- The dataset supports gross product profit, not accounting net profit.
- The source does not explain whether dates with no transactions are true zero-sales days or missing extracts.
