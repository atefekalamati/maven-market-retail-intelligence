"""Clean and standardize the Maven Market CSV files.

Run from the repository root:
    python scripts/data_cleaning.py

Raw files are never overwritten. Cleaned tables are written to data/processed/.
The script also writes validation and change summaries to reports/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

RAW_FILES = {
    "calendar": "MavenMarket_Calendar.csv",
    "customers": "MavenMarket_Customers.csv",
    "products": "MavenMarket_Products.csv",
    "regions": "MavenMarket_Regions.csv",
    "returns": "MavenMarket_Returns_1997-1998.csv",
    "stores": "MavenMarket_Stores.csv",
    "transactions_1997": "MavenMarket_Transactions_1997.csv",
    "transactions_1998": "MavenMarket_Transactions_1998.csv",
}

OUTPUT_FILES = {
    "calendar": "calendar_clean.csv",
    "customers": "customers_clean.csv",
    "products": "products_clean.csv",
    "regions": "regions_clean.csv",
    "returns": "returns_clean.csv",
    "stores": "stores_clean.csv",
    "transactions": "transactions_clean.csv",
}

DATE_FORMAT = "%Y-%m-%d"


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw: Path
    processed: Path
    reports: Path


def find_project_paths() -> ProjectPaths:
    """Locate the repository whether the script runs from root or scripts/."""
    current = Path.cwd().resolve()
    candidates = [current, current.parent]
    for root in candidates:
        raw = root / "data" / "raw"
        if raw.exists():
            return ProjectPaths(
                root=root,
                raw=raw,
                processed=root / "data" / "processed",
                reports=root / "reports",
            )
    raise FileNotFoundError(
        "Could not find data/raw. Run the script from the repository root."
    )


def require_raw_files(raw_dir: Path) -> None:
    missing = [name for name in RAW_FILES.values() if not (raw_dir / name).exists()]
    if missing:
        raise FileNotFoundError("Missing raw files:\n- " + "\n- ".join(missing))


def load_raw_tables(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load identifiers that must remain textual with explicit dtypes."""
    require_raw_files(raw_dir)

    tables: Dict[str, pd.DataFrame] = {}
    for table, filename in RAW_FILES.items():
        dtype = None
        if table == "customers":
            dtype = {
                "customer_acct_num": "string",
                "customer_postal_code": "string",
            }
        elif table == "products":
            dtype = {"product_sku": "string"}
        elif table == "stores":
            dtype = {"store_phone": "string"}

        tables[table] = pd.read_csv(raw_dir / filename, dtype=dtype)

    return tables


def strip_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove leading and trailing whitespace without changing missing values."""
    cleaned = df.copy()
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return cleaned


def parse_dates(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    cleaned = df.copy()
    for column in columns:
        cleaned[column] = pd.to_datetime(cleaned[column], errors="raise")
    return cleaned


def clean_calendar(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = parse_dates(raw, ["date"])
    cleaned = cleaned.sort_values("date").reset_index(drop=True)
    if cleaned["date"].duplicated().any():
        raise ValueError("Calendar contains duplicate dates.")
    return cleaned


def clean_customers(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = strip_text_columns(raw)
    cleaned = parse_dates(cleaned, ["birthdate", "acct_open_date"])

    cleaned["customer_acct_num"] = (
        cleaned["customer_acct_num"].astype("string").str.zfill(11)
    )
    cleaned["customer_postal_code"] = (
        cleaned["customer_postal_code"].astype("string").str.zfill(5)
    )

    cleaned["last_name_missing"] = cleaned["last_name"].isna()
    cleaned["last_name"] = cleaned["last_name"].fillna("Unknown")

    marital_map = {"M": "Married", "S": "Single"}
    gender_map = {"F": "Female", "M": "Male"}
    homeowner_map = {"Y": True, "N": False}

    cleaned["marital_status"] = cleaned["marital_status"].map(marital_map)
    cleaned["gender"] = cleaned["gender"].map(gender_map)
    cleaned["is_homeowner"] = cleaned["homeowner"].map(homeowner_map)
    cleaned = cleaned.drop(columns=["homeowner"])

    if cleaned[["marital_status", "gender", "is_homeowner"]].isna().any().any():
        raise ValueError("Unexpected customer code found during label mapping.")

    return cleaned.sort_values("customer_id").reset_index(drop=True)


def clean_products(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = strip_text_columns(raw)
    cleaned["product_sku"] = cleaned["product_sku"].astype("string").str.zfill(11)

    cleaned["is_recyclable"] = cleaned["recyclable"].fillna(0).eq(1)
    cleaned["is_low_fat"] = cleaned["low_fat"].fillna(0).eq(1)
    cleaned = cleaned.drop(columns=["recyclable", "low_fat"])

    return cleaned.sort_values("product_id").reset_index(drop=True)


def clean_regions(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = strip_text_columns(raw)
    return cleaned.sort_values("region_id").reset_index(drop=True)


def clean_stores(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = strip_text_columns(raw)
    cleaned = parse_dates(cleaned, ["first_opened_date", "last_remodel_date"])
    cleaned["store_phone"] = cleaned["store_phone"].astype("string")
    return cleaned.sort_values("store_id").reset_index(drop=True)


def build_transactions(raw_1997: pd.DataFrame, raw_1998: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for year, raw in ((1997, raw_1997), (1998, raw_1998)):
        piece = raw.copy()
        piece["source_year"] = year
        piece["source_row_number"] = range(1, len(piece) + 1)
        piece["transaction_line_id"] = (
            "TX-" + str(year) + "-" + piece["source_row_number"].astype(str).str.zfill(6)
        )
        pieces.append(piece)

    cleaned = pd.concat(pieces, ignore_index=True)
    cleaned = parse_dates(cleaned, ["transaction_date", "stock_date"])

    business_columns = [
        "transaction_date",
        "stock_date",
        "product_id",
        "customer_id",
        "store_id",
        "quantity",
    ]
    cleaned["duplicate_candidate"] = cleaned.duplicated(
        business_columns, keep=False
    )

    ordered_columns = [
        "transaction_line_id",
        "transaction_date",
        "stock_date",
        "product_id",
        "customer_id",
        "store_id",
        "quantity",
        "source_year",
        "source_row_number",
        "duplicate_candidate",
    ]
    return cleaned[ordered_columns]


def clean_returns(raw: pd.DataFrame) -> pd.DataFrame:
    cleaned = raw.copy()
    cleaned["source_row_number"] = range(1, len(cleaned) + 1)
    cleaned["return_line_id"] = (
        "RET-" + cleaned["source_row_number"].astype(str).str.zfill(6)
    )
    cleaned = parse_dates(cleaned, ["return_date"])

    business_columns = ["return_date", "product_id", "store_id", "quantity"]
    cleaned["duplicate_candidate"] = cleaned.duplicated(
        business_columns, keep=False
    )

    ordered_columns = [
        "return_line_id",
        "return_date",
        "product_id",
        "store_id",
        "quantity",
        "source_row_number",
        "duplicate_candidate",
    ]
    return cleaned[ordered_columns]


def build_clean_tables(raw: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {
        "calendar": clean_calendar(raw["calendar"]),
        "customers": clean_customers(raw["customers"]),
        "products": clean_products(raw["products"]),
        "regions": clean_regions(raw["regions"]),
        "returns": clean_returns(raw["returns"]),
        "stores": clean_stores(raw["stores"]),
        "transactions": build_transactions(
            raw["transactions_1997"], raw["transactions_1998"]
        ),
    }


def validate_clean_tables(
    raw: Dict[str, pd.DataFrame], clean: Dict[str, pd.DataFrame]
) -> dict[str, int | bool | str]:
    transactions = clean["transactions"]
    returns = clean["returns"]
    customers = clean["customers"]
    products = clean["products"]
    stores = clean["stores"]
    regions = clean["regions"]

    expected_transaction_rows = len(raw["transactions_1997"]) + len(
        raw["transactions_1998"]
    )

    checks: dict[str, int | bool | str] = {
        "transaction_rows_preserved": len(transactions) == expected_transaction_rows,
        "return_rows_preserved": len(returns) == len(raw["returns"]),
        "customer_rows_preserved": len(customers) == len(raw["customers"]),
        "product_rows_preserved": len(products) == len(raw["products"]),
        "store_rows_preserved": len(stores) == len(raw["stores"]),
        "region_rows_preserved": len(regions) == len(raw["regions"]),
        "calendar_rows_preserved": len(clean["calendar"]) == len(raw["calendar"]),
        "clean_missing_cells": int(
            sum(table.isna().sum().sum() for table in clean.values())
        ),
        "transaction_id_unique": bool(transactions["transaction_line_id"].is_unique),
        "return_id_unique": bool(returns["return_line_id"].is_unique),
        "customer_id_unique": bool(customers["customer_id"].is_unique),
        "product_id_unique": bool(products["product_id"].is_unique),
        "store_id_unique": bool(stores["store_id"].is_unique),
        "region_id_unique": bool(regions["region_id"].is_unique),
        "calendar_date_unique": bool(clean["calendar"]["date"].is_unique),
        "customer_account_is_string": str(customers["customer_acct_num"].dtype).startswith("string"),
        "customer_postal_code_is_string": str(customers["customer_postal_code"].dtype).startswith("string"),
        "product_sku_is_string": str(products["product_sku"].dtype).startswith("string"),
        "product_flags_are_boolean": bool(
            pd.api.types.is_bool_dtype(products["is_recyclable"])
            and pd.api.types.is_bool_dtype(products["is_low_fat"])
        ),
        "transaction_product_orphans": int(
            (~transactions["product_id"].isin(products["product_id"])).sum()
        ),
        "transaction_customer_orphans": int(
            (~transactions["customer_id"].isin(customers["customer_id"])).sum()
        ),
        "transaction_store_orphans": int(
            (~transactions["store_id"].isin(stores["store_id"])).sum()
        ),
        "return_product_orphans": int(
            (~returns["product_id"].isin(products["product_id"])).sum()
        ),
        "return_store_orphans": int(
            (~returns["store_id"].isin(stores["store_id"])).sum()
        ),
        "store_region_orphans": int(
            (~stores["region_id"].isin(regions["region_id"])).sum()
        ),
        "postal_codes_not_five_characters": int(
            customers["customer_postal_code"].str.len().ne(5).sum()
        ),
        "missing_last_names_after_cleaning": int(customers["last_name"].isna().sum()),
        "last_name_missing_flags": int(customers["last_name_missing"].sum()),
        "transaction_duplicate_candidate_rows": int(
            transactions["duplicate_candidate"].sum()
        ),
        "return_duplicate_candidate_rows": int(returns["duplicate_candidate"].sum()),
        "transaction_quantity_nonpositive": int(transactions["quantity"].le(0).sum()),
        "return_quantity_nonpositive": int(returns["quantity"].le(0).sum()),
        "stock_date_after_transaction_date": int(
            transactions["stock_date"].gt(transactions["transaction_date"]).sum()
        ),
        "price_not_above_cost": int(
            products["product_retail_price"].le(products["product_cost"]).sum()
        ),
    }

    required_true = [
        "transaction_rows_preserved",
        "return_rows_preserved",
        "customer_rows_preserved",
        "product_rows_preserved",
        "store_rows_preserved",
        "region_rows_preserved",
        "calendar_rows_preserved",
        "transaction_id_unique",
        "return_id_unique",
        "customer_id_unique",
        "product_id_unique",
        "store_id_unique",
        "region_id_unique",
        "calendar_date_unique",
        "customer_account_is_string",
        "customer_postal_code_is_string",
        "product_sku_is_string",
        "product_flags_are_boolean",
    ]
    failed_boolean_checks = [name for name in required_true if checks[name] is not True]

    required_zero = [
        "clean_missing_cells",
        "transaction_product_orphans",
        "transaction_customer_orphans",
        "transaction_store_orphans",
        "return_product_orphans",
        "return_store_orphans",
        "store_region_orphans",
        "postal_codes_not_five_characters",
        "missing_last_names_after_cleaning",
        "transaction_quantity_nonpositive",
        "return_quantity_nonpositive",
        "stock_date_after_transaction_date",
        "price_not_above_cost",
    ]
    failed_zero_checks = [name for name in required_zero if checks[name] != 0]

    checks["validation_status"] = (
        "passed" if not failed_boolean_checks and not failed_zero_checks else "failed"
    )
    if failed_boolean_checks or failed_zero_checks:
        failures = failed_boolean_checks + failed_zero_checks
        raise ValueError("Cleaning validation failed: " + ", ".join(failures))

    return checks


def build_change_log(raw: Dict[str, pd.DataFrame], clean: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "table": "transactions",
                "change": "Appended 1997 and 1998 files",
                "affected_rows": len(clean["transactions"]),
                "reason": "Create one consistent sales table while preserving source-year lineage.",
            },
            {
                "table": "transactions",
                "change": "Added surrogate line ID and source row fields",
                "affected_rows": len(clean["transactions"]),
                "reason": "The source has no transaction or order identifier.",
            },
            {
                "table": "transactions",
                "change": "Flagged exact-looking duplicate candidates",
                "affected_rows": int(clean["transactions"]["duplicate_candidate"].sum()),
                "reason": "Retain uncertain rows but make them visible for analysis and review.",
            },
            {
                "table": "returns",
                "change": "Added surrogate line ID and source row number",
                "affected_rows": len(clean["returns"]),
                "reason": "The source has no return-row identifier.",
            },
            {
                "table": "returns",
                "change": "Flagged exact-looking duplicate candidates",
                "affected_rows": int(clean["returns"]["duplicate_candidate"].sum()),
                "reason": "Identical returns may still be separate real events, so they were not removed.",
            },
            {
                "table": "customers",
                "change": "Converted account and postal identifiers to text",
                "affected_rows": len(clean["customers"]),
                "reason": "Identifiers should not be aggregated as numbers.",
            },
            {
                "table": "customers",
                "change": "Restored five-character postal-code display",
                "affected_rows": int(
                    raw["customers"]["customer_postal_code"].astype("string").str.len().lt(5).sum()
                ),
                "reason": "Four-digit source values had lost a leading zero.",
            },
            {
                "table": "customers",
                "change": "Filled missing display surname and kept a missing-value flag",
                "affected_rows": int(raw["customers"]["last_name"].isna().sum()),
                "reason": "Avoid blank labels without hiding that the source value was missing.",
            },
            {
                "table": "customers",
                "change": "Decoded compact demographic codes",
                "affected_rows": len(clean["customers"]),
                "reason": "Readable labels are safer for reports and Power BI fields.",
            },
            {
                "table": "products",
                "change": "Converted SKU to text",
                "affected_rows": len(clean["products"]),
                "reason": "SKU is an identifier, not a numeric measure.",
            },
            {
                "table": "products",
                "change": "Converted blank/1 product flags to booleans",
                "affected_rows": len(clean["products"]),
                "reason": "The source uses blank for False and 1 for True.",
            },
            {
                "table": "multiple",
                "change": "Parsed and standardized date fields",
                "affected_rows": sum(
                    len(clean[name])
                    for name in ["calendar", "customers", "stores", "returns", "transactions"]
                ),
                "reason": "Date types are required for valid sorting and time intelligence.",
            },
        ]
    )


def build_before_after_summary(
    raw: Dict[str, pd.DataFrame], clean: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    raw_view = {
        "calendar": raw["calendar"],
        "customers": raw["customers"],
        "products": raw["products"],
        "regions": raw["regions"],
        "returns": raw["returns"],
        "stores": raw["stores"],
        "transactions": pd.concat(
            [raw["transactions_1997"], raw["transactions_1998"]], ignore_index=True
        ),
    }

    rows = []
    for table in OUTPUT_FILES:
        before = raw_view[table]
        after = clean[table]
        rows.append(
            {
                "table": table,
                "rows_before": len(before),
                "rows_after": len(after),
                "columns_before": before.shape[1],
                "columns_after": after.shape[1],
                "missing_cells_before": int(before.isna().sum().sum()),
                "missing_cells_after": int(after.isna().sum().sum()),
                "exact_duplicate_rows_before": int(before.duplicated().sum()),
                "duplicate_candidate_rows_after": int(
                    after["duplicate_candidate"].sum()
                    if "duplicate_candidate" in after.columns
                    else 0
                ),
            }
        )
    return pd.DataFrame(rows)


def write_processed_tables(clean: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table, filename in OUTPUT_FILES.items():
        clean[table].to_csv(
            output_dir / filename,
            index=False,
            date_format=DATE_FORMAT,
            encoding="utf-8",
        )


def write_reports(
    reports_dir: Path,
    clean: Dict[str, pd.DataFrame],
    change_log: pd.DataFrame,
    before_after: pd.DataFrame,
    validation: dict[str, int | bool | str],
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    change_log.to_csv(reports_dir / "data_cleaning_log.csv", index=False)
    before_after.to_csv(reports_dir / "data_cleaning_summary.csv", index=False)
    with (reports_dir / "cleaning_validation.json").open("w", encoding="utf-8") as file:
        json.dump(validation, file, indent=2, ensure_ascii=False)

    schema = {
        table: {column: str(dtype) for column, dtype in dataframe.dtypes.items()}
        for table, dataframe in clean.items()
    }
    with (reports_dir / "processed_schema.json").open("w", encoding="utf-8") as file:
        json.dump(schema, file, indent=2, ensure_ascii=False)


def run_cleaning() -> tuple[
    Dict[str, pd.DataFrame],
    Dict[str, pd.DataFrame],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, int | bool | str],
]:
    paths = find_project_paths()
    raw = load_raw_tables(paths.raw)
    clean = build_clean_tables(raw)
    validation = validate_clean_tables(raw, clean)
    change_log = build_change_log(raw, clean)
    before_after = build_before_after_summary(raw, clean)
    write_processed_tables(clean, paths.processed)
    write_reports(paths.reports, clean, change_log, before_after, validation)
    return raw, clean, change_log, before_after, validation


if __name__ == "__main__":
    _, cleaned_tables, change_log_df, summary_df, validation_results = run_cleaning()

    print("Cleaning completed successfully.\n")
    print(summary_df.to_string(index=False))
    print("\nValidation status:", validation_results["validation_status"])
    print("Processed files:")
    for filename in OUTPUT_FILES.values():
        print(f"- data/processed/{filename}")
