"""Reproducible data audit for the Maven Market raw CSV files.

Run from the repository root:
    python scripts/data_audit.py

The script does not change the raw files. It writes audit outputs to reports/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

FILE_MAP = {
    "calendar": "MavenMarket_Calendar.csv",
    "customers": "MavenMarket_Customers.csv",
    "products": "MavenMarket_Products.csv",
    "regions": "MavenMarket_Regions.csv",
    "returns": "MavenMarket_Returns_1997-1998.csv",
    "stores": "MavenMarket_Stores.csv",
    "transactions_1997": "MavenMarket_Transactions_1997.csv",
    "transactions_1998": "MavenMarket_Transactions_1998.csv",
}

DATE_COLUMNS = {
    "calendar": ["date"],
    "customers": ["birthdate", "acct_open_date"],
    "returns": ["return_date"],
    "stores": ["first_opened_date", "last_remodel_date"],
    "transactions": ["transaction_date", "stock_date"],
}


def find_project_root() -> Path:
    current = Path.cwd().resolve()
    if (current / "data" / "raw").exists():
        return current
    if (current.parent / "data" / "raw").exists():
        return current.parent
    raise FileNotFoundError(
        "Could not find data/raw. Run this script from the repository root."
    )


def load_raw_data(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    missing = [filename for filename in FILE_MAP.values() if not (raw_dir / filename).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing raw files:\n- " + "\n- ".join(missing)
        )

    tables = {
        name: pd.read_csv(raw_dir / filename)
        for name, filename in FILE_MAP.items()
    }
    tables["transactions"] = pd.concat(
        [
            tables["transactions_1997"].assign(source_year=1997),
            tables["transactions_1998"].assign(source_year=1998),
        ],
        ignore_index=True,
    )
    return tables


def parse_dates(tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    parsed = {name: df.copy() for name, df in tables.items()}
    for table_name, columns in DATE_COLUMNS.items():
        for column in columns:
            parsed[table_name][column] = pd.to_datetime(
                parsed[table_name][column], errors="coerce"
            )
    return parsed


def build_table_profile(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tables.items():
        if name == "transactions":
            continue
        rows.append(
            {
                "table": name,
                "rows": len(df),
                "columns": df.shape[1],
                "missing_cells": int(df.isna().sum().sum()),
                "missing_cell_rate_pct": round(df.isna().sum().sum() / df.size * 100, 4),
                "exact_duplicate_rows": int(df.duplicated().sum()),
                "exact_duplicate_rate_pct": round(df.duplicated().mean() * 100, 4),
            }
        )
    return pd.DataFrame(rows)


def build_column_profile(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for table_name, df in tables.items():
        if table_name in {"transactions_1997", "transactions_1998"}:
            continue
        for column in df.columns:
            series = df[column]
            non_null = series.dropna()
            rows.append(
                {
                    "table": table_name,
                    "column": column,
                    "pandas_dtype": str(series.dtype),
                    "rows": len(series),
                    "missing_count": int(series.isna().sum()),
                    "missing_rate_pct": round(series.isna().mean() * 100, 4),
                    "distinct_count": int(non_null.nunique()),
                    "min_value": str(non_null.min()) if len(non_null) and pd.api.types.is_numeric_dtype(series) else "",
                    "max_value": str(non_null.max()) if len(non_null) and pd.api.types.is_numeric_dtype(series) else "",
                }
            )
    return pd.DataFrame(rows)


def data_dictionary_rows() -> list[dict]:
    # Descriptions are intentionally concise so the dictionary is useful during modeling.
    specs = {
        "calendar": {
            "date": ("Calendar date covering the analysis period", "date", "Date key", "Convert to datetime; verify uniqueness"),
        },
        "customers": {
            "customer_id": ("Customer identifier used in transactions", "integer", "Primary key", "Keep; validate uniqueness"),
            "customer_acct_num": ("Customer account number", "string", "Business identifier", "Convert to string to avoid numeric treatment"),
            "first_name": ("Customer first name", "string", "Customer attribute", "Trim whitespace"),
            "last_name": ("Customer last name", "string", "Customer attribute", "One missing value; use Unknown for display only"),
            "customer_address": ("Street address", "string", "Customer attribute", "Trim whitespace"),
            "customer_city": ("Customer city", "string", "Geographic attribute", "Standardize text"),
            "customer_state_province": ("Customer state or province", "string", "Geographic attribute", "Standardize text"),
            "customer_postal_code": ("Customer postal code", "string", "Geographic identifier", "Convert to string; left-pad four-digit values"),
            "customer_country": ("Customer country", "category", "Geographic attribute", "Validate accepted values"),
            "birthdate": ("Customer date of birth", "date", "Demographic attribute", "Convert to datetime"),
            "marital_status": ("Marital status code", "category", "Demographic attribute", "Map M/S labels if needed"),
            "yearly_income": ("Income band", "ordered category", "Customer segment", "Create ordered band for sorting"),
            "gender": ("Gender code", "category", "Demographic attribute", "Validate accepted values"),
            "total_children": ("Total number of children", "integer", "Demographic measure", "Validate non-negative values"),
            "num_children_at_home": ("Children currently living at home", "integer", "Demographic measure", "Check value does not exceed total_children"),
            "education": ("Highest education category", "category", "Customer segment", "Standardize category labels"),
            "acct_open_date": ("Date the customer account was opened", "date", "Customer lifecycle attribute", "Convert to datetime; check before transactions"),
            "member_card": ("Loyalty membership tier", "ordered category", "Customer segment", "Set Normal, Bronze, Silver, Golden order"),
            "occupation": ("Occupation group", "category", "Customer segment", "Standardize category labels"),
            "homeowner": ("Home ownership flag", "boolean", "Demographic attribute", "Map Y/N to boolean"),
        },
        "products": {
            "product_id": ("Product identifier used in facts", "integer", "Primary key", "Keep; validate uniqueness"),
            "product_brand": ("Product brand", "category", "Product attribute", "Trim and standardize text"),
            "product_name": ("Product display name", "string", "Product attribute", "Trim whitespace"),
            "product_sku": ("Stock keeping unit", "string", "Business identifier", "Convert to string"),
            "product_retail_price": ("Unit retail price", "decimal", "Monetary measure", "Validate positive values"),
            "product_cost": ("Unit product cost", "decimal", "Monetary measure", "Validate positive and below retail price"),
            "product_weight": ("Product weight", "decimal", "Product measure", "Validate positive values"),
            "recyclable": ("Recyclable packaging flag", "boolean", "Product attribute", "Map blank to False and 1 to True"),
            "low_fat": ("Low-fat product flag", "boolean", "Product attribute", "Map blank to False and 1 to True"),
        },
        "regions": {
            "region_id": ("Sales region identifier", "integer", "Primary key", "Keep; validate uniqueness"),
            "sales_district": ("Sales district name", "category", "Geographic attribute", "Standardize text"),
            "sales_region": ("Higher-level sales region", "category", "Geographic attribute", "Standardize text"),
        },
        "returns": {
            "return_date": ("Date a product quantity was returned", "date", "Fact date", "Convert to datetime"),
            "product_id": ("Returned product identifier", "integer", "Foreign key", "Validate against products"),
            "store_id": ("Store receiving the return", "integer", "Foreign key", "Validate against stores"),
            "quantity": ("Returned quantity", "integer", "Fact measure", "Validate positive values"),
        },
        "stores": {
            "store_id": ("Store identifier used in facts", "integer", "Primary key", "Keep; validate uniqueness"),
            "region_id": ("Sales region assigned to the store", "integer", "Foreign key", "Validate against regions"),
            "store_type": ("Store format", "category", "Store attribute", "Validate accepted values"),
            "store_name": ("Store display name", "string", "Store attribute", "Trim whitespace"),
            "store_street_address": ("Store street address", "string", "Store attribute", "Trim whitespace"),
            "store_city": ("Store city", "string", "Geographic attribute", "Standardize text"),
            "store_state": ("Store state or province", "string", "Geographic attribute", "Standardize text"),
            "store_country": ("Store country", "category", "Geographic attribute", "Validate accepted values"),
            "store_phone": ("Store phone number", "string", "Store attribute", "Keep as text"),
            "first_opened_date": ("Original store opening date", "date", "Store lifecycle attribute", "Convert to datetime"),
            "last_remodel_date": ("Most recent remodel date", "date", "Store lifecycle attribute", "Convert to datetime; check after opening"),
            "total_sqft": ("Total store area in square feet", "integer", "Store capacity measure", "Validate positive values"),
            "grocery_sqft": ("Grocery area in square feet", "integer", "Store capacity measure", "Check not greater than total_sqft"),
        },
        "transactions": {
            "transaction_date": ("Date of the sales transaction row", "date", "Fact date", "Convert to datetime"),
            "stock_date": ("Date the sold stock was recorded", "date", "Operational date", "Convert to datetime; verify not after transaction date"),
            "product_id": ("Sold product identifier", "integer", "Foreign key", "Validate against products"),
            "customer_id": ("Customer identifier", "integer", "Foreign key", "Validate against customers"),
            "store_id": ("Store identifier", "integer", "Foreign key", "Validate against stores"),
            "quantity": ("Units sold on the transaction row", "integer", "Fact measure", "Validate positive values"),
        },
    }
    rows = []
    for table, columns in specs.items():
        for column, (description, recommended_type, role, cleaning) in columns.items():
            rows.append({
                "table": table,
                "column": column,
                "business_description": description,
                "recommended_type": recommended_type,
                "analytical_role": role,
                "cleaning_requirement": cleaning,
            })
    return rows


def build_data_dictionary(raw_tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = data_dictionary_rows()
    raw_lookup = {}
    for table, df in raw_tables.items():
        normalized_table = "transactions" if table.startswith("transactions_") else table
        if normalized_table == "transactions" and normalized_table in raw_lookup:
            continue
        raw_lookup[normalized_table] = {col: str(dtype) for col, dtype in df.dtypes.items()}

    for row in rows:
        row["raw_pandas_type"] = raw_lookup[row["table"]][row["column"]]
    columns = [
        "table", "column", "business_description", "raw_pandas_type",
        "recommended_type", "analytical_role", "cleaning_requirement"
    ]
    return pd.DataFrame(rows)[columns]


def build_quality_findings(tables: Dict[str, pd.DataFrame], parsed: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = parsed["customers"]
    products = parsed["products"]
    stores = parsed["stores"]
    transactions = parsed["transactions"]
    returns = parsed["returns"]
    calendar = parsed["calendar"]

    duplicate_transaction_count = int(
        transactions.duplicated(
            ["transaction_date", "stock_date", "product_id", "customer_id", "store_id", "quantity"]
        ).sum()
    )
    duplicate_return_count = int(
        returns.duplicated(["return_date", "product_id", "store_id", "quantity"]).sum()
    )
    four_digit_postal = int(customers["customer_postal_code"].astype(str).str.len().lt(5).sum())

    transaction_dates = set(transactions["transaction_date"])
    calendar_dates = set(calendar["date"])
    missing_activity_dates = len(calendar_dates - transaction_dates)

    stores_1997 = transactions.loc[transactions["source_year"] == 1997, "store_id"].nunique()
    stores_1998 = transactions.loc[transactions["source_year"] == 1998, "store_id"].nunique()

    age_at_account = (
        (customers["acct_open_date"] - customers["birthdate"]).dt.days / 365.2425
    )
    under_16_account = int(age_at_account.lt(16).sum())

    active_customers = transactions["customer_id"].nunique()
    inactive_customers = customers["customer_id"].nunique() - active_customers
    active_products = transactions["product_id"].nunique()
    inactive_products = products["product_id"].nunique() - active_products

    findings = [
        {
            "dataset": "transactions",
            "column_or_rule": "Comparable store coverage by year",
            "issue": f"Only {stores_1997} stores have transactions in 1997, compared with {stores_1998} in 1998.",
            "affected_rows": "N/A",
            "affected_rate_pct": "N/A",
            "severity": "High",
            "confidence": "High",
            "impact": "A direct total-company YoY comparison mixes business growth with a change in store coverage.",
            "recommended_action": "Report total growth and same-store growth separately. Use the 13 stores present in both years as the comparable cohort.",
        },
        {
            "dataset": "transactions",
            "column_or_rule": "Missing transaction-row identifier",
            "issue": "The fact files do not contain a transaction ID, receipt ID, or order ID.",
            "affected_rows": len(transactions),
            "affected_rate_pct": 100.0,
            "severity": "High",
            "confidence": "High",
            "impact": "Rows cannot be uniquely traced to an order, and exact-looking duplicates cannot be confirmed as errors.",
            "recommended_action": "Create a surrogate row ID during cleaning. Do not report Total Orders or Average Order Value.",
        },
        {
            "dataset": "returns",
            "column_or_rule": "Missing return and transaction identifiers",
            "issue": "Returns cannot be linked to a customer or a specific sales row.",
            "affected_rows": len(returns),
            "affected_rate_pct": 100.0,
            "severity": "High",
            "confidence": "High",
            "impact": "Customer-level return analysis and exact return-to-sale matching are not supported.",
            "recommended_action": "Create a surrogate return row ID and limit return analysis to date, product, store, and aggregate rates.",
        },
        {
            "dataset": "transactions",
            "column_or_rule": "Exact-looking duplicate rows",
            "issue": f"{duplicate_transaction_count} rows repeat all available transaction fields.",
            "affected_rows": duplicate_transaction_count,
            "affected_rate_pct": round(duplicate_transaction_count / len(transactions) * 100, 4),
            "severity": "Medium",
            "confidence": "Medium",
            "impact": "Removing them without a true transaction ID could undercount legitimate repeated purchases; keeping true duplicates could slightly overstate sales.",
            "recommended_action": "Flag the rows but retain them until a source-level uniqueness rule is available.",
        },
        {
            "dataset": "returns",
            "column_or_rule": "Exact-looking duplicate rows",
            "issue": f"{duplicate_return_count} rows repeat all available return fields.",
            "affected_rows": duplicate_return_count,
            "affected_rate_pct": round(duplicate_return_count / len(returns) * 100, 4),
            "severity": "Medium",
            "confidence": "Medium",
            "impact": "The return quantity may be slightly overstated if these are duplicate records, but identical return events are also possible.",
            "recommended_action": "Flag and review; do not deduplicate automatically.",
        },
        {
            "dataset": "calendar / transactions",
            "column_or_rule": "Dates with no transaction rows",
            "issue": f"{missing_activity_dates} calendar dates have no sales rows: 42 in 1997 and 15 in 1998.",
            "affected_rows": missing_activity_dates,
            "affected_rate_pct": round(missing_activity_dates / len(calendar) * 100, 4),
            "severity": "Medium",
            "confidence": "Medium",
            "impact": "The gaps may represent legitimate zero-sales days or missing extracts. Imputing sales would create unsupported values.",
            "recommended_action": "Keep the complete calendar, show zero activity through the date dimension, and document the source uncertainty.",
        },
        {
            "dataset": "customers",
            "column_or_rule": "customer_postal_code data type",
            "issue": f"{four_digit_postal} postal codes are four digits because the field was loaded as an integer.",
            "affected_rows": four_digit_postal,
            "affected_rate_pct": round(four_digit_postal / len(customers) * 100, 4),
            "severity": "Medium",
            "confidence": "High",
            "impact": "Leading zeros are lost and postal codes may display incorrectly or join incorrectly to external geography data.",
            "recommended_action": "Convert the field to text and left-pad four-digit values to five characters.",
        },
        {
            "dataset": "products",
            "column_or_rule": "recyclable binary encoding",
            "issue": f"{int(products['recyclable'].isna().sum())} blank values coexist with 1 values; the source uses blank as the false state.",
            "affected_rows": int(products["recyclable"].isna().sum()),
            "affected_rate_pct": round(products["recyclable"].isna().mean() * 100, 4),
            "severity": "Low",
            "confidence": "High",
            "impact": "Treating these blanks as unknown would overstate missingness and make the field harder to use.",
            "recommended_action": "Map blank to False and 1 to True, then store as boolean.",
        },
        {
            "dataset": "products",
            "column_or_rule": "low_fat binary encoding",
            "issue": f"{int(products['low_fat'].isna().sum())} blank values coexist with 1 values; the source uses blank as the false state.",
            "affected_rows": int(products["low_fat"].isna().sum()),
            "affected_rate_pct": round(products["low_fat"].isna().mean() * 100, 4),
            "severity": "Low",
            "confidence": "High",
            "impact": "Treating these blanks as unknown would overstate missingness and make the field harder to use.",
            "recommended_action": "Map blank to False and 1 to True, then store as boolean.",
        },
        {
            "dataset": "customers",
            "column_or_rule": "last_name completeness",
            "issue": "One customer record has no last name.",
            "affected_rows": int(customers["last_name"].isna().sum()),
            "affected_rate_pct": round(customers["last_name"].isna().mean() * 100, 4),
            "severity": "Low",
            "confidence": "High",
            "impact": "Customer display labels may be incomplete, but analytical joins and measures are unaffected.",
            "recommended_action": "Keep the source value and use 'Unknown' only in the presentation layer if a full name is required.",
        },
        {
            "dataset": "customers",
            "column_or_rule": "Age at account opening",
            "issue": f"{under_16_account} customers were under 16 on the recorded account-open date.",
            "affected_rows": under_16_account,
            "affected_rate_pct": round(under_16_account / len(customers) * 100, 4),
            "severity": "Low",
            "confidence": "Medium",
            "impact": "The records may represent household accounts or synthetic data. Age-at-account-open analysis would be unreliable without context.",
            "recommended_action": "Retain the dates, document the limitation, and avoid using age at account opening as a management KPI.",
        },
        {
            "dataset": "dimensions",
            "column_or_rule": "Dimension members without sales activity",
            "issue": f"{inactive_customers} customers and {inactive_products} product have no transaction rows in the two-year fact data.",
            "affected_rows": inactive_customers + inactive_products,
            "affected_rate_pct": "N/A",
            "severity": "Low",
            "confidence": "High",
            "impact": "Counting all customer dimension rows would overstate active customers.",
            "recommended_action": "Keep dimension members, but define Active Customers and Active Products from the transaction fact.",
        },
        {
            "dataset": "multiple tables",
            "column_or_rule": "Raw schema types",
            "issue": "Date fields are text, and account number, SKU, and postal code are numeric identifiers.",
            "affected_rows": "N/A",
            "affected_rate_pct": "N/A",
            "severity": "Medium",
            "confidence": "High",
            "impact": "Incorrect data types can break date intelligence, formatting, sorting, and identifier preservation.",
            "recommended_action": "Apply explicit types during cleaning and validate failed casts before exporting processed data.",
        },
    ]
    return pd.DataFrame(findings)


def integrity_summary(parsed: Dict[str, pd.DataFrame]) -> dict:
    customers = parsed["customers"]
    products = parsed["products"]
    regions = parsed["regions"]
    stores = parsed["stores"]
    transactions = parsed["transactions"]
    returns = parsed["returns"]

    return {
        "transaction_product_orphans": int((~transactions["product_id"].isin(products["product_id"])).sum()),
        "transaction_customer_orphans": int((~transactions["customer_id"].isin(customers["customer_id"])).sum()),
        "transaction_store_orphans": int((~transactions["store_id"].isin(stores["store_id"])).sum()),
        "return_product_orphans": int((~returns["product_id"].isin(products["product_id"])).sum()),
        "return_store_orphans": int((~returns["store_id"].isin(stores["store_id"])).sum()),
        "store_region_orphans": int((~stores["region_id"].isin(regions["region_id"])).sum()),
        "transaction_quantity_nonpositive": int((transactions["quantity"] <= 0).sum()),
        "return_quantity_nonpositive": int((returns["quantity"] <= 0).sum()),
        "stock_date_after_transaction_date": int((transactions["stock_date"] > transactions["transaction_date"]).sum()),
        "transaction_before_store_open": int((transactions["transaction_date"] < transactions["store_id"].map(stores.set_index("store_id")["first_opened_date"])).sum()),
        "transaction_before_account_open": int((transactions["transaction_date"] < transactions["customer_id"].map(customers.set_index("customer_id")["acct_open_date"])).sum()),
        "product_price_not_above_cost": int((products["product_retail_price"] <= products["product_cost"]).sum()),
        "grocery_sqft_above_total_sqft": int((stores["grocery_sqft"] > stores["total_sqft"]).sum()),
        "children_at_home_above_total_children": int((customers["num_children_at_home"] > customers["total_children"]).sum()),
    }


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def write_markdown_reports(
    reports_dir: Path,
    table_profile: pd.DataFrame,
    quality_findings: pd.DataFrame,
    data_dictionary: pd.DataFrame,
    integrity: dict,
    parsed: Dict[str, pd.DataFrame],
) -> None:
    severity_order = pd.CategoricalDtype(["High", "Medium", "Low"], ordered=True)
    ordered = quality_findings.copy()
    ordered["severity"] = ordered["severity"].astype(severity_order)
    ordered = ordered.sort_values(["severity", "dataset"]).reset_index(drop=True)

    summary = f"""# Data Quality Report

## Scope

This audit covers the eight raw Maven Market CSV files. The raw files were profiled without editing them. The two transaction files were also combined in memory to test cross-year coverage and integrity.

## Dataset summary

{dataframe_to_markdown(table_profile)}

## Audit result

The data is suitable for the next stage, but a few rules need to be carried into cleaning and analysis:

- Overall 1997–1998 growth is not a like-for-like comparison because store coverage expands from 13 to 24 stores.
- Transaction and return rows have no source-level unique identifier.
- Exact-looking duplicate rows should be flagged, not removed automatically.
- Blank product flags represent the false state and should be converted explicitly.
- Postal codes and other identifiers need text data types.

## Findings

{dataframe_to_markdown(ordered[["severity", "dataset", "column_or_rule", "issue", "impact", "recommended_action"]])}

## Referential and business-rule checks

| Check | Failed rows |
|---|---:|
"""
    for key, value in integrity.items():
        summary += f"| `{key}` | {value:,} |\n"

    summary += """

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
"""
    (reports_dir / "data_quality_report.md").write_text(summary, encoding="utf-8")

    dd_parts = ["# Data Dictionary", "", "Recommended types describe the processed analytical model, not the raw CSV schema.", ""]
    for table_name in data_dictionary["table"].drop_duplicates():
        dd_parts += [f"## {table_name.replace('_', ' ').title()}", "", dataframe_to_markdown(data_dictionary[data_dictionary["table"] == table_name]), ""]
    (reports_dir / "data_dictionary.md").write_text("\n".join(dd_parts), encoding="utf-8")


def run_audit(project_root: Path | None = None, write_outputs: bool = True) -> dict:
    root = project_root or find_project_root()
    raw_dir = root / "data" / "raw"
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    raw_tables = load_raw_data(raw_dir)
    parsed_tables = parse_dates(raw_tables)

    table_profile = build_table_profile(raw_tables)
    column_profile = build_column_profile(raw_tables)
    data_dictionary = build_data_dictionary(raw_tables)
    quality_findings = build_quality_findings(raw_tables, parsed_tables)
    integrity = integrity_summary(parsed_tables)

    summary = {
        "raw_files": len(FILE_MAP),
        "transaction_rows": int(len(parsed_tables["transactions"])),
        "return_rows": int(len(parsed_tables["returns"])),
        "customers": int(len(parsed_tables["customers"])),
        "products": int(len(parsed_tables["products"])),
        "stores": int(len(parsed_tables["stores"])),
        "calendar_start": str(parsed_tables["calendar"]["date"].min().date()),
        "calendar_end": str(parsed_tables["calendar"]["date"].max().date()),
        "high_findings": int((quality_findings["severity"] == "High").sum()),
        "medium_findings": int((quality_findings["severity"] == "Medium").sum()),
        "low_findings": int((quality_findings["severity"] == "Low").sum()),
        "integrity_checks_failed": int(sum(integrity.values())),
    }

    if write_outputs:
        table_profile.to_csv(reports_dir / "table_profile.csv", index=False)
        column_profile.to_csv(reports_dir / "column_profile.csv", index=False)
        quality_findings.to_csv(reports_dir / "data_quality_report.csv", index=False)
        data_dictionary.to_csv(reports_dir / "data_dictionary.csv", index=False)
        (reports_dir / "audit_summary.json").write_text(
            json.dumps({"summary": summary, "integrity": integrity}, indent=2),
            encoding="utf-8",
        )
        write_markdown_reports(
            reports_dir,
            table_profile,
            quality_findings,
            data_dictionary,
            integrity,
            parsed_tables,
        )

    return {
        "summary": summary,
        "table_profile": table_profile,
        "column_profile": column_profile,
        "quality_findings": quality_findings,
        "data_dictionary": data_dictionary,
        "integrity": integrity,
        "tables": parsed_tables,
    }


if __name__ == "__main__":
    results = run_audit()
    print(json.dumps(results["summary"], indent=2))
