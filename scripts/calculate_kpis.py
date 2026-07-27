from __future__ import annotations

import json
import math
import os
from pathlib import Path

import pandas as pd


def resolve_roots() -> tuple[Path, Path]:
    """Resolve the project root and output root.

    Local usage expects the command to be run from the repository root.
    Environment variables are available for automated validation.
    """
    project_root = Path(os.getenv("MAVEN_MARKET_PROJECT_ROOT", Path.cwd())).resolve()
    output_root = Path(os.getenv("MAVEN_MARKET_OUTPUT_ROOT", project_root)).resolve()
    return project_root, output_root


def load_model_tables(project_root: Path) -> dict[str, pd.DataFrame]:
    model_dir = project_root / "data" / "model"
    required = {
        "sales": "fact_sales.csv",
        "returns": "fact_returns.csv",
        "date": "dim_date.csv",
        "customer": "dim_customer.csv",
        "product": "dim_product.csv",
        "store": "dim_store.csv",
    }

    missing = [name for name in required.values() if not (model_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Model files are missing. Run Stage 5 before Stage 7. Missing: "
            + ", ".join(missing)
        )

    return {
        alias: pd.read_csv(model_dir / filename)
        for alias, filename in required.items()
    }


def add_year_columns(tables: dict[str, pd.DataFrame]) -> None:
    date_map = tables["date"].set_index("date_key")["year"]
    tables["sales"]["year"] = tables["sales"]["transaction_date_key"].map(date_map)
    tables["returns"]["year"] = tables["returns"]["return_date_key"].map(date_map)


def top_share(sales: pd.DataFrame, group_column: str, fraction: float) -> float:
    revenue = sales.groupby(group_column, observed=True)["revenue"].sum().sort_values(ascending=False)
    count = max(1, math.ceil(len(revenue) * fraction))
    return float(revenue.head(count).sum() / revenue.sum())


def repeat_customer_stats(sales: pd.DataFrame) -> tuple[int, float]:
    purchase_days = sales.groupby("customer_key", observed=True)["transaction_date_key"].nunique()
    repeat_customers = int((purchase_days > 1).sum())
    rate = repeat_customers / len(purchase_days) if len(purchase_days) else 0.0
    return repeat_customers, float(rate)


def period_metrics(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    stores: pd.DataFrame,
) -> dict[str, float | int]:
    revenue = float(sales["revenue"].sum())
    cost = float(sales["product_cost_amount"].sum())
    profit = float(sales["gross_product_profit"].sum())
    quantity = int(sales["quantity_sold"].sum())
    sales_lines = int(len(sales))
    active_customers = int(sales["customer_key"].nunique())
    active_stores = int(sales["store_key"].nunique())
    active_products = int(sales["product_key"].nunique())
    returned_quantity = int(returns["return_quantity"].sum())

    active_store_keys = sales["store_key"].drop_duplicates()
    active_area = float(
        stores.loc[stores["store_key"].isin(active_store_keys), "total_sqft"].sum()
    )

    repeat_customers, repeat_rate = repeat_customer_stats(sales)
    top_product_revenue = float(
        sales.groupby("product_key", observed=True)["revenue"].sum().max()
    )

    return {
        "total_revenue": revenue,
        "total_product_cost": cost,
        "gross_product_profit": profit,
        "gross_margin_pct": profit / revenue,
        "quantity_sold": quantity,
        "sales_lines": sales_lines,
        "active_customers": active_customers,
        "active_stores": active_stores,
        "active_products": active_products,
        "returned_quantity": returned_quantity,
        "return_quantity_rate_pct": returned_quantity / quantity,
        "revenue_per_active_customer": revenue / active_customers,
        "profit_per_active_customer": profit / active_customers,
        "repeat_customers": repeat_customers,
        "repeat_customer_rate_pct": repeat_rate,
        "revenue_per_store": revenue / active_stores,
        "profit_per_store": profit / active_stores,
        "active_store_area_sqft": active_area,
        "revenue_per_sqft": revenue / active_area,
        "profit_per_sqft": profit / active_area,
        "average_revenue_per_sales_line": revenue / sales_lines,
        "average_units_per_sales_line": quantity / sales_lines,
        "top_10pct_customer_revenue_contribution_pct": top_share(
            sales, "customer_key", 0.10
        ),
        "top_product_revenue_contribution_pct": top_product_revenue / revenue,
    }


def build_snapshot(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sales = tables["sales"]
    returns = tables["returns"]
    stores = tables["store"]

    periods = {
        "Overall": period_metrics(sales, returns, stores),
        "1997": period_metrics(
            sales.loc[sales["year"] == 1997],
            returns.loc[returns["year"] == 1997],
            stores,
        ),
        "1998": period_metrics(
            sales.loc[sales["year"] == 1998],
            returns.loc[returns["year"] == 1998],
            stores,
        ),
    }

    periods["1998"]["revenue_growth_pct"] = (
        periods["1998"]["total_revenue"] / periods["1997"]["total_revenue"] - 1
    )
    periods["1998"]["profit_growth_pct"] = (
        periods["1998"]["gross_product_profit"]
        / periods["1997"]["gross_product_profit"]
        - 1
    )

    comparable_keys = set(
        stores.loc[stores["is_same_store_comparable"] == True, "store_key"]  # noqa: E712
    )
    comparable_sales = sales.loc[sales["store_key"].isin(comparable_keys)]
    comparable_returns = returns.loc[returns["store_key"].isin(comparable_keys)]
    same_store = {
        year: period_metrics(
            comparable_sales.loc[comparable_sales["year"] == year],
            comparable_returns.loc[comparable_returns["year"] == year],
            stores,
        )
        for year in (1997, 1998)
    }
    periods["1998"]["same_store_revenue_growth_pct"] = (
        same_store[1998]["total_revenue"] / same_store[1997]["total_revenue"] - 1
    )
    periods["1998"]["same_store_profit_growth_pct"] = (
        same_store[1998]["gross_product_profit"]
        / same_store[1997]["gross_product_profit"]
        - 1
    )

    display_order = [
        "total_revenue",
        "total_product_cost",
        "gross_product_profit",
        "gross_margin_pct",
        "revenue_growth_pct",
        "profit_growth_pct",
        "same_store_revenue_growth_pct",
        "same_store_profit_growth_pct",
        "quantity_sold",
        "sales_lines",
        "active_customers",
        "active_stores",
        "active_products",
        "returned_quantity",
        "return_quantity_rate_pct",
        "revenue_per_active_customer",
        "profit_per_active_customer",
        "repeat_customers",
        "repeat_customer_rate_pct",
        "revenue_per_store",
        "profit_per_store",
        "revenue_per_sqft",
        "profit_per_sqft",
        "average_revenue_per_sales_line",
        "average_units_per_sales_line",
        "top_10pct_customer_revenue_contribution_pct",
        "top_product_revenue_contribution_pct",
    ]

    rows = []
    for metric in display_order:
        rows.append(
            {
                "metric_id": metric,
                "overall": periods["Overall"].get(metric),
                "1997": periods["1997"].get(metric),
                "1998": periods["1998"].get(metric),
            }
        )
    return pd.DataFrame(rows)


def kpi_dictionary() -> pd.DataFrame:
    rows = [
        {
            "group": "Executive",
            "metric_id": "total_revenue",
            "name_en": "Total Revenue",
            "name_fa": "درآمد کل",
            "business_definition": "Sales value generated from units sold at retail price.",
            "formula": "SUM(FactSales[revenue])",
            "required_fields": "FactSales.revenue",
            "python_expression": "sales['revenue'].sum()",
            "dax_measure": "[Total Revenue]",
            "dashboard_display": "Primary KPI card; currency",
            "management_interpretation": "Shows business scale for the selected period and filters.",
            "limitation": "Revenue is not cash collected and does not include tax information.",
        },
        {
            "group": "Executive",
            "metric_id": "gross_product_profit",
            "name_en": "Gross Product Profit",
            "name_fa": "سود ناخالص محصول",
            "business_definition": "Revenue remaining after product cost.",
            "formula": "Total Revenue - Total Product Cost",
            "required_fields": "FactSales.gross_product_profit",
            "python_expression": "sales['gross_product_profit'].sum()",
            "dax_measure": "[Gross Product Profit]",
            "dashboard_display": "Primary KPI card; currency",
            "management_interpretation": "Tracks the value generated before store and corporate operating expenses.",
            "limitation": "This is not net profit because payroll, rent, marketing and other operating costs are unavailable.",
        },
        {
            "group": "Executive",
            "metric_id": "gross_margin_pct",
            "name_en": "Gross Margin %",
            "name_fa": "حاشیه سود ناخالص",
            "business_definition": "Share of revenue retained after product cost.",
            "formula": "Gross Product Profit / Total Revenue",
            "required_fields": "FactSales.revenue; FactSales.gross_product_profit",
            "python_expression": "sales['gross_product_profit'].sum() / sales['revenue'].sum()",
            "dax_measure": "[Gross Margin %]",
            "dashboard_display": "Primary KPI card; percentage",
            "management_interpretation": "Separates growth in sales volume from improvement in unit economics.",
            "limitation": "Stable gross margin does not imply stable net margin.",
        },
        {
            "group": "Executive",
            "metric_id": "revenue_growth_pct",
            "name_en": "Reported Revenue Growth %",
            "name_fa": "رشد گزارش‌شده درآمد",
            "business_definition": "Change in total revenue versus the previous year using all active stores.",
            "formula": "(Current Revenue - Previous Year Revenue) / Previous Year Revenue",
            "required_fields": "FactSales.revenue; DimDate.date",
            "python_expression": "revenue_1998 / revenue_1997 - 1",
            "dax_measure": "[Revenue Growth %]",
            "dashboard_display": "KPI card beside same-store growth",
            "management_interpretation": "Shows total network growth, including the effect of newly active stores.",
            "limitation": "The 1997 and 1998 store bases differ, so this is not an organic-growth measure.",
        },
        {
            "group": "Executive",
            "metric_id": "same_store_revenue_growth_pct",
            "name_en": "Same-Store Revenue Growth %",
            "name_fa": "رشد درآمد فروشگاه‌های همسان",
            "business_definition": "Revenue growth for the 13 stores with sales in both years.",
            "formula": "(Comparable Revenue CY - Comparable Revenue PY) / Comparable Revenue PY",
            "required_fields": "FactSales.revenue; DimDate.date; DimStore.is_same_store_comparable",
            "python_expression": "same_store_revenue_1998 / same_store_revenue_1997 - 1",
            "dax_measure": "[Same-Store Revenue Growth %]",
            "dashboard_display": "Primary growth card; percentage",
            "management_interpretation": "Provides a cleaner view of organic performance than reported growth.",
            "limitation": "The comparable-store flag is fixed for this two-year dataset and should be redesigned for longer histories.",
        },
        {
            "group": "Executive",
            "metric_id": "quantity_sold",
            "name_en": "Quantity Sold",
            "name_fa": "تعداد کالای فروخته‌شده",
            "business_definition": "Total units sold in the selected context.",
            "formula": "SUM(FactSales[quantity_sold])",
            "required_fields": "FactSales.quantity_sold",
            "python_expression": "sales['quantity_sold'].sum()",
            "dax_measure": "[Quantity Sold]",
            "dashboard_display": "Secondary KPI card or trend",
            "management_interpretation": "Helps distinguish volume growth from price and product-mix effects.",
            "limitation": "Units from different products are counted equally regardless of value or weight.",
        },
        {
            "group": "Executive",
            "metric_id": "active_customers",
            "name_en": "Active Customers",
            "name_fa": "مشتریان فعال",
            "business_definition": "Distinct customers with at least one sales line in the selected period.",
            "formula": "DISTINCTCOUNT(FactSales[customer_key])",
            "required_fields": "FactSales.customer_key",
            "python_expression": "sales['customer_key'].nunique()",
            "dax_measure": "[Active Customers]",
            "dashboard_display": "Secondary KPI card",
            "management_interpretation": "Shows the size of the purchasing customer base.",
            "limitation": "The dataset does not distinguish acquisition source or customer status outside observed purchases.",
        },
        {
            "group": "Executive",
            "metric_id": "return_quantity_rate_pct",
            "name_en": "Return Quantity Rate %",
            "name_fa": "نرخ مقداری مرجوعی",
            "business_definition": "Returned units divided by sold units for the same visible product, store and date context.",
            "formula": "Returned Quantity / Quantity Sold",
            "required_fields": "FactReturns.return_quantity; FactSales.quantity_sold; shared dimensions",
            "python_expression": "returns['return_quantity'].sum() / sales['quantity_sold'].sum()",
            "dax_measure": "[Return Quantity Rate %]",
            "dashboard_display": "Guardrail KPI and alert visual",
            "management_interpretation": "Highlights products or stores that may require quality or process review.",
            "limitation": "Returns cannot be matched to the original sale or customer; do not use this KPI by customer.",
        },
        {
            "group": "Operational",
            "metric_id": "total_product_cost",
            "name_en": "Total Product Cost",
            "name_fa": "هزینه کل محصول",
            "business_definition": "Cost of units sold based on product unit cost.",
            "formula": "SUM(FactSales[product_cost_amount])",
            "required_fields": "FactSales.product_cost_amount",
            "python_expression": "sales['product_cost_amount'].sum()",
            "dax_measure": "[Total Product Cost]",
            "dashboard_display": "Supporting KPI or tooltip",
            "management_interpretation": "Explains the cost side of gross product profit.",
            "limitation": "Excludes inventory carrying cost and operating expenses.",
        },
        {
            "group": "Operational",
            "metric_id": "sales_lines",
            "name_en": "Sales Lines",
            "name_fa": "ردیف‌های فروش",
            "business_definition": "Number of sales records at the product-customer-store-date grain.",
            "formula": "COUNTROWS(FactSales)",
            "required_fields": "FactSales.sales_line_key",
            "python_expression": "len(sales)",
            "dax_measure": "[Sales Lines]",
            "dashboard_display": "Operational KPI or tooltip",
            "management_interpretation": "Measures transaction-line activity, not the number of customer orders.",
            "limitation": "There is no order ID, so this must never be labelled Total Orders.",
        },
        {
            "group": "Operational",
            "metric_id": "revenue_per_active_customer",
            "name_en": "Revenue per Active Customer",
            "name_fa": "درآمد به‌ازای مشتری فعال",
            "business_definition": "Average revenue generated per purchasing customer.",
            "formula": "Total Revenue / Active Customers",
            "required_fields": "FactSales.revenue; FactSales.customer_key",
            "python_expression": "sales['revenue'].sum() / sales['customer_key'].nunique()",
            "dax_measure": "[Revenue per Active Customer]",
            "dashboard_display": "Customer KPI card or membership comparison",
            "management_interpretation": "Compares customer value across periods and segments.",
            "limitation": "This is period revenue per active customer, not customer lifetime value.",
        },
        {
            "group": "Operational",
            "metric_id": "repeat_customer_rate_pct",
            "name_en": "Repeat Customer Rate %",
            "name_fa": "نرخ مشتریان تکرارشونده",
            "business_definition": "Share of active customers purchasing on more than one distinct date in the selected period.",
            "formula": "Repeat Customers / Active Customers",
            "required_fields": "FactSales.customer_key; FactSales.transaction_date_key",
            "python_expression": "(sales.groupby('customer_key')['transaction_date_key'].nunique() > 1).mean()",
            "dax_measure": "[Repeat Customer Rate %]",
            "dashboard_display": "Customer KPI; use at month, quarter or year level",
            "management_interpretation": "Indicates whether the active customer base returns within the measured period.",
            "limitation": "The value is sensitive to the selected date window and will be zero at a single-day grain.",
        },
        {
            "group": "Operational",
            "metric_id": "revenue_per_store",
            "name_en": "Revenue per Active Store",
            "name_fa": "درآمد به‌ازای فروشگاه فعال",
            "business_definition": "Average revenue across stores with sales in the selected period.",
            "formula": "Total Revenue / Active Stores",
            "required_fields": "FactSales.revenue; FactSales.store_key",
            "python_expression": "sales['revenue'].sum() / sales['store_key'].nunique()",
            "dax_measure": "[Revenue per Active Store]",
            "dashboard_display": "Store summary KPI",
            "management_interpretation": "Normalizes total revenue for changes in the number of active stores.",
            "limitation": "Average store performance can hide large differences by format and location.",
        },
        {
            "group": "Operational",
            "metric_id": "revenue_per_sqft",
            "name_en": "Revenue per Square Foot",
            "name_fa": "درآمد به‌ازای فوت مربع",
            "business_definition": "Revenue divided by total floor area of stores active in the selected period.",
            "formula": "Total Revenue / Active Store Area",
            "required_fields": "FactSales.revenue; DimStore.total_sqft",
            "python_expression": "sales['revenue'].sum() / active_store_area",
            "dax_measure": "[Revenue per Square Foot]",
            "dashboard_display": "Store efficiency KPI and ranked bar",
            "management_interpretation": "Compares how efficiently stores use their physical footprint.",
            "limitation": "The available floor-area value is static and does not reflect temporary closures or layout changes within a period.",
        },
        {
            "group": "Operational",
            "metric_id": "profit_per_sqft",
            "name_en": "Gross Profit per Square Foot",
            "name_fa": "سود ناخالص به‌ازای فوت مربع",
            "business_definition": "Gross product profit divided by total floor area of active stores.",
            "formula": "Gross Product Profit / Active Store Area",
            "required_fields": "FactSales.gross_product_profit; DimStore.total_sqft",
            "python_expression": "sales['gross_product_profit'].sum() / active_store_area",
            "dax_measure": "[Gross Profit per Square Foot]",
            "dashboard_display": "Store efficiency KPI or scatter axis",
            "management_interpretation": "Balances store productivity with product margin.",
            "limitation": "Does not include store operating expenses, so it is not store-level net profit per square foot.",
        },
        {
            "group": "Operational",
            "metric_id": "average_revenue_per_sales_line",
            "name_en": "Average Revenue per Sales Line",
            "name_fa": "میانگین درآمد هر ردیف فروش",
            "business_definition": "Average revenue per recorded product sales line.",
            "formula": "Total Revenue / Sales Lines",
            "required_fields": "FactSales.revenue; FactSales.sales_line_key",
            "python_expression": "sales['revenue'].sum() / len(sales)",
            "dax_measure": "[Average Revenue per Sales Line]",
            "dashboard_display": "Tooltip or detailed operational KPI",
            "management_interpretation": "Tracks changes in value at the available sales-line grain.",
            "limitation": "This is not Average Order Value because the dataset has no order identifier.",
        },
        {
            "group": "Operational",
            "metric_id": "top_10pct_customer_revenue_contribution_pct",
            "name_en": "Top 10% Customer Revenue Contribution %",
            "name_fa": "سهم درآمد ۱۰٪ مشتریان برتر",
            "business_definition": "Share of revenue generated by the highest-revenue 10% of active customers.",
            "formula": "Revenue from top 10% active customers / Total Revenue",
            "required_fields": "FactSales.customer_key; FactSales.revenue",
            "python_expression": "top_10_percent_customer_revenue / total_revenue",
            "dax_measure": "[Top 10% Customer Revenue Contribution %]",
            "dashboard_display": "Concentration KPI or Pareto view",
            "management_interpretation": "Shows how dependent revenue is on the highest-value customer group.",
            "limitation": "The customer set changes with filters, so comparisons need the same period and segment definition.",
        },
        {
            "group": "Operational",
            "metric_id": "top_product_revenue_contribution_pct",
            "name_en": "Top Product Revenue Contribution %",
            "name_fa": "سهم درآمد محصول برتر",
            "business_definition": "Revenue share generated by the single highest-revenue product.",
            "formula": "Top Product Revenue / Total Revenue",
            "required_fields": "FactSales.product_key; FactSales.revenue",
            "python_expression": "sales.groupby('product_key')['revenue'].sum().max() / sales['revenue'].sum()",
            "dax_measure": "[Top Product Revenue Contribution %]",
            "dashboard_display": "Product concentration KPI or tooltip",
            "management_interpretation": "Identifies whether revenue depends heavily on one product.",
            "limitation": "A low share does not prove a healthy assortment; category and brand concentration should also be reviewed.",
        },
    ]
    return pd.DataFrame(rows)


def validate(snapshot: pd.DataFrame) -> dict[str, object]:
    indexed = snapshot.set_index("metric_id")
    checks = {
        "overall_revenue_matches_model": abs(
            float(indexed.loc["total_revenue", "overall"]) - 1_764_546.44
        ) < 0.01,
        "overall_profit_matches_model": abs(
            float(indexed.loc["gross_product_profit", "overall"]) - 1_052_818.78
        ) < 0.01,
        "overall_quantity_matches_model": int(
            indexed.loc["quantity_sold", "overall"]
        ) == 833_489,
        "reported_growth_exceeds_same_store_growth": float(
            indexed.loc["revenue_growth_pct", "1998"]
        ) > float(indexed.loc["same_store_revenue_growth_pct", "1998"]),
        "return_rate_is_between_zero_and_one": 0 <= float(
            indexed.loc["return_quantity_rate_pct", "overall"]
        ) <= 1,
        "gross_margin_is_between_zero_and_one": 0 <= float(
            indexed.loc["gross_margin_pct", "overall"]
        ) <= 1,
        "no_metric_definition_duplicates": kpi_dictionary()["metric_id"].is_unique,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "notes": [
            "No target values were created because the dataset contains no budget, plan or management threshold.",
            "Order count and average order value are excluded because the source has no order identifier.",
            "Return Quantity Rate must not be analysed by customer because FactReturns has no customer key.",
        ],
    }


def write_outputs(output_root: Path, snapshot: pd.DataFrame, dictionary: pd.DataFrame) -> None:
    reports_dir = output_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    snapshot.to_csv(reports_dir / "kpi_baseline_snapshot.csv", index=False)
    dictionary.to_csv(reports_dir / "kpi_dictionary.csv", index=False)
    validation = validate(snapshot)
    (reports_dir / "kpi_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )


def main() -> None:
    project_root, output_root = resolve_roots()
    tables = load_model_tables(project_root)
    add_year_columns(tables)
    snapshot = build_snapshot(tables)
    dictionary = kpi_dictionary()
    write_outputs(output_root, snapshot, dictionary)

    validation = json.loads((output_root / "reports" / "kpi_validation.json").read_text())
    print("KPI calculation completed successfully.")
    print(f"KPI definitions: {len(dictionary):,}")
    print(f"Validation status: {validation['status']}")


if __name__ == "__main__":
    main()
