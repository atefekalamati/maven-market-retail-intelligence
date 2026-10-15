"""Report (PBIR): schemas and the layout rules for every page and visual."""

from __future__ import annotations

import itertools
import json
import re
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from conftest import DASHBOARD, ROOT

import build_power_bi_report as builder

SCHEMA_PREFIX = "https://developer.microsoft.com/json-schemas/"
SCHEMA_DIR = ROOT / "tests" / "schemas"
PROJECT_JSON = [
    path
    for pattern in ("*.pbip", "**/*.pbir", "**/*.pbism", "**/definition/**/*.json")
    for path in DASHBOARD.glob(pattern)
    if ".pbi" not in path.parts
]
RETURN_RATE_MEASURE = "Return Quantity Rate %"
# Average Segoe UI glyph width as a share of the font size (measured in Power BI
# Desktop at about 0.46), used to check that text fits its box.
CHAR_WIDTH_RATIO = 0.5
POINTS_TO_PIXELS = 4 / 3


def literal(value: dict):
    return value["expr"]["Literal"]["Value"]


def visual_text(visual: dict) -> list[str]:
    """All user-facing strings of a visual: titles, text runs and field labels."""
    texts = []
    body = visual.get("visual", {})
    for paragraph in body.get("objects", {}).get("general", [{}])[0].get("properties", {}).get("paragraphs", []):
        texts += [run["value"] for run in paragraph["textRuns"]]
    for name in ("title", "subTitle"):
        for entry in body.get("visualContainerObjects", {}).get(name, []):
            if "text" in entry["properties"]:
                texts.append(literal(entry["properties"]["text"]).strip("'"))
    for role in body.get("query", {}).get("queryState", {}).values():
        texts += [p.get("displayName", p["nativeQueryRef"]) for p in role["projections"]]
    return texts


def kinds(page: dict, prefix: str) -> list[dict]:
    return [v for v in page["visuals"] if v["name"].startswith(prefix)]


@pytest.fixture(scope="module")
def registry() -> Registry:
    def retrieve(uri: str) -> Resource:
        path = SCHEMA_DIR / uri[len(SCHEMA_PREFIX):]
        return Resource.from_contents(json.loads(path.read_text(encoding="utf-8")))

    return Registry(retrieve=retrieve)


@pytest.mark.parametrize("path", PROJECT_JSON, ids=lambda p: str(p.relative_to(DASHBOARD)))
def test_files_match_pbir_schemas(path: Path, registry: Registry) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    schema = registry.get_or_retrieve(document["$schema"]).value.contents
    validator_class = jsonschema.validators.validator_for(schema)
    errors = sorted(validator_class(schema, registry=registry).iter_errors(document), key=str)
    assert not errors, [f"{list(e.absolute_path)}: {e.message[:200]}" for e in errors[:5]]


def test_report_has_six_pages_in_design_order(pages: list[dict]) -> None:
    assert [p["page"]["displayName"] for p in pages] == [name for _, name, _ in builder.PAGES]
    for page in pages:
        assert (page["page"]["width"], page["page"]["height"]) == (1280, 720)


def test_every_page_has_title_finding_and_source_footer(pages: list[dict]) -> None:
    for page in pages:
        names = {v["name"] for v in page["visuals"]}
        assert {"title", "finding", "footer"} <= names
        title = visual_text(next(v for v in page["visuals"] if v["name"] == "title"))
        assert title == [page["page"]["displayName"]]
        finding = visual_text(next(v for v in page["visuals"] if v["name"] == "finding"))
        assert len(finding) == 1 and "\n" not in finding[0]
        finding_box = next(v for v in page["visuals"] if v["name"] == "finding")["position"]
        assert len(finding[0]) * 11 * POINTS_TO_PIXELS * CHAR_WIDTH_RATIO <= finding_box["width"] - 16
        footer = visual_text(next(v for v in page["visuals"] if v["name"] == "footer"))
        assert footer[0].startswith("Source:")


def test_visuals_stay_on_canvas(pages: list[dict]) -> None:
    for page in pages:
        for visual in page["visuals"]:
            p = visual["position"]
            assert p["x"] >= 0 and p["y"] >= 0, visual["name"]
            assert p["x"] + p["width"] <= page["page"]["width"], visual["name"]
            assert p["y"] + p["height"] <= page["page"]["height"], visual["name"]


def test_no_visuals_overlap(pages: list[dict]) -> None:
    for page in pages:
        for a, b in itertools.combinations(page["visuals"], 2):
            pa, pb = a["position"], b["position"]
            overlap_x = min(pa["x"] + pa["width"], pb["x"] + pb["width"]) - max(pa["x"], pb["x"])
            overlap_y = min(pa["y"] + pa["height"], pb["y"] + pb["height"]) - max(pa["y"], pb["y"])
            assert overlap_x <= 0 or overlap_y <= 0, (page["page"]["name"], a["name"], b["name"])


def test_cards_use_20pt_values_and_unclipped_9pt_labels(pages: list[dict]) -> None:
    cards = [v for page in pages for v in page["visuals"] if v["visual"]["visualType"] == "card"]
    assert cards
    for card in cards:
        objects = card["visual"]["objects"]
        assert literal(objects["labels"][0]["properties"]["fontSize"]) == "20D"
        assert literal(objects["categoryLabels"][0]["properties"]["fontSize"]) == "9D"
        assert literal(objects["categoryLabels"][0]["properties"]["show"]) == "true"
        label = card["visual"]["query"]["queryState"]["Values"]["projections"][0]["displayName"]
        label_width = len(label) * 9 * POINTS_TO_PIXELS * CHAR_WIDTH_RATIO
        assert label_width <= card["position"]["width"] - 24, card["name"]
        # 20pt value + 9pt label + padding, verified in Power BI Desktop.
        assert card["position"]["height"] >= 80, card["name"]


def test_tables_and_matrices_have_no_totals_and_fit(pages: list[dict]) -> None:
    tables = [
        v for page in pages for v in page["visuals"]
        if v["visual"]["visualType"] in {"tableEx", "pivotTable"}
    ]
    assert tables
    for table in tables:
        objects = table["visual"]["objects"]
        if table["visual"]["visualType"] == "tableEx":
            assert literal(objects["total"][0]["properties"]["totals"]) == "false"
        else:
            assert literal(objects["subTotals"][0]["properties"]["rowSubtotals"]) == "false"
            assert literal(objects["subTotals"][0]["properties"]["columnSubtotals"]) == "false"
        widths = [literal(w["properties"]["value"]) for w in objects["columnWidth"]]
        total_width = sum(float(w.rstrip("D")) for w in widths)
        assert total_width <= table["position"]["width"] - 40, table["name"]
        headers = [p["displayName"] for p in table["visual"]["query"]["queryState"]["Values"]["projections"]]
        for header, width in zip(headers, widths):
            assert len(header) * 9 * POINTS_TO_PIXELS * CHAR_WIDTH_RATIO <= float(width.rstrip("D")) - 8, header
        top = [f for f in table["filterConfig"]["filters"] if f["type"] == "TopN"]
        assert top, "tables must limit their rows so they fit without a scrollbar"
        rows = top[0]["filter"]["From"][0]["Expression"]["Subquery"]["Query"]["Top"]
        # Title 30 px, header 24 px and 20 px per row at 9pt, verified in Desktop.
        assert 30 + 24 + rows * 20 + 16 <= table["position"]["height"], table["name"]


def test_bar_charts_fit_without_scrollbars(pages: list[dict], model_tables) -> None:
    category_counts = {
        "DimStore.store_country": model_tables["dim_store"]["store_country"].nunique(),
        "DimStore.sales_region": model_tables["dim_store"]["sales_region"].nunique(),
        "DimStore.store_type": model_tables["dim_store"]["store_type"].nunique(),
    }
    for page in pages:
        for visual in page["visuals"]:
            if visual["visual"]["visualType"] != "clusteredBarChart":
                continue
            assert visual["position"]["height"] >= builder.ROW_HEIGHT
            axis = visual["visual"]["objects"]["categoryAxis"][0]["properties"]
            assert literal(axis["preferredCategoryWidth"]) == f"{builder.BAR_CATEGORY_WIDTH}D"
            top = [f for f in visual.get("filterConfig", {}).get("filters", []) if f["type"] == "TopN"]
            if top:
                count = top[0]["filter"]["From"][0]["Expression"]["Subquery"]["Query"]["Top"]
            else:
                category = visual["visual"]["query"]["queryState"]["Category"]["projections"][0]["queryRef"]
                count = category_counts[category]
            assert count <= builder.MAX_BARS, visual["name"]


def test_return_rate_is_labelled_as_proxy(pages: list[dict]) -> None:
    for page in pages:
        for visual in page["visuals"]:
            for role in visual.get("visual", {}).get("query", {}).get("queryState", {}).values():
                for projection in role["projections"]:
                    if projection["nativeQueryRef"] in {RETURN_RATE_MEASURE, "Product Return Rate (300+ Units) %"}:
                        assert projection.get("displayName") == "Return rate (proxy)", visual["name"]
            for text in visual_text(visual):
                for match in re.finditer(r"return rates?\b", text, re.IGNORECASE):
                    assert text[match.end():].startswith(" (proxy)"), (visual["name"], text)


def test_conditional_colours_use_fx_rules(pages: list[dict]) -> None:
    rule_visuals = []
    for page in pages:
        for visual in page["visuals"]:
            serialized = json.dumps(visual["visual"].get("objects", {}))
            if '"Conditional"' in serialized:
                rule_visuals.append(visual["name"])
                assert '"Return Rate vs Overall (pp)"' in serialized
                assert '"ComparisonKind": 2' in serialized
    assert {"pr04_product_return_risk", "re02_store_return_rate", "re03_product_return_risk",
            "re04_return_detail"} <= set(rule_visuals)


def test_visual_headers_hidden_and_navigation_complete(pages: list[dict]) -> None:
    page_names = [p["page"]["name"] for p in pages]
    for page in pages:
        for visual in page["visuals"]:
            header = visual["visual"].get("visualContainerObjects", {}).get("visualHeader")
            assert header and literal(header[0]["properties"]["show"]) == "false", visual["name"]
        targets = [
            literal(v["visual"]["visualContainerObjects"]["visualLink"][0]["properties"]["navigationSection"]).strip("'")
            for v in kinds(page, "nav_")
        ]
        assert targets == page_names


def test_global_slicers_on_every_page(pages: list[dict]) -> None:
    for page in pages:
        fields = sorted(
            v["visual"]["query"]["queryState"]["Values"]["projections"][0]["queryRef"]
            for v in page["visuals"] if v["visual"]["visualType"] == "slicer"
        )
        assert fields == ["DimDate.year", "DimStore.sales_region", "DimStore.store_country"]


def test_report_text_is_english(pages: list[dict]) -> None:
    non_latin = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
    for page in pages:
        assert not non_latin.search(page["page"]["displayName"])
        for visual in page["visuals"]:
            for text in visual_text(visual):
                assert not non_latin.search(text), (visual["name"], text)


def test_returns_page_is_drillthrough_target(pages: list[dict]) -> None:
    returns = next(p for p in pages if p["page"]["name"] == "p06_returns_detail")["page"]
    assert returns["pageBinding"]["type"] == "Drillthrough"
    fields = {f["field"]["Column"]["Property"] for f in returns["filterConfig"]["filters"]}
    assert fields == {"store_name", "product_name"}
