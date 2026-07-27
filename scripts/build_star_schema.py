from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "data" / "model"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_processed_tables() -> Dict[str, pd.DataFrame]:
    """Load the cleaned tables with identifier and date types kept explicit."""
    tables = {
        "calendar": pd.read_csv(PROCESSED_DIR / "calendar_clean.csv", parse_dates=["date"]),
        "customers": pd.read_csv(
            PROCESSED_DIR / "customers_clean.csv",
            dtype={"customer_acct_num": "string", "customer_postal_code": "string"},
            parse_dates=["birthdate", "acct_open_date"],
        ),
        "products": pd.read_csv(
            PROCESSED_DIR / "products_clean.csv",
            dtype={"product_sku": "string"},
        ),
        "regions": pd.read_csv(PROCESSED_DIR / "regions_clean.csv"),
        "returns": pd.read_csv(
            PROCESSED_DIR / "returns_clean.csv",
            dtype={"return_line_id": "string"},
            parse_dates=["return_date"],
        ),
        "stores": pd.read_csv(
            PROCESSED_DIR / "stores_clean.csv",
            dtype={"store_phone": "string"},
            parse_dates=["first_opened_date", "last_remodel_date"],
        ),
        "transactions": pd.read_csv(
            PROCESSED_DIR / "transactions_clean.csv",
            dtype={"transaction_line_id": "string"},
            parse_dates=["transaction_date", "stock_date"],
        ),
    }
    return tables


def build_dim_date(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    start_date = min(
        tables["calendar"]["date"].min(),
        tables["transactions"]["transaction_date"].min(),
        tables["transactions"]["stock_date"].min(),
        tables["returns"]["return_date"].min(),
    )
    end_date = max(
        tables["calendar"]["date"].max(),
        tables["transactions"]["transaction_date"].max(),
        tables["transactions"]["stock_date"].max(),
        tables["returns"]["return_date"].max(),
    )

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dim_date = pd.DataFrame({"date": dates})
    dim_date.insert(0, "date_key", dim_date["date"].dt.strftime("%Y%m%d").astype("int32"))
    dim_date["year"] = dim_date["date"].dt.year.astype("int16")
    dim_date["quarter_number"] = dim_date["date"].dt.quarter.astype("int8")
    dim_date["quarter"] = "Q" + dim_date["quarter_number"].astype(str)
    dim_date["month_number"] = dim_date["date"].dt.month.astype("int8")
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["month_short_name"] = dim_date["date"].dt.strftime("%b")
    dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["year_month_sort"] = dim_date["date"].dt.strftime("%Y%m").astype("int32")
    dim_date["iso_week_number"] = dim_date["date"].dt.isocalendar().week.astype("int16")
    dim_date["day_of_month"] = dim_date["date"].dt.day.astype("int8")
    dim_date["day_name"] = dim_date["date"].dt.day_name()
    dim_date["day_of_week_number"] = (dim_date["date"].dt.dayofweek + 1).astype("int8")
    dim_date["is_weekend"] = dim_date["day_of_week_number"].isin([6, 7])
    return dim_date


def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    dim_customer = customers.sort_values("customer_id").reset_index(drop=True).copy()
    dim_customer.insert(0, "customer_key", np.arange(1, len(dim_customer) + 1, dtype=np.int32))
    dim_customer["customer_full_name"] = (
        dim_customer["first_name"].str.strip() + " " + dim_customer["last_name"].str.strip()
    )
    dim_customer["birth_year"] = dim_customer["birthdate"].dt.year.astype("int16")
    dim_customer["account_open_year"] = dim_customer["acct_open_date"].dt.year.astype("int16")

    columns = [
        "customer_key",
        "customer_id",
        "customer_acct_num",
        "customer_full_name",
        "first_name",
        "last_name",
        "last_name_missing",
        "customer_city",
        "customer_state_province",
        "customer_postal_code",
        "customer_country",
        "birthdate",
        "birth_year",
        "marital_status",
        "yearly_income",
        "gender",
        "total_children",
        "num_children_at_home",
        "education",
        "acct_open_date",
        "account_open_year",
        "member_card",
        "occupation",
        "is_homeowner",
    ]
    return dim_customer[columns]


def build_dim_product(products: pd.DataFrame) -> pd.DataFrame:
    dim_product = products.sort_values("product_id").reset_index(drop=True).copy()
    dim_product.insert(0, "product_key", np.arange(1, len(dim_product) + 1, dtype=np.int32))
    dim_product["unit_gross_profit"] = (
        dim_product["product_retail_price"] - dim_product["product_cost"]
    ).round(2)
    dim_product["unit_margin_pct"] = (
        dim_product["unit_gross_profit"] / dim_product["product_retail_price"] * 100
    ).round(2)
    dim_product["unit_markup_pct"] = (
        dim_product["unit_gross_profit"] / dim_product["product_cost"] * 100
    ).round(2)

    columns = [
        "product_key",
        "product_id",
        "product_brand",
        "product_name",
        "product_sku",
        "product_retail_price",
        "product_cost",
        "unit_gross_profit",
        "unit_margin_pct",
        "unit_markup_pct",
        "product_weight",
        "is_recyclable",
        "is_low_fat",
    ]
    return dim_product[columns]


def build_dim_store(
    stores: pd.DataFrame,
    regions: pd.DataFrame,
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    dim_store = stores.merge(regions, on="region_id", how="left", validate="many_to_one")
    dim_store = dim_store.sort_values("store_id").reset_index(drop=True)
    dim_store.insert(0, "store_key", np.arange(1, len(dim_store) + 1, dtype=np.int32))

    store_year_activity = transactions.groupby(["store_id", "source_year"]).size().unstack(fill_value=0)
    comparable_store_ids = store_year_activity[
        (store_year_activity.get(1997, 0) > 0) & (store_year_activity.get(1998, 0) > 0)
    ].index

    dim_store["is_same_store_comparable"] = dim_store["store_id"].isin(comparable_store_ids)
    dim_store["non_grocery_sqft"] = dim_store["total_sqft"] - dim_store["grocery_sqft"]
    dim_store["grocery_share_pct"] = (
        dim_store["grocery_sqft"] / dim_store["total_sqft"] * 100
    ).round(2)

    columns = [
        "store_key",
        "store_id",
        "store_name",
        "store_type",
        "store_city",
        "store_state",
        "store_country",
        "first_opened_date",
        "last_remodel_date",
        "total_sqft",
        "grocery_sqft",
        "non_grocery_sqft",
        "grocery_share_pct",
        "region_id",
        "sales_district",
        "sales_region",
        "is_same_store_comparable",
    ]
    return dim_store[columns]


def build_fact_sales(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_store: pd.DataFrame,
) -> pd.DataFrame:
    product_key_map = dim_product.set_index("product_id")["product_key"]
    customer_key_map = dim_customer.set_index("customer_id")["customer_key"]
    store_key_map = dim_store.set_index("store_id")["store_key"]

    fact_sales = transactions.copy()
    fact_sales.insert(0, "sales_line_key", np.arange(1, len(fact_sales) + 1, dtype=np.int64))
    fact_sales["transaction_date_key"] = fact_sales["transaction_date"].dt.strftime("%Y%m%d").astype("int32")
    fact_sales["stock_date_key"] = fact_sales["stock_date"].dt.strftime("%Y%m%d").astype("int32")
    fact_sales["product_key"] = fact_sales["product_id"].map(product_key_map)
    fact_sales["customer_key"] = fact_sales["customer_id"].map(customer_key_map)
    fact_sales["store_key"] = fact_sales["store_id"].map(store_key_map)

    product_prices = products[["product_id", "product_retail_price", "product_cost"]]
    fact_sales = fact_sales.merge(product_prices, on="product_id", how="left", validate="many_to_one")
    fact_sales["quantity_sold"] = fact_sales["quantity"].astype("int16")
    fact_sales["unit_retail_price"] = fact_sales["product_retail_price"].round(2)
    fact_sales["unit_product_cost"] = fact_sales["product_cost"].round(2)
    fact_sales["revenue"] = (fact_sales["quantity_sold"] * fact_sales["unit_retail_price"]).round(2)
    fact_sales["product_cost_amount"] = (
        fact_sales["quantity_sold"] * fact_sales["unit_product_cost"]
    ).round(2)
    fact_sales["gross_product_profit"] = (
        fact_sales["revenue"] - fact_sales["product_cost_amount"]
    ).round(2)

    columns = [
        "sales_line_key",
        "transaction_line_id",
        "transaction_date_key",
        "stock_date_key",
        "product_key",
        "customer_key",
        "store_key",
        "quantity_sold",
        "unit_retail_price",
        "unit_product_cost",
        "revenue",
        "product_cost_amount",
        "gross_product_profit",
        "source_year",
        "source_row_number",
        "duplicate_candidate",
    ]
    return fact_sales[columns]


def build_fact_returns(
    returns: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_store: pd.DataFrame,
) -> pd.DataFrame:
    product_key_map = dim_product.set_index("product_id")["product_key"]
    store_key_map = dim_store.set_index("store_id")["store_key"]

    fact_returns = returns.copy()
    fact_returns.insert(0, "return_line_key", np.arange(1, len(fact_returns) + 1, dtype=np.int64))
    fact_returns["return_date_key"] = fact_returns["return_date"].dt.strftime("%Y%m%d").astype("int32")
    fact_returns["product_key"] = fact_returns["product_id"].map(product_key_map)
    fact_returns["store_key"] = fact_returns["store_id"].map(store_key_map)
    fact_returns["return_quantity"] = fact_returns["quantity"].astype("int16")

    columns = [
        "return_line_key",
        "return_line_id",
        "return_date_key",
        "product_key",
        "store_key",
        "return_quantity",
        "source_row_number",
        "duplicate_candidate",
    ]
    return fact_returns[columns]


def build_model_tables(tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    dim_date = build_dim_date(tables)
    dim_customer = build_dim_customer(tables["customers"])
    dim_product = build_dim_product(tables["products"])
    dim_store = build_dim_store(tables["stores"], tables["regions"], tables["transactions"])
    fact_sales = build_fact_sales(
        tables["transactions"],
        tables["products"],
        dim_customer,
        dim_product,
        dim_store,
    )
    fact_returns = build_fact_returns(tables["returns"], dim_product, dim_store)

    return {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_store": dim_store,
        "fact_sales": fact_sales,
        "fact_returns": fact_returns,
    }


def validate_model(
    source_tables: Dict[str, pd.DataFrame],
    model_tables: Dict[str, pd.DataFrame],
) -> dict:
    dim_date = model_tables["dim_date"]
    dim_customer = model_tables["dim_customer"]
    dim_product = model_tables["dim_product"]
    dim_store = model_tables["dim_store"]
    fact_sales = model_tables["fact_sales"]
    fact_returns = model_tables["fact_returns"]

    checks = {
        "dim_date_key_unique": bool(dim_date["date_key"].is_unique),
        "dim_customer_key_unique": bool(dim_customer["customer_key"].is_unique),
        "dim_product_key_unique": bool(dim_product["product_key"].is_unique),
        "dim_store_key_unique": bool(dim_store["store_key"].is_unique),
        "fact_sales_key_unique": bool(fact_sales["sales_line_key"].is_unique),
        "fact_returns_key_unique": bool(fact_returns["return_line_key"].is_unique),
        "sales_row_count_preserved": len(fact_sales) == len(source_tables["transactions"]),
        "return_row_count_preserved": len(fact_returns) == len(source_tables["returns"]),
        "sales_foreign_keys_complete": not fact_sales[
            ["transaction_date_key", "stock_date_key", "product_key", "customer_key", "store_key"]
        ].isna().any().any(),
        "return_foreign_keys_complete": not fact_returns[
            ["return_date_key", "product_key", "store_key"]
        ].isna().any().any(),
        "sales_dates_covered": set(fact_sales["transaction_date_key"]).issubset(set(dim_date["date_key"])),
        "stock_dates_covered": set(fact_sales["stock_date_key"]).issubset(set(dim_date["date_key"])),
        "return_dates_covered": set(fact_returns["return_date_key"]).issubset(set(dim_date["date_key"])),
        "sales_quantity_reconciled": int(fact_sales["quantity_sold"].sum())
        == int(source_tables["transactions"]["quantity"].sum()),
        "return_quantity_reconciled": int(fact_returns["return_quantity"].sum())
        == int(source_tables["returns"]["quantity"].sum()),
        "sales_amounts_non_negative": bool(
            (fact_sales[["revenue", "product_cost_amount", "gross_product_profit"]].min() >= 0).all()
        ),
        "store_region_attributes_complete": not dim_store[
            ["sales_district", "sales_region"]
        ].isna().any().any(),
        "same_store_count_is_13": int(dim_store["is_same_store_comparable"].sum()) == 13,
    }

    failed_checks = [name for name, passed in checks.items() if not passed]
    summary = {
        "status": "passed" if not failed_checks else "failed",
        "failed_checks": failed_checks,
        "checks": checks,
        "table_rows": {name: int(len(df)) for name, df in model_tables.items()},
        "reconciliation": {
            "quantity_sold": int(fact_sales["quantity_sold"].sum()),
            "return_quantity": int(fact_returns["return_quantity"].sum()),
            "revenue": round(float(fact_sales["revenue"].sum()), 2),
            "product_cost_amount": round(float(fact_sales["product_cost_amount"].sum()), 2),
            "gross_product_profit": round(float(fact_sales["gross_product_profit"].sum()), 2),
            "gross_profit_margin_pct": round(
                float(fact_sales["gross_product_profit"].sum() / fact_sales["revenue"].sum() * 100),
                2,
            ),
            "same_store_comparable_stores": int(dim_store["is_same_store_comparable"].sum()),
        },
    }
    return summary


def export_model(model_tables: Dict[str, pd.DataFrame], validation: dict) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for name, table in model_tables.items():
        output_path = MODEL_DIR / f"{name}.csv"
        date_columns = [column for column in table.columns if pd.api.types.is_datetime64_any_dtype(table[column])]
        table.to_csv(output_path, index=False, date_format="%Y-%m-%d")

    table_metadata = [
        {
            "table": "dim_date",
            "grain": "One row per calendar date",
            "primary_key": "date_key",
            "rows": len(model_tables["dim_date"]),
            "columns": len(model_tables["dim_date"].columns),
        },
        {
            "table": "dim_customer",
            "grain": "One row per customer",
            "primary_key": "customer_key",
            "rows": len(model_tables["dim_customer"]),
            "columns": len(model_tables["dim_customer"].columns),
        },
        {
            "table": "dim_product",
            "grain": "One row per product",
            "primary_key": "product_key",
            "rows": len(model_tables["dim_product"]),
            "columns": len(model_tables["dim_product"].columns),
        },
        {
            "table": "dim_store",
            "grain": "One row per store, including region attributes",
            "primary_key": "store_key",
            "rows": len(model_tables["dim_store"]),
            "columns": len(model_tables["dim_store"].columns),
        },
        {
            "table": "fact_sales",
            "grain": "One cleaned source transaction line",
            "primary_key": "sales_line_key",
            "rows": len(model_tables["fact_sales"]),
            "columns": len(model_tables["fact_sales"].columns),
        },
        {
            "table": "fact_returns",
            "grain": "One cleaned source return line",
            "primary_key": "return_line_key",
            "rows": len(model_tables["fact_returns"]),
            "columns": len(model_tables["fact_returns"].columns),
        },
    ]
    pd.DataFrame(table_metadata).to_csv(REPORTS_DIR / "model_table_profile.csv", index=False)

    relationships = [
        {
            "from_table": "dim_date",
            "from_column": "date_key",
            "to_table": "fact_sales",
            "to_column": "transaction_date_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_date",
            "from_column": "date_key",
            "to_table": "fact_sales",
            "to_column": "stock_date_key",
            "cardinality": "1:*",
            "active_in_power_bi": False,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_date",
            "from_column": "date_key",
            "to_table": "fact_returns",
            "to_column": "return_date_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_product",
            "from_column": "product_key",
            "to_table": "fact_sales",
            "to_column": "product_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_product",
            "from_column": "product_key",
            "to_table": "fact_returns",
            "to_column": "product_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_customer",
            "from_column": "customer_key",
            "to_table": "fact_sales",
            "to_column": "customer_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_store",
            "from_column": "store_key",
            "to_table": "fact_sales",
            "to_column": "store_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
        {
            "from_table": "dim_store",
            "from_column": "store_key",
            "to_table": "fact_returns",
            "to_column": "store_key",
            "cardinality": "1:*",
            "active_in_power_bi": True,
            "filter_direction": "Single",
        },
    ]
    pd.DataFrame(relationships).to_csv(REPORTS_DIR / "model_relationships.csv", index=False)

    with open(REPORTS_DIR / "model_validation.json", "w", encoding="utf-8") as file:
        json.dump(validation, file, ensure_ascii=False, indent=2)


def main() -> None:
    missing_inputs = [
        filename
        for filename in [
            "calendar_clean.csv",
            "customers_clean.csv",
            "products_clean.csv",
            "regions_clean.csv",
            "returns_clean.csv",
            "stores_clean.csv",
            "transactions_clean.csv",
        ]
        if not (PROCESSED_DIR / filename).exists()
    ]
    if missing_inputs:
        raise FileNotFoundError(
            "Missing processed input files. Run scripts/data_cleaning.py first: "
            + ", ".join(missing_inputs)
        )

    source_tables = load_processed_tables()
    model_tables = build_model_tables(source_tables)
    validation = validate_model(source_tables, model_tables)
    export_model(model_tables, validation)

    if validation["status"] != "passed":
        raise ValueError(f"Model validation failed: {validation['failed_checks']}")

    print("Star schema build completed successfully.")
    print("Validation status: passed")
    print(f"FactSales rows: {len(model_tables['fact_sales']):,}")
    print(f"FactReturns rows: {len(model_tables['fact_returns']):,}")
    print(f"Revenue: ${validation['reconciliation']['revenue']:,.2f}")
    print(f"Gross product profit: ${validation['reconciliation']['gross_product_profit']:,.2f}")


if __name__ == "__main__":
    main()
