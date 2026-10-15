"""Validate every Power BI measure on the Power BI Desktop engine.

Prerequisite: dashboard/MavenMarket.pbip is open in Power BI Desktop.

Run from the repository root:
    python scripts/validate_power_bi_measures.py --refresh

The script queries the Analysis Services engine that Power BI Desktop runs for
the open report (through scripts/power_bi_desktop_engine.ps1) and compares:

- KPI measures with reports/kpi_baseline_snapshot.csv for the full period,
  1997 and 1998;
- all other measures with values calculated independently in pandas from the
  data/model CSV files.

Every measure in the semantic model must be covered by at least one check.
Results are written to reports/power_bi_measure_validation.csv and
reports/power_bi_measure_validation.json (no run timestamps).
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_power_bi_report import MEASURE_METADATA  # noqa: E402

ENGINE_SCRIPT = ROOT / "scripts" / "power_bi_desktop_engine.ps1"
RELATIVE_TOLERANCE = 1e-9
ABSOLUTE_TOLERANCE = 1e-6
# DIVIDE(fixed decimal, whole number) returns a fixed decimal number, which the
# engine stores with four decimal places. These ratios are compared at that precision.
FIXED_DECIMAL_TOLERANCE = 5e-5
FIXED_DECIMAL_RATIOS = {
    "Revenue per Active Customer",
    "Profit per Active Customer",
    "Revenue per Active Store",
    "Profit per Active Store",
    "Revenue per Square Foot",
    "Gross Profit per Square Foot",
    "Average Revenue per Sales Line",
}

# Snapshot metric -> measure. Growth metrics only have a 1998 value.
SNAPSHOT_MEASURES = {
    "total_revenue": "Total Revenue",
    "total_product_cost": "Total Product Cost",
    "gross_product_profit": "Gross Product Profit",
    "gross_margin_pct": "Gross Margin %",
    "revenue_growth_pct": "Revenue Growth %",
    "profit_growth_pct": "Profit Growth %",
    "same_store_revenue_growth_pct": "Same-Store Revenue Growth %",
    "same_store_profit_growth_pct": "Same-Store Profit Growth %",
    "quantity_sold": "Quantity Sold",
    "sales_lines": "Sales Lines",
    "active_customers": "Active Customers",
    "active_stores": "Active Stores",
    "active_products": "Active Products",
    "returned_quantity": "Returned Quantity",
    "return_quantity_rate_pct": "Return Quantity Rate %",
    "revenue_per_active_customer": "Revenue per Active Customer",
    "profit_per_active_customer": "Profit per Active Customer",
    "repeat_customers": "Repeat Customers",
    "repeat_customer_rate_pct": "Repeat Customer Rate %",
    "revenue_per_store": "Revenue per Active Store",
    "profit_per_store": "Profit per Active Store",
    "revenue_per_sqft": "Revenue per Square Foot",
    "profit_per_sqft": "Gross Profit per Square Foot",
    "average_revenue_per_sales_line": "Average Revenue per Sales Line",
    "average_units_per_sales_line": "Average Units per Sales Line",
    "top_10pct_customer_revenue_contribution_pct": "Top 10% Customer Revenue Contribution %",
    "top_product_revenue_contribution_pct": "Top Product Revenue Contribution %",
}
CONTEXT_FILTERS = {
    "overall": None,
    "1997": "DimDate[year] = 1997",
    "1998": "DimDate[year] = 1998",
}


@dataclass
class Check:
    measure: str
    context: str
    dax: str
    expected: Any
    source: str
    grouped: bool = False


def dax_string(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def scalar_query(measure: str, filters: list[str]) -> str:
    expression = f"[{measure}]"
    if filters:
        expression = f"CALCULATE([{measure}], {', '.join(filters)})"
    return f'EVALUATE ROW("value", {expression})'


def grouped_query(column: str, measure: str) -> str:
    return f'EVALUATE SUMMARIZECOLUMNS({column}, "value", [{measure}])'


# ---------------------------------------------------------------------------
# Independent expectations (pandas)
# ---------------------------------------------------------------------------


def load_model() -> dict[str, pd.DataFrame]:
    model = ROOT / "data" / "model"
    tables = {
        name: pd.read_csv(model / f"{name}.csv")
        for name in ["dim_date", "dim_customer", "dim_product", "dim_store", "fact_sales", "fact_returns"]
    }
    tables["dim_date"]["date"] = pd.to_datetime(tables["dim_date"]["date"])
    return tables


def dense_rank_desc(amounts: pd.Series) -> pd.Series:
    # Round to cents first: the engine sums fixed decimals exactly, floats do not.
    return amounts.round(2).rank(method="dense", ascending=False).astype(int)


def build_checks(snapshot: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> list[Check]:
    checks: list[Check] = []
    sales = tables["fact_sales"].merge(
        tables["dim_date"][["date_key", "date", "year", "year_month"]],
        left_on="transaction_date_key",
        right_on="date_key",
    )
    sales = sales.merge(tables["dim_store"][["store_key", "store_name", "is_same_store_comparable", "sales_region"]], on="store_key")
    sales = sales.merge(tables["dim_product"][["product_key", "product_name", "product_brand"]], on="product_key")
    returns = tables["fact_returns"].merge(
        tables["dim_store"][["store_key", "store_name"]], on="store_key"
    ).merge(tables["dim_product"][["product_key", "product_name"]], on="product_key")

    # 1. Snapshot measures: overall, 1997 and 1998.
    snapshot = snapshot.set_index("metric_id")
    for metric, measure in SNAPSHOT_MEASURES.items():
        for context, year_filter in CONTEXT_FILTERS.items():
            expected = snapshot.loc[metric, context]
            if pd.isna(expected):
                continue
            filters = [year_filter] if year_filter else []
            checks.append(
                Check(measure, context, scalar_query(measure, filters), float(expected), "kpi_baseline_snapshot")
            )

    # 2. Values derived from the model CSV files.
    by_year = sales.groupby("year")[["revenue", "gross_product_profit"]].sum()
    comparable = sales.loc[sales["is_same_store_comparable"]]
    comparable_by_year = comparable.groupby("year")[["revenue", "gross_product_profit"]].sum()
    total_quantity = sales["quantity_sold"].sum()
    network_rate = returns["return_quantity"].sum() / total_quantity

    def add(measure: str, context: str, filters: list[str], expected: Any) -> None:
        checks.append(Check(measure, context, scalar_query(measure, filters), expected, "pandas_model_csv"))

    y1998 = ["DimDate[year] = 1998"]
    add("Revenue Previous Year", "1998", y1998, by_year.loc[1997, "revenue"])
    add("Profit Previous Year", "1998", y1998, by_year.loc[1997, "gross_product_profit"])
    add("Same-Store Revenue", "overall", [], comparable["revenue"].sum())
    add("Same-Store Revenue", "1998", y1998, comparable_by_year.loc[1998, "revenue"])
    add("Same-Store Revenue Previous Year", "1998", y1998, comparable_by_year.loc[1997, "revenue"])
    add("Same-Store Profit", "overall", [], comparable["gross_product_profit"].sum())
    add("Same-Store Profit Previous Year", "1998", y1998, comparable_by_year.loc[1997, "gross_product_profit"])

    latest_growth = by_year.loc[1998, "revenue"] / by_year.loc[1997, "revenue"] - 1
    latest_same_store = comparable_by_year.loc[1998, "revenue"] / comparable_by_year.loc[1997, "revenue"] - 1
    add("Latest Year Revenue Growth %", "overall", [], latest_growth)
    add("Latest Year Revenue Growth %", "1997", ["DimDate[year] = 1997"], None)
    add("Latest Year Same-Store Revenue Growth %", "overall", [], latest_same_store)
    add("Reported Growth Label", "overall", [], f"+{latest_growth * 100:.1f}%")
    add("Reported Growth Label", "1997", ["DimDate[year] = 1997"], "No prior-year comparison")
    add("Same-Store Growth Label", "overall", [], f"+{latest_same_store * 100:.1f}%")
    add("Same-Store Growth Label", "1997", ["DimDate[year] = 1997"], "No comparable-store baseline")

    customer_revenue = sales.groupby("customer_key")["revenue"].sum()
    top_count = math.ceil(len(customer_revenue) * 0.10)
    ordered_customers = (
        customer_revenue.reset_index().sort_values(["revenue", "customer_key"], ascending=[False, True])
    )
    add("Top 10% Customer Revenue", "overall", [], ordered_customers["revenue"].head(top_count).sum())
    add("Top Product Revenue", "overall", [], sales.groupby("product_key")["revenue"].sum().max())

    active_area = tables["dim_store"].loc[
        tables["dim_store"]["store_key"].isin(sales["store_key"].unique()), "total_sqft"
    ].sum()
    add("Active Store Area", "overall", [], active_area)
    add("Active Store Area", "1997", ["DimDate[year] = 1997"], tables["dim_store"].loc[
        tables["dim_store"]["store_key"].isin(sales.loc[sales["year"] == 1997, "store_key"].unique()), "total_sqft"
    ].sum())
    add("Comparable Stores", "overall", [], int(tables["dim_store"]["is_same_store_comparable"].sum()))
    add("Visible Store Count", "overall", [], sales["store_key"].nunique())
    add("Visible Product Count", "overall", [], sales["product_key"].nunique())
    add("Visible Customer Count", "overall", [], sales["customer_key"].nunique())
    add("Return Lines", "overall", [], len(tables["fact_returns"]))
    add("Returned Products", "overall", [], tables["fact_returns"]["product_key"].nunique())
    add("Product Return Rate (300+ Units) %", "overall", [], network_rate)
    add("Return Rate vs Overall (pp)", "overall", [], 0.0)
    add("Return Review Flag", "overall", [], "Within network range")
    add("Revenue YTD", "overall", [], by_year.loc[1998, "revenue"])
    add("Revenue YTD", "1997", ["DimDate[year] = 1997"], by_year.loc[1997, "revenue"])
    add("Gross Profit YTD", "overall", [], by_year.loc[1998, "gross_product_profit"])
    add("Revenue Running Total", "overall", [], sales["revenue"].sum())

    date_min = tables["dim_date"]["date"].min()
    date_max = tables["dim_date"]["date"].max()
    date_range = f"{date_min:%b} {date_min.day}, {date_min:%Y} – {date_max:%b} {date_max.day}, {date_max:%Y}"
    add("Selected Date Range", "overall", [], date_range)
    add("Selected Geography", "overall", [], "All selected locations")
    add("Selected Geography", "region North West", ['DimStore[sales_region] = "North West"'], "North West")
    add("Selected Geography", "store Store 8", ['DimStore[store_name] = "Store 8"'], "Store 8")
    add("Selected Geography", "country Canada", ['DimStore[store_country] = "Canada"'], "Canada West")
    add("Executive Page Subtitle", "overall", [], f"{date_range}  |  All selected locations")

    # Monthly series: previous month, MoM growth, YTD and running total.
    months = (
        tables["dim_date"].groupby("year_month").agg(year=("year", "first"), month_start=("date", "min"))
    )
    monthly = sales.groupby("year_month")[["revenue", "gross_product_profit"]].sum()
    months = months.join(monthly).sort_values("month_start")
    months["previous_revenue"] = months["revenue"].shift(1)
    months["previous_profit"] = months["gross_product_profit"].shift(1)
    months["mom_revenue"] = months["revenue"] / months["previous_revenue"] - 1
    months["mom_profit"] = months["gross_product_profit"] / months["previous_profit"] - 1
    months["ytd_revenue"] = months.groupby("year")["revenue"].cumsum()
    months["ytd_profit"] = months.groupby("year")["gross_product_profit"].cumsum()
    months["running_total"] = months["revenue"].fillna(0).cumsum()

    def grouped(measure: str, column: str, expected: pd.Series) -> None:
        values = {str(k): (None if pd.isna(v) else v) for k, v in expected.items()}
        values = {k: v for k, v in values.items() if v is not None}
        checks.append(
            Check(measure, f"by {column}", grouped_query(column, measure), values, "pandas_model_csv", grouped=True)
        )

    grouped("Revenue Previous Month", "DimDate[year_month]", months["previous_revenue"])
    grouped("Revenue MoM Growth %", "DimDate[year_month]", months["mom_revenue"])
    grouped("Gross Profit Previous Month", "DimDate[year_month]", months["previous_profit"])
    grouped("Gross Profit MoM Growth %", "DimDate[year_month]", months["mom_profit"])
    grouped("Revenue YTD", "DimDate[year_month]", months["ytd_revenue"])
    grouped("Gross Profit YTD", "DimDate[year_month]", months["ytd_profit"])
    running = months["running_total"].where(months["month_start"] >= sales["date"].min().replace(day=1))
    grouped("Revenue Running Total", "DimDate[year_month]", running)

    # Rankings and return rates by entity.
    all_stores = tables["dim_store"]["store_name"]
    store_revenue = sales.groupby("store_name")["revenue"].sum().reindex(all_stores, fill_value=0)
    grouped("Store Revenue Rank", "DimStore[store_name]", dense_rank_desc(store_revenue))

    product_revenue = (
        sales.groupby("product_name")["revenue"].sum()
        .reindex(tables["dim_product"]["product_name"].unique(), fill_value=0)
    )
    grouped("Product Revenue Rank", "DimProduct[product_name]", dense_rank_desc(product_revenue))

    brand_profit = (
        sales.groupby("product_brand")["gross_product_profit"].sum()
        .reindex(tables["dim_product"]["product_brand"].unique(), fill_value=0)
    )
    grouped("Brand Profit Rank", "DimProduct[product_brand]", dense_rank_desc(brand_profit))

    store_quantity = sales.groupby("store_name")["quantity_sold"].sum()
    store_returns = returns.groupby("store_name")["return_quantity"].sum().reindex(store_quantity.index)
    # In DAX a blank return rate minus the network rate is a negative number,
    # and the review flag reports "No return data" for stores without returns.
    store_rate = store_returns.fillna(0) / store_quantity
    difference = (store_rate - network_rate) * 100
    grouped("Return Rate vs Overall (pp)", "DimStore[store_name]", difference)
    flags = pd.Series(
        np.select(
            [store_returns.isna(), difference >= 0.50, difference >= 0.15],
            ["No return data", "Review", "Watch"],
            "Within network range",
        ),
        index=difference.index,
    )
    grouped("Return Review Flag", "DimStore[store_name]", flags)

    product_quantity = sales.groupby("product_name")["quantity_sold"].sum()
    product_returns = returns.groupby("product_name")["return_quantity"].sum()
    product_rate = (product_returns.reindex(product_quantity.index) / product_quantity).where(
        product_quantity >= 300
    )
    grouped("Product Return Rate (300+ Units) %", "DimProduct[product_name]", product_rate)

    cumulative = ordered_customers["revenue"].cumsum() / ordered_customers["revenue"].sum()
    customer_count = len(ordered_customers)
    shares = pd.Series(
        {p: cumulative.iloc[math.ceil(customer_count * p / 100) - 1] for p in range(1, 101)}
    )
    grouped("Cumulative Customer Revenue Share %", "CustomerPercentile[Customer Percentile]", shares)
    return checks


# ---------------------------------------------------------------------------
# Engine access and comparison
# ---------------------------------------------------------------------------


def run_powershell(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Power BI engine call failed:\n{completed.stdout}\n{completed.stderr}")
    return completed.stdout


def run_engine(action: str, request: list[dict] | None = None) -> Any:
    command = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(ENGINE_SCRIPT), "-Action", action,
    ]
    if action != "query":
        return run_powershell(command)
    with tempfile.TemporaryDirectory() as temp:
        request_path = Path(temp) / "queries.json"
        result_path = Path(temp) / "results.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        run_powershell(command + ["-RequestPath", str(request_path), "-ResultPath", str(result_path)])
        return json.loads(result_path.read_text(encoding="utf-8"))


def to_number(value: str | None) -> float | None:
    return None if value is None else float(value)


def values_match(expected: Any, actual: str | None, tolerance: float = ABSOLUTE_TOLERANCE) -> tuple[bool, float | None]:
    if expected is None:
        return actual is None, None
    if isinstance(expected, str):
        return actual == expected, None
    if actual is None:
        return False, None
    difference = abs(float(actual) - float(expected))
    tolerance = max(tolerance, RELATIVE_TOLERANCE * abs(float(expected)))
    return difference <= tolerance, difference


def normalise_key(value: str) -> str:
    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else value
    except ValueError:
        return value


def compare(checks: list[Check], results: list[dict]) -> list[dict]:
    rows = []
    for check, result in zip(checks, results):
        base = {"measure": check.measure, "context": check.context, "source": check.source}
        tolerance = FIXED_DECIMAL_TOLERANCE if check.measure in FIXED_DECIMAL_RATIOS else ABSOLUTE_TOLERANCE
        if result["error"]:
            rows.append({**base, "expected": "", "actual": "", "max_abs_difference": "", "status": "error",
                         "detail": result["error"][:200]})
            continue
        if not check.grouped:
            actual = result["rows"][0][0] if result["rows"] else None
            ok, difference = values_match(check.expected, actual, tolerance)
            rows.append({
                **base,
                "expected": "" if check.expected is None else check.expected,
                "actual": "" if actual is None else actual,
                "max_abs_difference": "" if difference is None else f"{difference:.3g}",
                "status": "passed" if ok else "failed",
                "detail": "",
            })
            continue
        actual_map = {normalise_key(row[0]): row[1] for row in result["rows"] if row[1] is not None}
        expected_map = {normalise_key(k): v for k, v in check.expected.items()}
        mismatches, max_difference = [], 0.0
        for item in sorted(set(actual_map) | set(expected_map)):
            ok, difference = values_match(expected_map.get(item), actual_map.get(item), tolerance)
            if difference is not None:
                max_difference = max(max_difference, difference)
            if not ok:
                mismatches.append(item)
        rows.append({
            **base,
            "expected": f"{len(expected_map)} values",
            "actual": f"{len(actual_map)} values",
            "max_abs_difference": f"{max_difference:.3g}",
            "status": "passed" if not mismatches else "failed",
            "detail": "" if not mismatches else "mismatched: " + ", ".join(mismatches[:5]),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--refresh", action="store_true", help="Refresh the model before validating.")
    args = parser.parse_args()

    if args.refresh:
        print(run_engine("refresh"))
    snapshot = pd.read_csv(ROOT / "reports" / "kpi_baseline_snapshot.csv")
    checks = build_checks(snapshot, load_model())
    uncovered = sorted(set(MEASURE_METADATA) - {check.measure for check in checks})
    if uncovered:
        print(f"Measures without a validation check: {uncovered}")
        return 1

    results = run_engine("query", [{"id": str(i), "dax": c.dax} for i, c in enumerate(checks)])
    rows = compare(checks, results)
    frame = pd.DataFrame(rows)
    frame.to_csv(ROOT / "reports" / "power_bi_measure_validation.csv", index=False)
    summary = {
        "engine": "Power BI Desktop (local Analysis Services instance)",
        "measures_in_model": len(MEASURE_METADATA),
        "measures_validated": int(frame["measure"].nunique()),
        "checks": len(frame),
        "checks_against_kpi_snapshot": int((frame["source"] == "kpi_baseline_snapshot").sum()),
        "checks_against_model_csv": int((frame["source"] == "pandas_model_csv").sum()),
        "failed_checks": int((frame["status"] != "passed").sum()),
        "status": "passed" if (frame["status"] == "passed").all() else "failed",
    }
    (ROOT / "reports" / "power_bi_measure_validation.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    failures = frame.loc[frame["status"] != "passed"]
    if not failures.empty:
        print(failures.to_string(index=False))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
