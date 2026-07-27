from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_model_tables(project_root: Path) -> dict[str, pd.DataFrame]:
    model_dir = project_root / "data" / "model"
    required_files = {
        "fact_sales": "fact_sales.csv",
        "fact_returns": "fact_returns.csv",
        "dim_date": "dim_date.csv",
        "dim_customer": "dim_customer.csv",
        "dim_product": "dim_product.csv",
        "dim_store": "dim_store.csv",
    }

    missing = [name for name in required_files.values() if not (model_dir / name).exists()]
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing model files: {missing_text}. Run scripts/build_star_schema.py first."
        )

    tables = {
        name: pd.read_csv(model_dir / filename)
        for name, filename in required_files.items()
    }

    tables["dim_date"]["date"] = pd.to_datetime(tables["dim_date"]["date"])
    return tables


def build_analysis_views(tables: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = tables["fact_sales"].merge(
        tables["dim_date"][
            [
                "date_key",
                "date",
                "year",
                "quarter",
                "month_number",
                "month_name",
                "year_month",
                "is_weekend",
            ]
        ],
        left_on="transaction_date_key",
        right_on="date_key",
        how="left",
        validate="many_to_one",
    )
    sales = sales.merge(
        tables["dim_product"], on="product_key", how="left", validate="many_to_one"
    )
    sales = sales.merge(
        tables["dim_customer"], on="customer_key", how="left", validate="many_to_one"
    )
    sales = sales.merge(
        tables["dim_store"], on="store_key", how="left", validate="many_to_one"
    )

    returns = tables["fact_returns"].merge(
        tables["dim_date"][
            ["date_key", "date", "year", "quarter", "month_number", "month_name", "year_month"]
        ],
        left_on="return_date_key",
        right_on="date_key",
        how="left",
        validate="many_to_one",
    )
    returns = returns.merge(
        tables["dim_product"], on="product_key", how="left", validate="many_to_one"
    )
    returns = returns.merge(
        tables["dim_store"], on="store_key", how="left", validate="many_to_one"
    )

    return sales, returns


def make_output_directories(project_root: Path) -> tuple[Path, Path]:
    reports_dir = project_root / "reports"
    images_dir = project_root / "images" / "eda"
    reports_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir, images_dir


def calculate_tables(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    dim_store: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    annual = (
        sales.groupby("year", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
            active_stores=("store_key", "nunique"),
            sales_lines=("sales_line_key", "count"),
        )
        .sort_values("year")
    )
    annual["gross_margin_pct"] = (
        annual["gross_product_profit"] / annual["revenue"] * 100
    )
    annual["revenue_growth_pct"] = annual["revenue"].pct_change() * 100
    annual["profit_growth_pct"] = annual["gross_product_profit"].pct_change() * 100
    annual["quantity_growth_pct"] = annual["quantity_sold"].pct_change() * 100

    same_store_keys = dim_store.loc[
        dim_store["is_same_store_comparable"], "store_key"
    ]
    same_store = (
        sales.loc[sales["store_key"].isin(same_store_keys)]
        .groupby("year", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
            active_stores=("store_key", "nunique"),
        )
        .sort_values("year")
    )
    same_store["gross_margin_pct"] = (
        same_store["gross_product_profit"] / same_store["revenue"] * 100
    )
    same_store["revenue_growth_pct"] = same_store["revenue"].pct_change() * 100
    same_store["profit_growth_pct"] = (
        same_store["gross_product_profit"].pct_change() * 100
    )
    same_store["quantity_growth_pct"] = same_store["quantity_sold"].pct_change() * 100

    monthly = (
        sales.groupby(
            ["year", "month_number", "month_name", "year_month"], as_index=False
        )
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
            active_stores=("store_key", "nunique"),
        )
        .sort_values(["year", "month_number"])
    )
    monthly["gross_margin_pct"] = (
        monthly["gross_product_profit"] / monthly["revenue"] * 100
    )

    store_all = (
        sales.groupby(
            [
                "store_key",
                "store_name",
                "store_type",
                "store_country",
                "sales_region",
                "total_sqft",
                "grocery_sqft",
                "is_same_store_comparable",
            ],
            as_index=False,
        )
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
            active_days=("date", "nunique"),
        )
    )
    store_all["gross_margin_pct"] = (
        store_all["gross_product_profit"] / store_all["revenue"] * 100
    )
    store_all["revenue_per_sqft"] = store_all["revenue"] / store_all["total_sqft"]
    store_all["profit_per_sqft"] = (
        store_all["gross_product_profit"] / store_all["total_sqft"]
    )

    store_1998 = (
        sales.loc[sales["year"] == 1998]
        .groupby(
            [
                "store_key",
                "store_name",
                "store_type",
                "store_country",
                "sales_region",
                "total_sqft",
                "grocery_sqft",
            ],
            as_index=False,
        )
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
            active_days=("date", "nunique"),
        )
    )
    store_1998["gross_margin_pct"] = (
        store_1998["gross_product_profit"] / store_1998["revenue"] * 100
    )
    store_1998["revenue_per_sqft"] = store_1998["revenue"] / store_1998["total_sqft"]
    store_1998["profit_per_sqft"] = (
        store_1998["gross_product_profit"] / store_1998["total_sqft"]
    )

    brand = (
        sales.groupby("product_brand", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            products=("product_key", "nunique"),
        )
    )
    brand["gross_margin_pct"] = brand["gross_product_profit"] / brand["revenue"] * 100
    brand["revenue_share_pct"] = brand["revenue"] / brand["revenue"].sum() * 100

    customer_segment = (
        sales.groupby("member_card", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            active_customers=("customer_key", "nunique"),
        )
    )
    customer_segment["revenue_per_customer"] = (
        customer_segment["revenue"] / customer_segment["active_customers"]
    )
    customer_segment["gross_margin_pct"] = (
        customer_segment["gross_product_profit"] / customer_segment["revenue"] * 100
    )

    customer = (
        sales.groupby("customer_key", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            gross_product_profit=("gross_product_profit", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            shopping_days=("date", "nunique"),
        )
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    customer["customer_rank"] = np.arange(1, len(customer) + 1)
    customer["customer_percentile"] = customer["customer_rank"] / len(customer) * 100
    customer["cumulative_revenue_share_pct"] = (
        customer["revenue"].cumsum() / customer["revenue"].sum() * 100
    )

    sold_by_store = sales.groupby("store_key")["quantity_sold"].sum().rename("quantity_sold")
    returned_by_store = (
        returns.groupby("store_key")["return_quantity"].sum().rename("return_quantity")
    )
    store_returns = (
        pd.concat([sold_by_store, returned_by_store], axis=1)
        .fillna(0)
        .reset_index()
        .merge(
            dim_store[
                ["store_key", "store_name", "store_type", "store_country", "sales_region"]
            ],
            on="store_key",
            how="left",
            validate="one_to_one",
        )
    )
    store_returns["return_rate_pct"] = (
        store_returns["return_quantity"] / store_returns["quantity_sold"] * 100
    )

    sold_by_product = sales.groupby("product_key")["quantity_sold"].sum().rename("quantity_sold")
    returned_by_product = (
        returns.groupby("product_key")["return_quantity"].sum().rename("return_quantity")
    )
    product_returns = (
        pd.concat([sold_by_product, returned_by_product], axis=1)
        .fillna(0)
        .reset_index()
        .merge(
            sales[["product_key", "product_brand", "product_name"]].drop_duplicates(),
            on="product_key",
            how="left",
            validate="one_to_one",
        )
    )
    product_returns["return_rate_pct"] = (
        product_returns["return_quantity"] / product_returns["quantity_sold"] * 100
    )

    return {
        "annual_performance": annual,
        "same_store_performance": same_store,
        "monthly_performance": monthly,
        "store_performance": store_all,
        "store_performance_1998": store_1998,
        "brand_performance": brand,
        "customer_segment_performance": customer_segment,
        "customer_concentration": customer,
        "store_return_rates": store_returns,
        "product_return_rates": product_returns,
    }


def create_charts(tables: dict[str, pd.DataFrame], images_dir: Path) -> list[str]:
    chart_files: list[str] = []

    monthly = tables["monthly_performance"].copy()
    plt.figure(figsize=(11, 6))
    plt.plot(monthly["year_month"], monthly["revenue"], marker="o", label="Revenue")
    plt.plot(
        monthly["year_month"],
        monthly["gross_product_profit"],
        marker="o",
        label="Gross product profit",
    )
    plt.title("Monthly revenue and gross product profit")
    plt.xlabel("Month")
    plt.ylabel("Amount")
    plt.xticks(rotation=60)
    plt.legend()
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "01_monthly_revenue_profit.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    annual = tables["annual_performance"]
    same_store = tables["same_store_performance"]
    labels = ["Revenue", "Gross profit", "Quantity"]
    reported = [
        annual.iloc[-1]["revenue_growth_pct"],
        annual.iloc[-1]["profit_growth_pct"],
        annual.iloc[-1]["quantity_growth_pct"],
    ]
    comparable = [
        same_store.iloc[-1]["revenue_growth_pct"],
        same_store.iloc[-1]["profit_growth_pct"],
        same_store.iloc[-1]["quantity_growth_pct"],
    ]
    positions = np.arange(len(labels))
    width = 0.36
    plt.figure(figsize=(9, 6))
    plt.bar(positions - width / 2, reported, width, label="Reported growth")
    plt.bar(positions + width / 2, comparable, width, label="Same-store growth")
    plt.axhline(0, linewidth=0.8)
    plt.title("1998 growth: reported versus same-store")
    plt.ylabel("Growth (%)")
    plt.xticks(positions, labels)
    plt.legend()
    for x, value in zip(positions - width / 2, reported):
        plt.text(x, value + 2, f"{value:.1f}%", ha="center")
    for x, value in zip(positions + width / 2, comparable):
        plt.text(x, value + 2, f"{value:.1f}%", ha="center")
    plt.tight_layout()
    path = images_dir / "02_reported_vs_same_store_growth.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    store_1998 = tables["store_performance_1998"].copy()
    plt.figure(figsize=(9, 6))
    plt.scatter(store_1998["total_sqft"], store_1998["revenue"])
    for _, row in store_1998.iterrows():
        plt.annotate(
            row["store_name"].replace("Store ", ""),
            (row["total_sqft"], row["revenue"]),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=8,
        )
    plt.title("Store size and revenue in 1998")
    plt.xlabel("Total store area (sq ft)")
    plt.ylabel("Revenue")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    path = images_dir / "03_store_size_vs_revenue_1998.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    top_stores = store_1998.nlargest(10, "revenue").sort_values("revenue")
    plt.figure(figsize=(9, 6))
    plt.barh(top_stores["store_name"], top_stores["revenue"])
    plt.title("Top stores by revenue in 1998")
    plt.xlabel("Revenue")
    plt.ylabel("Store")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "04_top_stores_revenue_1998.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    top_brands = tables["brand_performance"].nlargest(10, "revenue").sort_values("revenue")
    plt.figure(figsize=(9, 6))
    plt.barh(top_brands["product_brand"], top_brands["revenue"])
    plt.title("Top product brands by revenue")
    plt.xlabel("Revenue")
    plt.ylabel("Brand")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "05_top_brands_revenue.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    concentration = tables["customer_concentration"]
    plt.figure(figsize=(9, 6))
    plt.plot(
        concentration["customer_percentile"],
        concentration["cumulative_revenue_share_pct"],
    )
    plt.plot([0, 100], [0, 100], linestyle="--", label="Equal distribution")
    plt.title("Cumulative revenue by active customer percentile")
    plt.xlabel("Cumulative share of active customers (%)")
    plt.ylabel("Cumulative share of revenue (%)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    path = images_dir / "06_customer_revenue_concentration.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    member = tables["customer_segment_performance"].sort_values("revenue_per_customer")
    plt.figure(figsize=(8, 5))
    plt.barh(member["member_card"], member["revenue_per_customer"])
    plt.title("Revenue per active customer by membership level")
    plt.xlabel("Revenue per active customer")
    plt.ylabel("Membership level")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "07_member_card_revenue_per_customer.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    store_returns = tables["store_return_rates"].nlargest(10, "return_rate_pct").sort_values(
        "return_rate_pct"
    )
    plt.figure(figsize=(9, 6))
    plt.barh(store_returns["store_name"], store_returns["return_rate_pct"])
    plt.title("Stores with the highest return-rate proxy")
    plt.xlabel("Returned quantity / sold quantity (%)")
    plt.ylabel("Store")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "08_store_return_rate.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    product_returns = tables["product_return_rates"]
    product_returns = product_returns.loc[product_returns["quantity_sold"] >= 300]
    top_product_returns = product_returns.nlargest(10, "return_rate_pct").sort_values(
        "return_rate_pct"
    )
    plt.figure(figsize=(11, 6))
    plt.barh(top_product_returns["product_name"], top_product_returns["return_rate_pct"])
    plt.title("Products with the highest return-rate proxy (minimum 300 units sold)")
    plt.xlabel("Returned quantity / sold quantity (%)")
    plt.ylabel("Product")
    plt.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    path = images_dir / "09_product_return_risk.png"
    plt.savefig(path, dpi=160)
    plt.close()
    chart_files.append(str(path))

    return chart_files


def build_summary(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
) -> dict[str, float | int | str]:
    annual = tables["annual_performance"]
    same_store = tables["same_store_performance"]
    monthly = tables["monthly_performance"]
    store_1998 = tables["store_performance_1998"]
    member = tables["customer_segment_performance"]
    customer = tables["customer_concentration"]
    store_returns = tables["store_return_rates"]
    product_returns = tables["product_return_rates"]

    top_10_count = max(1, int(np.ceil(len(customer) * 0.10)))
    top_20_count = max(1, int(np.ceil(len(customer) * 0.20)))
    top_10_share = customer.head(top_10_count)["revenue"].sum() / customer["revenue"].sum() * 100
    top_20_share = customer.head(top_20_count)["revenue"].sum() / customer["revenue"].sum() * 100

    monthly_1998 = monthly.loc[monthly["year"] == 1998]
    december_1998 = monthly_1998.loc[monthly_1998["month_number"] == 12, "revenue"].iloc[0]
    average_month_1998 = monthly_1998["revenue"].mean()

    size_revenue_corr = store_1998[["total_sqft", "revenue"]].corr().iloc[0, 1]
    highest_store = store_1998.nlargest(1, "revenue").iloc[0]
    highest_product_return = product_returns.loc[product_returns["quantity_sold"] >= 300].nlargest(
        1, "return_rate_pct"
    ).iloc[0]
    highest_store_return = store_returns.nlargest(1, "return_rate_pct").iloc[0]
    highest_member = member.nlargest(1, "revenue_per_customer").iloc[0]
    lowest_member = member.nsmallest(1, "revenue_per_customer").iloc[0]

    total_revenue = float(sales["revenue"].sum())
    total_profit = float(sales["gross_product_profit"].sum())
    total_quantity = int(sales["quantity_sold"].sum())
    total_return_quantity = int(returns["return_quantity"].sum())

    return {
        "total_revenue": total_revenue,
        "total_gross_product_profit": total_profit,
        "gross_margin_pct": total_profit / total_revenue * 100,
        "quantity_sold": total_quantity,
        "return_quantity": total_return_quantity,
        "return_rate_proxy_pct": total_return_quantity / total_quantity * 100,
        "active_customers": int(sales["customer_key"].nunique()),
        "active_stores": int(sales["store_key"].nunique()),
        "reported_revenue_growth_1998_pct": float(annual.iloc[-1]["revenue_growth_pct"]),
        "same_store_revenue_growth_1998_pct": float(same_store.iloc[-1]["revenue_growth_pct"]),
        "reported_profit_growth_1998_pct": float(annual.iloc[-1]["profit_growth_pct"]),
        "same_store_profit_growth_1998_pct": float(same_store.iloc[-1]["profit_growth_pct"]),
        "stores_1997": int(annual.iloc[0]["active_stores"]),
        "stores_1998": int(annual.iloc[-1]["active_stores"]),
        "december_1998_revenue": float(december_1998),
        "december_1998_vs_monthly_average_pct": float(
            (december_1998 / average_month_1998 - 1) * 100
        ),
        "store_size_revenue_correlation_1998": float(size_revenue_corr),
        "top_store_1998": str(highest_store["store_name"]),
        "top_store_1998_revenue": float(highest_store["revenue"]),
        "top_10_customer_revenue_share_pct": float(top_10_share),
        "top_20_customer_revenue_share_pct": float(top_20_share),
        "highest_revenue_per_customer_membership": str(highest_member["member_card"]),
        "highest_membership_revenue_per_customer": float(highest_member["revenue_per_customer"]),
        "lowest_revenue_per_customer_membership": str(lowest_member["member_card"]),
        "lowest_membership_revenue_per_customer": float(lowest_member["revenue_per_customer"]),
        "highest_store_return_rate_store": str(highest_store_return["store_name"]),
        "highest_store_return_rate_pct": float(highest_store_return["return_rate_pct"]),
        "highest_product_return_rate_product": str(highest_product_return["product_name"]),
        "highest_product_return_rate_pct": float(highest_product_return["return_rate_pct"]),
    }


def write_outputs(
    project_root: Path,
    tables: dict[str, pd.DataFrame],
    summary: dict[str, float | int | str],
    chart_files: list[str],
) -> None:
    reports_dir, _ = make_output_directories(project_root)

    csv_outputs = {
        "annual_performance.csv": tables["annual_performance"],
        "same_store_performance.csv": tables["same_store_performance"],
        "monthly_performance.csv": tables["monthly_performance"],
        "store_performance.csv": tables["store_performance"],
        "store_performance_1998.csv": tables["store_performance_1998"],
        "brand_performance.csv": tables["brand_performance"].sort_values(
            "revenue", ascending=False
        ),
        "customer_segment_performance.csv": tables["customer_segment_performance"].sort_values(
            "revenue", ascending=False
        ),
        "customer_concentration.csv": tables["customer_concentration"],
        "store_return_rates.csv": tables["store_return_rates"].sort_values(
            "return_rate_pct", ascending=False
        ),
        "product_return_rates.csv": tables["product_return_rates"].sort_values(
            "return_rate_pct", ascending=False
        ),
    }
    for filename, dataframe in csv_outputs.items():
        dataframe.to_csv(reports_dir / filename, index=False)

    with (reports_dir / "eda_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    validation = {
        "status": "passed",
        "checks": {
            "sales_rows_preserved": int(tables["annual_performance"]["sales_lines"].sum()) == 269720,
            "revenue_reconciles": round(summary["total_revenue"], 2) == 1764546.44,
            "profit_reconciles": round(summary["total_gross_product_profit"], 2) == 1052818.78,
            "quantity_reconciles": summary["quantity_sold"] == 833489,
            "all_expected_charts_created": len(chart_files) == 9,
            "annual_periods_present": len(tables["annual_performance"]) == 2,
            "all_1998_stores_present": len(tables["store_performance_1998"]) == 24,
        },
        "generated_charts": [Path(path).name for path in chart_files],
    }
    validation["status"] = (
        "passed" if all(validation["checks"].values()) else "failed"
    )
    with (reports_dir / "eda_validation.json").open("w", encoding="utf-8") as file:
        json.dump(validation, file, indent=2)

    report = f"""# Exploratory Data Analysis Summary

## Scope

This analysis uses the validated star-schema tables produced in the previous stage. Sales and returns are analysed separately because the return table does not contain a customer key or a transaction identifier that can be matched back to an individual sale.

## Headline metrics

| Metric | Result |
|---|---:|
| Revenue | ${summary['total_revenue']:,.2f} |
| Gross product profit | ${summary['total_gross_product_profit']:,.2f} |
| Gross margin | {summary['gross_margin_pct']:.2f}% |
| Quantity sold | {summary['quantity_sold']:,} |
| Active customers | {summary['active_customers']:,} |
| Active stores | {summary['active_stores']} |
| Returned quantity | {summary['return_quantity']:,} |
| Return-rate proxy | {summary['return_rate_proxy_pct']:.2f}% |

## Findings

### 1. Most of the reported 1998 growth came from store expansion

Reported revenue increased by **{summary['reported_revenue_growth_1998_pct']:.1f}%** in 1998, while revenue from the 13 stores active in both years increased by **{summary['same_store_revenue_growth_1998_pct']:.1f}%**. The store count moved from **{summary['stores_1997']}** to **{summary['stores_1998']}**. The total growth figure is valid, but it should not be presented as organic growth.

![Reported versus same-store growth](../images/eda/02_reported_vs_same_store_growth.png)

### 2. Gross margin remained almost unchanged

Gross margin stayed close to **{summary['gross_margin_pct']:.2f}%** across the period. Revenue and profit moved at nearly the same rate, which suggests that the improvement came mainly from higher sales volume and wider store coverage rather than a change in product margin.

### 3. The end of 1998 was the strongest part of the period

December 1998 generated **${summary['december_1998_revenue']:,.2f}** in revenue, **{summary['december_1998_vs_monthly_average_pct']:.1f}%** above the 1998 monthly average. November was also stronger than most earlier months. This pattern is useful for staffing and inventory planning, but the dataset contains only two years, so it is not enough to establish a long-term seasonal rule.

![Monthly revenue and profit](../images/eda/01_monthly_revenue_profit.png)

### 4. Store size was not a useful predictor of revenue

The correlation between total store area and 1998 revenue was **{summary['store_size_revenue_correlation_1998']:.2f}**. The relationship is weak and slightly negative. **{summary['top_store_1998']}** produced the highest 1998 revenue at **${summary['top_store_1998_revenue']:,.2f}**, but several larger stores performed below it. Store format, location and local demand appear more useful than floor area alone.

![Store size and revenue](../images/eda/03_store_size_vs_revenue_1998.png)

### 5. Customer revenue is concentrated, but not dependent on a very small group

The top 10% of active customers generated **{summary['top_10_customer_revenue_share_pct']:.1f}%** of revenue, and the top 20% generated **{summary['top_20_customer_revenue_share_pct']:.1f}%**. This supports targeted retention work, while also showing that the wider customer base still contributes a material share.

![Customer concentration](../images/eda/06_customer_revenue_concentration.png)

### 6. Golden members had the highest revenue per active customer

Golden members averaged **${summary['highest_membership_revenue_per_customer']:,.2f}** in revenue per active customer. Silver members were lowest at **${summary['lowest_membership_revenue_per_customer']:,.2f}**. Membership levels are associated with different customer value, but the data does not show programme costs, benefits or causal impact.

![Membership performance](../images/eda/07_member_card_revenue_per_customer.png)

### 7. Returns were low overall but concentrated in a few products and stores

Returned quantity was **{summary['return_rate_proxy_pct']:.2f}%** of sold quantity overall. **{summary['highest_store_return_rate_store']}** had the highest store-level proxy at **{summary['highest_store_return_rate_pct']:.2f}%**. Among products with at least 300 units sold, **{summary['highest_product_return_rate_product']}** had the highest proxy at **{summary['highest_product_return_rate_pct']:.2f}%**.

The ratio is a monitoring proxy, not a matched return rate, because returns cannot be linked to the original sales transaction.

![Store return-rate proxy](../images/eda/08_store_return_rate.png)

## Recommended dashboard emphasis

- Show reported growth and same-store growth together.
- Keep gross margin next to revenue and profit so expansion is not mistaken for better unit economics.
- Rank stores by both revenue and revenue per square foot.
- Add a customer concentration view and membership-level comparison.
- Use the return-rate proxy as an operational alert, with a visible methodology note.

## Analytical limits

- No order identifier is available, so order count and average order value cannot be calculated.
- Returns cannot be matched to a customer or sales line.
- Gross product profit excludes operating expenses and is not net profit.
- No discount, inventory, marketing campaign or sales-target data is available.
- Two years of history are not enough for robust forecasting or long-term seasonality claims.
"""
    (reports_dir / "eda_summary.md").write_text(report, encoding="utf-8")


def run_eda(project_root: str | Path = ".") -> dict[str, float | int | str]:
    root = Path(project_root).resolve()
    tables = load_model_tables(root)
    sales, returns = build_analysis_views(tables)
    reports_dir, images_dir = make_output_directories(root)
    analysis_tables = calculate_tables(sales, returns, tables["dim_store"])
    chart_files = create_charts(analysis_tables, images_dir)
    summary = build_summary(sales, returns, analysis_tables)
    write_outputs(root, analysis_tables, summary, chart_files)

    print("EDA completed successfully.")
    print(f"Validation file: {reports_dir / 'eda_validation.json'}")
    print(f"Charts created: {len(chart_files)}")
    return summary


if __name__ == "__main__":
    run_eda(Path.cwd())
