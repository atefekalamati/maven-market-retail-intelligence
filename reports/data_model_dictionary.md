# Data Model Dictionary

This dictionary describes the model-ready tables created by `scripts/build_star_schema.py`.

## `dim_date`

**Grain:** One row per calendar date  
**Primary key:** `date_key`  
**Rows:** 737

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `date_key` | Integer date key in YYYYMMDD format | Whole number | Primary key |
| `date` | Calendar date | Date | Attribute |
| `year` | Calendar year | Whole number | Attribute |
| `quarter_number` | Quarter number from 1 to 4 | Whole number | Sort/attribute |
| `quarter` | Quarter label such as Q1 | Text | Attribute |
| `month_number` | Month number from 1 to 12 | Whole number | Sort column |
| `month_name` | Full month name | Text | Attribute |
| `month_short_name` | Three-letter month name | Text | Attribute |
| `year_month` | Year and month label in YYYY-MM format | Text | Attribute |
| `year_month_sort` | Numeric YYYYMM value used to sort year-month labels | Whole number | Sort column |
| `iso_week_number` | ISO week number | Whole number | Attribute |
| `day_of_month` | Day number within the month | Whole number | Attribute |
| `day_name` | Day-of-week name | Text | Attribute |
| `day_of_week_number` | Monday-based day number from 1 to 7 | Whole number | Sort column |
| `is_weekend` | True for Saturday and Sunday | True/False | Attribute |

## `dim_customer`

**Grain:** One row per customer  
**Primary key:** `customer_key`  
**Rows:** 10,281

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `customer_key` | Surrogate customer key used by the fact table | Whole number | Primary key |
| `customer_id` | Source customer identifier | Whole number | Business key |
| `customer_acct_num` | Customer account number retained as an identifier | Text | Identifier |
| `customer_full_name` | Combined first and last name for display | Text | Attribute |
| `first_name` | Customer first name | Text | Attribute |
| `last_name` | Customer last name; Unknown is used for one missing source value | Text | Attribute |
| `last_name_missing` | Flags the source row with a missing surname | True/False | Quality flag |
| `customer_city` | Customer city | Text | Geography attribute |
| `customer_state_province` | Customer state or province | Text | Geography attribute |
| `customer_postal_code` | Postal code kept as text | Text | Geography attribute |
| `customer_country` | Customer country | Text | Geography attribute |
| `birthdate` | Customer date of birth | Date | Attribute |
| `birth_year` | Year extracted from birthdate | Whole number | Attribute |
| `marital_status` | Decoded marital status | Text | Attribute |
| `yearly_income` | Source income band | Text | Segmentation attribute |
| `gender` | Decoded gender value | Text | Attribute |
| `total_children` | Total number of children | Whole number | Attribute |
| `num_children_at_home` | Number of children living at home | Whole number | Attribute |
| `education` | Education category | Text | Segmentation attribute |
| `acct_open_date` | Date the customer account was opened | Date | Attribute |
| `account_open_year` | Year extracted from account open date | Whole number | Attribute |
| `member_card` | Membership tier | Text | Segmentation attribute |
| `occupation` | Occupation category | Text | Segmentation attribute |
| `is_homeowner` | Home ownership flag | True/False | Attribute |

## `dim_product`

**Grain:** One row per product  
**Primary key:** `product_key`  
**Rows:** 1,560

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `product_key` | Surrogate product key used by both fact tables | Whole number | Primary key |
| `product_id` | Source product identifier | Whole number | Business key |
| `product_brand` | Product brand | Text | Attribute |
| `product_name` | Product name | Text | Attribute |
| `product_sku` | Product SKU kept as text | Text | Identifier |
| `product_retail_price` | Current retail price in the source product table | Fixed decimal number | Attribute |
| `product_cost` | Current unit product cost in the source product table | Fixed decimal number | Attribute |
| `unit_gross_profit` | Retail price minus product cost | Fixed decimal number | Derived attribute |
| `unit_margin_pct` | Unit gross profit divided by retail price | Decimal number | Derived attribute |
| `unit_markup_pct` | Unit gross profit divided by product cost | Decimal number | Derived attribute |
| `product_weight` | Product weight from the source table | Decimal number | Attribute |
| `is_recyclable` | Recyclable product flag | True/False | Attribute |
| `is_low_fat` | Low-fat product flag | True/False | Attribute |

## `dim_store`

**Grain:** One row per store, including region attributes  
**Primary key:** `store_key`  
**Rows:** 24

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `store_key` | Surrogate store key used by both fact tables | Whole number | Primary key |
| `store_id` | Source store identifier | Whole number | Business key |
| `store_name` | Store display name | Text | Attribute |
| `store_type` | Store format | Text | Segmentation attribute |
| `store_city` | Store city | Text | Geography attribute |
| `store_state` | Store state or province | Text | Geography attribute |
| `store_country` | Store country | Text | Geography attribute |
| `first_opened_date` | Store opening date | Date | Attribute |
| `last_remodel_date` | Most recent remodel date in the source | Date | Attribute |
| `total_sqft` | Total store area in square feet | Whole number | Attribute |
| `grocery_sqft` | Grocery area in square feet | Whole number | Attribute |
| `non_grocery_sqft` | Total area minus grocery area | Whole number | Derived attribute |
| `grocery_share_pct` | Grocery area as a percentage of total area | Decimal number | Derived attribute |
| `region_id` | Source region identifier retained for traceability | Whole number | Identifier |
| `sales_district` | Sales district from the region lookup | Text | Geography attribute |
| `sales_region` | Sales region from the region lookup | Text | Geography attribute |
| `is_same_store_comparable` | True for stores with sales in both 1997 and 1998 | True/False | Analysis flag |

## `fact_sales`

**Grain:** One cleaned source transaction line  
**Primary key:** `sales_line_key`  
**Rows:** 269,720

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `sales_line_key` | Surrogate key for the modeled sales line | Whole number | Primary key |
| `transaction_line_id` | Line identifier created during cleaning | Text | Degenerate identifier |
| `transaction_date_key` | Date key for the sales transaction date | Whole number | Foreign key |
| `stock_date_key` | Date key for stock date; use an inactive Power BI relationship | Whole number | Foreign key |
| `product_key` | Surrogate product key | Whole number | Foreign key |
| `customer_key` | Surrogate customer key | Whole number | Foreign key |
| `store_key` | Surrogate store key | Whole number | Foreign key |
| `quantity_sold` | Units sold on the source transaction line | Whole number | Additive measure |
| `unit_retail_price` | Retail price copied to the fact at model build time | Fixed decimal number | Line attribute |
| `unit_product_cost` | Unit product cost copied to the fact at model build time | Fixed decimal number | Line attribute |
| `revenue` | Quantity sold multiplied by unit retail price | Fixed decimal number | Additive measure |
| `product_cost_amount` | Quantity sold multiplied by unit product cost | Fixed decimal number | Additive measure |
| `gross_product_profit` | Revenue minus product cost amount | Fixed decimal number | Additive measure |
| `source_year` | Original transaction file year | Whole number | Lineage attribute |
| `source_row_number` | Original row number within the yearly source file | Whole number | Lineage attribute |
| `duplicate_candidate` | Flags exact-looking source rows retained for review | True/False | Quality flag |

## `fact_returns`

**Grain:** One cleaned source return line  
**Primary key:** `return_line_key`  
**Rows:** 7,087

| Column | Description | Power BI type | Role |
|---|---|---|---|
| `return_line_key` | Surrogate key for the modeled return line | Whole number | Primary key |
| `return_line_id` | Line identifier created during cleaning | Text | Degenerate identifier |
| `return_date_key` | Date key for the return date | Whole number | Foreign key |
| `product_key` | Surrogate product key | Whole number | Foreign key |
| `store_key` | Surrogate store key | Whole number | Foreign key |
| `return_quantity` | Units returned on the source return line | Whole number | Additive measure |
| `source_row_number` | Original row number in the return file | Whole number | Lineage attribute |
| `duplicate_candidate` | Flags exact-looking source rows retained for review | True/False | Quality flag |
