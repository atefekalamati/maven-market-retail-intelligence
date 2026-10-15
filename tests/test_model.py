"""Semantic model (TMDL): structure, relationships, measures and reproducibility."""

from __future__ import annotations

import filecmp
import re
from pathlib import Path

import pandas as pd
import pytest

from conftest import DASHBOARD, MODEL_DIR, ROOT

import build_power_bi_report as builder

MODEL_TABLES = {
    "dim_date": "DimDate",
    "dim_customer": "DimCustomer",
    "dim_product": "DimProduct",
    "dim_store": "DimStore",
    "fact_sales": "FactSales",
    "fact_returns": "FactReturns",
}
TIMESTAMP = re.compile(r"20\d\d-\d\d-\d\d[T ]\d\d:\d\d|lastModified|createdAt", re.IGNORECASE)


def tables_by_name(summary: dict) -> dict[str, dict]:
    return {table["name"]: table for table in summary["tables"]}


def test_generator_output_is_committed_and_deterministic(tmp_path: Path) -> None:
    """Regenerating the project reproduces the committed files byte for byte."""
    output = tmp_path / "dashboard"
    output.mkdir()
    builder.build_project(ROOT, output, str(ROOT / "data" / "model"))

    def project_files(base: Path) -> list[Path]:
        return sorted(
            path.relative_to(base)
            for path in base.rglob("*")
            if path.is_file()
            and path.relative_to(base).parts[0].startswith("MavenMarket.")
            and ".pbi" not in path.parts
        )

    generated = project_files(output)
    assert project_files(DASHBOARD) == generated
    mismatched = [
        str(path) for path in generated
        if not filecmp.cmp(output / path, DASHBOARD / path, shallow=False)
    ]
    assert mismatched == []


def test_no_run_timestamps_in_project_files() -> None:
    for path in DASHBOARD.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".tmdl", ".pbir", ".pbism", ".pbip"} and ".pbi" not in path.parts:
            if "BaseThemes" in path.parts:
                continue
            assert not TIMESTAMP.search(path.read_text(encoding="utf-8")), path


def test_tmdl_parses_with_model_settings(tmdl_summary: dict) -> None:
    assert tmdl_summary["maxParallelismPerRefresh"] == 1
    assert tmdl_summary["annotations"]["__PBI_TimeIntelligenceEnabled"] == "0"
    assert tmdl_summary["culture"] == "en-US"
    assert tmdl_summary["discourageImplicitMeasures"] is True


def test_data_folder_parameter_feeds_every_import_table(tmdl_summary: dict) -> None:
    expressions = {e["name"]: e["expression"] for e in tmdl_summary["expressions"]}
    assert "IsParameterQuery = true" in expressions["DataFolder"]
    assert expressions["DataFolder"].split('"')[1].replace("\\", "/").endswith("data/model")
    for table in builder.TABLES:
        source = (MODEL_DIR / "definition" / "tables" / f"{table.name}.tmdl").read_text(encoding="utf-8")
        assert f'File.Contents(DataFolder & "\\{table.source_file}")' in source


def test_tables_match_model_csv_columns(tmdl_summary: dict, model_tables: dict[str, pd.DataFrame]) -> None:
    tables = tables_by_name(tmdl_summary)
    for csv_name, table_name in MODEL_TABLES.items():
        model_columns = [c["name"] for c in tables[table_name]["columns"]]
        assert model_columns[: len(model_tables[csv_name].columns)] == list(model_tables[csv_name].columns)


def test_dim_date_is_marked_as_date_table(tmdl_summary: dict) -> None:
    dim_date = tables_by_name(tmdl_summary)["DimDate"]
    assert dim_date["dataCategory"] == "Time"
    keys = [c["name"] for c in dim_date["columns"] if c["isKey"]]
    assert keys == ["date"]
    date_column = next(c for c in dim_date["columns"] if c["name"] == "date")
    assert date_column["dataType"] == "DateTime"


def test_sort_by_columns(tmdl_summary: dict) -> None:
    columns = {
        (t["name"], c["name"]): c["sortByColumn"]
        for t in tmdl_summary["tables"]
        for c in t["columns"]
    }
    assert columns[("DimDate", "month_short_name")] == "month_number"
    assert columns[("DimDate", "year_month")] == "year_month_sort"
    assert columns[("DimDate", "quarter")] == "quarter_number"
    assert columns[("DimCustomer", "member_card")] == "member_card_sort"


def test_relationships_match_documented_star_schema(tmdl_summary: dict) -> None:
    documented = pd.read_csv(ROOT / "reports" / "model_relationships.csv")
    expected = {
        (
            MODEL_TABLES[row.to_table], row.to_column,
            MODEL_TABLES[row.from_table], row.from_column,
            bool(row.active_in_power_bi),
        )
        for row in documented.itertuples()
    }
    actual = {
        (r["fromTable"], r["fromColumn"], r["toTable"], r["toColumn"], r["isActive"])
        for r in tmdl_summary["relationships"]
    }
    assert actual == expected
    for relationship in tmdl_summary["relationships"]:
        assert relationship["fromCardinality"] == "Many"
        assert relationship["toCardinality"] == "One"
        assert relationship["crossFilteringBehavior"] == "OneDirection"


def test_measures_match_dax_files(tmdl_summary: dict) -> None:
    measures = {m["name"]: m for m in tables_by_name(tmdl_summary)["_Measures"]["measures"]}
    dax = dict(builder.load_measures(ROOT))
    assert set(measures) == set(dax)
    for name, expression in dax.items():
        assert measures[name]["expression"].strip() == expression.strip(), name
        folder, format_string = builder.MEASURE_METADATA[name]
        assert measures[name]["displayFolder"] == folder
        if format_string:
            assert measures[name]["formatString"] == format_string


def test_measure_table_is_hidden_placeholder(tmdl_summary: dict) -> None:
    columns = tables_by_name(tmdl_summary)["_Measures"]["columns"]
    assert [(c["name"], c["isHidden"]) for c in columns] == [("Placeholder", True)]


@pytest.mark.parametrize("label", ["Reported Growth Label", "Same-Store Growth Label"])
def test_growth_labels_use_latest_year_measures(label: str) -> None:
    expression = dict(builder.load_measures(ROOT))[label]
    assert "Latest Year" in expression
