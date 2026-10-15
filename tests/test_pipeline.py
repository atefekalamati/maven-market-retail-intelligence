"""Pipeline outputs: reconciliation, validation reports and the fixed price list."""

from __future__ import annotations

import json
import re

import pandas as pd
import pytest

from conftest import ROOT

EXPECTED_ROWS = {
    "dim_date": 737,
    "dim_customer": 10281,
    "dim_product": 1560,
    "dim_store": 24,
    "fact_sales": 269720,
    "fact_returns": 7087,
}


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_cleaning_validation_passed() -> None:
    checks = read_json("reports/cleaning_validation.json")
    assert all(value is True for value in checks.values() if isinstance(value, bool))
    assert checks["clean_missing_cells"] == 0


@pytest.mark.parametrize(
    "relative",
    [
        "reports/model_validation.json",
        "reports/eda_validation.json",
        "reports/kpi_validation.json",
        "reports/power_bi_measure_validation.json",
    ],
)
def test_stage_validation_passed(relative: str) -> None:
    assert read_json(relative)["status"] == "passed"


def test_model_row_counts(model_tables: dict[str, pd.DataFrame]) -> None:
    assert {name: len(frame) for name, frame in model_tables.items()} == EXPECTED_ROWS


def test_revenue_and_profit_reconcile(model_tables: dict[str, pd.DataFrame]) -> None:
    sales = model_tables["fact_sales"]
    assert round(sales["revenue"].sum(), 2) == 1_764_546.44
    assert round(sales["gross_product_profit"].sum(), 2) == 1_052_818.78
    assert round(sales["product_cost_amount"].sum(), 2) == 711_727.66


def test_kpi_snapshot_matches_model(model_tables: dict[str, pd.DataFrame]) -> None:
    snapshot = pd.read_csv(ROOT / "reports" / "kpi_baseline_snapshot.csv").set_index("metric_id")
    sales = model_tables["fact_sales"]
    assert snapshot.loc["total_revenue", "overall"] == pytest.approx(sales["revenue"].sum())
    assert snapshot.loc["active_customers", "overall"] == sales["customer_key"].nunique()
    assert snapshot.loc["returned_quantity", "overall"] == model_tables["fact_returns"]["return_quantity"].sum()


def test_price_and_cost_are_fixed_per_product(model_tables: dict[str, pd.DataFrame]) -> None:
    """Gross margin can only move with product mix: one price and one cost per product."""
    sales = model_tables["fact_sales"]
    distinct = sales.groupby("product_key")[["unit_retail_price", "unit_product_cost"]].nunique()
    assert distinct.max().tolist() == [1, 1]
    merged = sales.merge(model_tables["dim_product"], on="product_key")
    assert (merged["unit_retail_price"] == merged["product_retail_price"]).all()
    assert (merged["unit_product_cost"] == merged["product_cost"]).all()


def test_eda_summary_states_structural_margin() -> None:
    summary = read_json("reports/eda_summary.json")
    assert summary["max_retail_prices_per_product"] == 1
    assert summary["max_product_costs_per_product"] == 1
    text = (ROOT / "reports" / "eda_summary.md").read_text(encoding="utf-8")
    assert "property of the price list, not a business result" in text
    assert "Gross margin remained almost unchanged" not in text


def test_measure_validation_covers_every_measure() -> None:
    from build_power_bi_report import MEASURE_METADATA

    results = pd.read_csv(ROOT / "reports" / "power_bi_measure_validation.csv")
    assert set(results["measure"]) == set(MEASURE_METADATA)
    assert (results["status"] == "passed").all()
    assert (results["source"] == "kpi_baseline_snapshot").sum() > 0


RUN_TIMESTAMP = re.compile(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d")


def test_notebooks_have_no_run_metadata() -> None:
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for cell in notebook["cells"]:
            assert "execution" not in cell.get("metadata", {}), path.name
        assert not RUN_TIMESTAMP.search(path.read_text(encoding="utf-8")), path.name


def test_reports_have_no_run_timestamps() -> None:
    for path in sorted((ROOT / "reports").glob("*")):
        if path.suffix in {".json", ".csv", ".md"}:
            assert not RUN_TIMESTAMP.search(path.read_text(encoding="utf-8")), path.name


def test_dashboard_pdf_has_six_pages_and_no_creation_date() -> None:
    pymupdf = pytest.importorskip("pymupdf")
    document = pymupdf.open(ROOT / "dashboard" / "dashboard.pdf")
    assert document.page_count == 6
    assert document.metadata["creationDate"] == ""


def test_readme_links_and_images_exist() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)#]+)\)", readme)
    local = [t for t in targets if not t.startswith("http")]
    assert "images/dashboard/01_executive_overview.png" in local
    assert "dashboard/dashboard.pdf" in local
    for target in local:
        assert (ROOT / target).exists(), target
