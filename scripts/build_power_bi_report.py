"""Generate the Maven Market Power BI project (.pbip) from the Stage 8 design.

Run from the repository root:
    python scripts/build_power_bi_report.py

The script writes a TMDL semantic model and a PBIR report to dashboard/:

    dashboard/MavenMarket.pbip
    dashboard/MavenMarket.SemanticModel/
    dashboard/MavenMarket.Report/

Measures are read from dax/07_kpi_measures.dax and dax/08_dashboard_measures.dax,
so the DAX files remain the single source of truth. Page findings are read from
the validated EDA outputs in reports/. Output is deterministic: identifiers are
derived from names and no run timestamps are written.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_NAME = "MavenMarket"
SCHEMA_ROOT = "https://developer.microsoft.com/json-schemas/fabric/"
SCHEMAS = {
    "pbip": SCHEMA_ROOT + "pbip/pbipProperties/1.0.0/schema.json",
    "pbir": SCHEMA_ROOT + "item/report/definitionProperties/2.0.0/schema.json",
    "pbism": SCHEMA_ROOT + "item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": SCHEMA_ROOT + "item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": SCHEMA_ROOT + "item/report/definition/report/3.3.0/schema.json",
    "pages": SCHEMA_ROOT + "item/report/definition/pagesMetadata/1.0.0/schema.json",
    "page": SCHEMA_ROOT + "item/report/definition/page/2.1.0/schema.json",
    "visual": SCHEMA_ROOT + "item/report/definition/visualContainer/2.10.0/schema.json",
}
THEME_VERSION = {"visual": "2.10.0", "report": "3.3.0", "page": "2.1.0"}
BASE_THEME = "Fluent2-CY26SU08"
BASE_THEME_SOURCE = Path(
    r"C:\Program Files\Microsoft Power BI Desktop\bin\WebView2Resources"
    r"\minerva\sharedresources\BaseThemes"
)
LINEAGE_NAMESPACE = uuid.UUID("6f1d3c2a-5b7e-4f0a-9c8d-2e4b6a8c0d1e")

# Canvas and layout grid (pixels). See docs/08_power_bi_dashboard.md.
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
MARGIN = 32
GAP = 14
CONTENT_WIDTH = CANVAS_WIDTH - 2 * MARGIN
TITLE_Y, TITLE_HEIGHT = 8, 40
SUBTITLE_Y, SUBTITLE_HEIGHT = 50, 40
SLICER_Y, SLICER_HEIGHT, SLICER_WIDTH = 46, 48, 186
NAV_Y, NAV_HEIGHT, NAV_WIDTH, NAV_GAP = 10, 30, 92, 6
CARD_Y, CARD_HEIGHT = 100, 80
ROW_A_Y, ROW_B_Y, ROW_HEIGHT = 192, 442, 238
FOOTER_Y, FOOTER_HEIGHT = 690, 22
WIDE_WIDTH = 760
NARROW_WIDTH = CONTENT_WIDTH - WIDE_WIDTH - GAP
HALF_WIDTH = (CONTENT_WIDTH - GAP) // 2

# Theme colours (dashboard/maven_market_power_bi_theme.json).
TEAL = "#0F766E"
BLUE = "#2563EB"
GOLD = "#D97706"
SLATE = "#64748B"
DARK_RED = "#B91C1C"
INK = "#0F172A"
INK_SECONDARY = "#334155"
BORDER = "#E2E8F0"
WHITE = "#FFFFFF"
PAGE_BACKGROUND = "#F8FAFC"

# Power BI Desktop accepts a category width of 20-180 px. At the minimum,
# a 238 px chart with a title and subtitle shows seven bars without scrolling.
BAR_CATEGORY_WIDTH = 20
BAR_INNER_PADDING = 10
MAX_BARS = 7
DETAIL_TABLE_ROWS = 6
CARD_VALUE_SIZE = 20
CARD_LABEL_SIZE = 9
RETURN_RATE_LABEL = "Return rate (proxy)"

# Return-rate rules: difference from the network rate in percentage points,
# matching the thresholds of [Return Review Flag] in dax/08.
RETURN_RATE_RULES = [(0.50, DARK_RED), (0.15, GOLD)]
RETURN_RATE_RULE_DEFAULT = SLATE


# ---------------------------------------------------------------------------
# Semantic model definition
# ---------------------------------------------------------------------------

# (column, TMDL data type, Power Query type, format string, hidden)
TEXT, WHOLE, DECIMAL, DOUBLE, DATE, BOOL = (
    ("string", "type text"),
    ("int64", "Int64.Type"),
    ("decimal", "Currency.Type"),
    ("double", "type number"),
    ("dateTime", "type date"),
    ("boolean", "type logical"),
)
CURRENCY_FORMAT = "\\$#,0.00;-\\$#,0.00;\\$#,0.00"
DATE_FORMAT = "yyyy-mm-dd"


@dataclass
class Column:
    name: str
    kind: tuple[str, str]
    format_string: str | None = None
    hidden: bool = False
    sort_by: str | None = None
    is_key: bool = False
    data_category: str | None = None


@dataclass
class Table:
    name: str
    source_file: str
    columns: list[Column]
    data_category: str | None = None
    added_columns: list[tuple[str, str]] = field(default_factory=list)


def col(name: str, kind: tuple[str, str], **kwargs: Any) -> Column:
    if "format_string" not in kwargs:
        if kind == WHOLE:
            kwargs["format_string"] = "#,0"
        elif kind == DECIMAL:
            kwargs["format_string"] = CURRENCY_FORMAT
        elif kind == DATE:
            kwargs["format_string"] = DATE_FORMAT
    return Column(name, kind, **kwargs)


def key(name: str) -> Column:
    return Column(name, WHOLE, format_string="0", hidden=True)


TABLES = [
    Table(
        "DimDate",
        "dim_date.csv",
        [
            col("date_key", WHOLE, format_string="0", hidden=True),
            col("date", DATE, is_key=True),
            col("year", WHOLE, format_string="0"),
            col("quarter_number", WHOLE, format_string="0", hidden=True),
            col("quarter", TEXT, sort_by="quarter_number"),
            col("month_number", WHOLE, format_string="0", hidden=True),
            col("month_name", TEXT, sort_by="month_number"),
            col("month_short_name", TEXT, sort_by="month_number"),
            col("year_month", TEXT, sort_by="year_month_sort"),
            col("year_month_sort", WHOLE, format_string="0", hidden=True),
            col("iso_week_number", WHOLE, format_string="0"),
            col("day_of_month", WHOLE, format_string="0"),
            col("day_name", TEXT, sort_by="day_of_week_number"),
            col("day_of_week_number", WHOLE, format_string="0", hidden=True),
            col("is_weekend", BOOL),
        ],
        data_category="Time",
    ),
    Table(
        "DimCustomer",
        "dim_customer.csv",
        [
            key("customer_key"),
            col("customer_id", WHOLE, format_string="0"),
            col("customer_acct_num", TEXT),
            col("customer_full_name", TEXT),
            col("first_name", TEXT),
            col("last_name", TEXT),
            col("last_name_missing", BOOL),
            col("customer_city", TEXT, data_category="City"),
            col("customer_state_province", TEXT, data_category="StateOrProvince"),
            col("customer_postal_code", TEXT, data_category="PostalCode"),
            col("customer_country", TEXT, data_category="Country"),
            col("birthdate", DATE),
            col("birth_year", WHOLE, format_string="0"),
            col("marital_status", TEXT),
            col("yearly_income", TEXT, sort_by="income_band_sort"),
            col("gender", TEXT),
            col("total_children", WHOLE),
            col("num_children_at_home", WHOLE),
            col("education", TEXT),
            col("acct_open_date", DATE),
            col("account_open_year", WHOLE, format_string="0"),
            col("member_card", TEXT, sort_by="member_card_sort"),
            col("occupation", TEXT),
            col("is_homeowner", BOOL),
            col("member_card_sort", WHOLE, format_string="0", hidden=True),
            col("income_band_sort", WHOLE, format_string="0", hidden=True),
        ],
        added_columns=[
            (
                "member_card_sort",
                'each if [member_card] = "Normal" then 1 else if [member_card] = "Bronze" '
                'then 2 else if [member_card] = "Silver" then 3 else if [member_card] = "Golden" '
                "then 4 else 5, Int64.Type",
            ),
            (
                "income_band_sort",
                'each Number.From(Text.BetweenDelimiters([yearly_income], "$", "K")), Int64.Type',
            ),
        ],
    ),
    Table(
        "DimProduct",
        "dim_product.csv",
        [
            key("product_key"),
            col("product_id", WHOLE, format_string="0"),
            col("product_brand", TEXT),
            col("product_name", TEXT),
            col("product_sku", TEXT),
            col("product_retail_price", DECIMAL),
            col("product_cost", DECIMAL),
            col("unit_gross_profit", DECIMAL),
            col("unit_margin_pct", DOUBLE, format_string="0.00"),
            col("unit_markup_pct", DOUBLE, format_string="0.00"),
            col("product_weight", DOUBLE, format_string="0.00"),
            col("is_recyclable", BOOL),
            col("is_low_fat", BOOL),
        ],
    ),
    Table(
        "DimStore",
        "dim_store.csv",
        [
            key("store_key"),
            col("store_id", WHOLE, format_string="0", hidden=True),
            col("store_name", TEXT, sort_by="store_id"),
            col("store_type", TEXT),
            col("store_city", TEXT, data_category="City"),
            col("store_state", TEXT, data_category="StateOrProvince"),
            col("store_country", TEXT, data_category="Country"),
            col("first_opened_date", DATE),
            col("last_remodel_date", DATE),
            col("total_sqft", WHOLE),
            col("grocery_sqft", WHOLE),
            col("non_grocery_sqft", WHOLE),
            col("grocery_share_pct", DOUBLE, format_string="0.00"),
            col("region_id", WHOLE, format_string="0"),
            col("sales_district", TEXT),
            col("sales_region", TEXT),
            col("is_same_store_comparable", BOOL),
        ],
    ),
    Table(
        "FactSales",
        "fact_sales.csv",
        [
            key("sales_line_key"),
            col("transaction_line_id", TEXT),
            key("transaction_date_key"),
            key("stock_date_key"),
            key("product_key"),
            key("customer_key"),
            key("store_key"),
            col("quantity_sold", WHOLE),
            col("unit_retail_price", DECIMAL),
            col("unit_product_cost", DECIMAL),
            col("revenue", DECIMAL),
            col("product_cost_amount", DECIMAL),
            col("gross_product_profit", DECIMAL),
            col("source_year", WHOLE, format_string="0"),
            key("source_row_number"),
            col("duplicate_candidate", BOOL),
        ],
    ),
    Table(
        "FactReturns",
        "fact_returns.csv",
        [
            key("return_line_key"),
            col("return_line_id", TEXT),
            key("return_date_key"),
            key("product_key"),
            key("store_key"),
            col("return_quantity", WHOLE),
            key("source_row_number"),
            col("duplicate_candidate", BOOL),
        ],
    ),
]

# (from table, from column, to table, to column, active)
RELATIONSHIPS = [
    ("FactSales", "transaction_date_key", "DimDate", "date_key", True),
    ("FactSales", "stock_date_key", "DimDate", "date_key", False),
    ("FactReturns", "return_date_key", "DimDate", "date_key", True),
    ("FactSales", "customer_key", "DimCustomer", "customer_key", True),
    ("FactSales", "product_key", "DimProduct", "product_key", True),
    ("FactReturns", "product_key", "DimProduct", "product_key", True),
    ("FactSales", "store_key", "DimStore", "store_key", True),
    ("FactReturns", "store_key", "DimStore", "store_key", True),
]

PERCENTILE_TABLE = "CustomerPercentile"
PERCENTILE_COLUMN = "Customer Percentile"
PERCENTILE_EXPRESSION = (
    'SELECTCOLUMNS(GENERATESERIES(1, 100, 1), "Customer Percentile", [Value])'
)
MEASURE_TABLE = "_Measures"

PERCENT = "0.0%"
GROWTH = "+0.0%;-0.0%;0.0%"
COUNT = "#,0"
RANK = "0"
MEASURE_METADATA: dict[str, tuple[str, str | None]] = {
    "Total Revenue": ("01 Base", CURRENCY_FORMAT),
    "Total Product Cost": ("01 Base", CURRENCY_FORMAT),
    "Gross Product Profit": ("01 Base", CURRENCY_FORMAT),
    "Gross Margin %": ("01 Base", PERCENT),
    "Quantity Sold": ("01 Base", COUNT),
    "Sales Lines": ("01 Base", COUNT),
    "Active Customers": ("01 Base", COUNT),
    "Active Stores": ("01 Base", COUNT),
    "Active Products": ("01 Base", COUNT),
    "Revenue Previous Year": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Revenue Growth %": ("02 Time Intelligence", GROWTH),
    "Profit Previous Year": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Profit Growth %": ("02 Time Intelligence", GROWTH),
    "Same-Store Revenue": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Same-Store Revenue Previous Year": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Same-Store Revenue Growth %": ("02 Time Intelligence", GROWTH),
    "Same-Store Profit": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Same-Store Profit Previous Year": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Same-Store Profit Growth %": ("02 Time Intelligence", GROWTH),
    "Revenue YTD": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Gross Profit YTD": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Revenue Previous Month": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Revenue MoM Growth %": ("02 Time Intelligence", GROWTH),
    "Gross Profit Previous Month": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Gross Profit MoM Growth %": ("02 Time Intelligence", GROWTH),
    "Revenue Running Total": ("02 Time Intelligence", CURRENCY_FORMAT),
    "Latest Year Revenue Growth %": ("02 Time Intelligence", GROWTH),
    "Latest Year Same-Store Revenue Growth %": ("02 Time Intelligence", GROWTH),
    "Revenue per Active Customer": ("03 Customer", CURRENCY_FORMAT),
    "Profit per Active Customer": ("03 Customer", CURRENCY_FORMAT),
    "Repeat Customers": ("03 Customer", COUNT),
    "Repeat Customer Rate %": ("03 Customer", PERCENT),
    "Top 10% Customer Revenue": ("03 Customer", CURRENCY_FORMAT),
    "Top 10% Customer Revenue Contribution %": ("03 Customer", PERCENT),
    "Cumulative Customer Revenue Share %": ("03 Customer", PERCENT),
    "Visible Customer Count": ("03 Customer", COUNT),
    "Average Revenue per Sales Line": ("04 Product", CURRENCY_FORMAT),
    "Average Units per Sales Line": ("04 Product", "0.00"),
    "Top Product Revenue": ("04 Product", CURRENCY_FORMAT),
    "Top Product Revenue Contribution %": ("04 Product", "0.00%"),
    "Product Revenue Rank": ("04 Product", RANK),
    "Brand Profit Rank": ("04 Product", RANK),
    "Visible Product Count": ("04 Product", COUNT),
    "Revenue per Active Store": ("05 Store", CURRENCY_FORMAT),
    "Profit per Active Store": ("05 Store", CURRENCY_FORMAT),
    "Active Store Area": ("05 Store", COUNT),
    "Revenue per Square Foot": ("05 Store", CURRENCY_FORMAT),
    "Gross Profit per Square Foot": ("05 Store", CURRENCY_FORMAT),
    "Store Revenue Rank": ("05 Store", RANK),
    "Visible Store Count": ("05 Store", COUNT),
    "Comparable Stores": ("05 Store", COUNT),
    "Returned Quantity": ("06 Returns", COUNT),
    "Return Quantity Rate %": ("06 Returns", PERCENT),
    "Return Rate vs Overall (pp)": ("06 Returns", "+0.00;-0.00;0.00"),
    "Return Review Flag": ("06 Returns", None),
    "Return Lines": ("06 Returns", COUNT),
    "Returned Products": ("06 Returns", COUNT),
    "Product Return Rate (300+ Units) %": ("06 Returns", PERCENT),
    "Selected Date Range": ("07 Display", None),
    "Selected Geography": ("07 Display", None),
    "Executive Page Subtitle": ("07 Display", None),
    "Reported Growth Label": ("07 Display", None),
    "Same-Store Growth Label": ("07 Display", None),
}

MEASURE_HEADER = re.compile(r"^(?!VAR |RETURN)([A-Za-z0-9][^=]*?) =$")


def parse_dax_measures(path: Path) -> list[tuple[str, str]]:
    """Parse `Name =` blocks from a .dax file into (name, expression) pairs."""
    measures: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_name is not None:
            expression = "\n".join(current_lines).strip()
            if not expression:
                raise ValueError(f"Measure {current_name!r} in {path.name} has no expression")
            measures.append((current_name, expression))

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        header = MEASURE_HEADER.match(line)
        if header:
            flush()
            current_name, current_lines = header.group(1), []
        elif line.startswith("//"):
            flush()
            current_name, current_lines = None, []
        elif current_name is not None:
            current_lines.append(line)
    flush()
    return measures


def load_measures(root: Path) -> list[tuple[str, str]]:
    measures = parse_dax_measures(root / "dax" / "07_kpi_measures.dax")
    measures += parse_dax_measures(root / "dax" / "08_dashboard_measures.dax")
    names = [name for name, _ in measures]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Duplicate measures in dax/: {duplicates}")
    missing = sorted(set(names) - set(MEASURE_METADATA))
    stale = sorted(set(MEASURE_METADATA) - set(names))
    if missing or stale:
        raise ValueError(f"Measure metadata mismatch. Missing: {missing}. Stale: {stale}.")
    return measures


# ---------------------------------------------------------------------------
# TMDL writer
# ---------------------------------------------------------------------------


def lineage(*parts: str) -> str:
    return str(uuid.uuid5(LINEAGE_NAMESPACE, "/".join(parts)))


def tmdl_name(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return name
    return "'" + name.replace("'", "''") + "'"


def indent_block(text: str, tabs: int) -> list[str]:
    prefix = "\t" * tabs
    return [prefix + line if line.strip() else "" for line in text.splitlines()]


def csv_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as file:
        return next(csv.reader(file))


def table_m_expression(table: Table) -> str:
    source_columns = [c for c in table.columns if c.name not in dict(table.added_columns)]
    type_pairs = ",\n        ".join(
        f'{{"{c.name}", {c.kind[1]}}}' for c in source_columns
    )
    steps = [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{table.source_file}"), '
        "[Delimiter = \",\", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),",
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        "    ChangedTypes = Table.TransformColumnTypes(",
        "        PromotedHeaders,",
        "        {",
        f"        {type_pairs}",
        "        },",
        '        "en-US"',
        "    )" + ("," if table.added_columns else ""),
    ]
    previous = "ChangedTypes"
    for index, (name, expression) in enumerate(table.added_columns, start=1):
        step = f"Added{index}"
        last = index == len(table.added_columns)
        steps.append(
            f'    {step} = Table.AddColumn({previous}, "{name}", {expression})'
            + ("" if last else ",")
        )
        previous = step
    steps += ["in", f"    {previous}"]
    return "\n".join(steps)


def write_table_tmdl(table: Table) -> str:
    lines = [f"table {tmdl_name(table.name)}"]
    if table.data_category:
        lines.append(f"\tdataCategory: {table.data_category}")
    lines += [f"\tlineageTag: {lineage('table', table.name)}", ""]
    for column in table.columns:
        lines.append(f"\tcolumn {tmdl_name(column.name)}")
        lines.append(f"\t\tdataType: {column.kind[0]}")
        if column.is_key:
            lines.append("\t\tisKey")
        if column.hidden:
            lines.append("\t\tisHidden")
        if column.format_string:
            lines.append(f"\t\tformatString: {column.format_string}")
        if column.data_category:
            lines.append(f"\t\tdataCategory: {column.data_category}")
        lines.append(f"\t\tlineageTag: {lineage('column', table.name, column.name)}")
        lines.append("\t\tsummarizeBy: none")
        lines.append(f"\t\tsourceColumn: {column.name}")
        if column.sort_by:
            lines.append(f"\t\tsortByColumn: {tmdl_name(column.sort_by)}")
        lines += ["", "\t\tannotation SummarizationSetBy = User", ""]
    lines += [
        f"\tpartition {tmdl_name(table.name)} = m",
        "\t\tmode: import",
        "\t\tsource =",
        *indent_block(table_m_expression(table), 4),
        "",
        # Without the result type, Power BI Desktop evaluates every query on
        # open to find it, which runs all CSV loads in parallel.
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_percentile_table_tmdl() -> str:
    lines = [
        f"table {PERCENTILE_TABLE}",
        f"\tlineageTag: {lineage('table', PERCENTILE_TABLE)}",
        "",
        f"\tcolumn {tmdl_name(PERCENTILE_COLUMN)}",
        "\t\tdataType: int64",
        "\t\tformatString: 0",
        f"\t\tlineageTag: {lineage('column', PERCENTILE_TABLE, PERCENTILE_COLUMN)}",
        "\t\tsummarizeBy: none",
        "\t\tisNameInferred",
        f"\t\tsourceColumn: [{PERCENTILE_COLUMN}]",
        "",
        "\t\tannotation SummarizationSetBy = User",
        "",
        f"\tpartition {PERCENTILE_TABLE} = calculated",
        "\t\tmode: import",
        f"\t\tsource = {PERCENTILE_EXPRESSION}",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_measure_table_tmdl(measures: list[tuple[str, str]]) -> str:
    lines = [
        f"table {MEASURE_TABLE}",
        f"\tlineageTag: {lineage('table', MEASURE_TABLE)}",
        "",
    ]
    for name, expression in measures:
        folder, format_string = MEASURE_METADATA[name]
        lines.append(f"\tmeasure {tmdl_name(name)} =")
        lines += indent_block(expression, 3)
        if format_string:
            lines.append(f"\t\tformatString: {format_string}")
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {lineage('measure', name)}")
        lines.append("")
    lines += [
        "\tcolumn Placeholder",
        "\t\tdataType: int64",
        "\t\tisHidden",
        "\t\tformatString: 0",
        f"\t\tlineageTag: {lineage('column', MEASURE_TABLE, 'Placeholder')}",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: Placeholder",
        "",
        "\t\tannotation SummarizationSetBy = User",
        "",
        f"\tpartition {MEASURE_TABLE} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        "\t\t\t\t    Source = #table(type table [Placeholder = Int64.Type], {})",
        "\t\t\t\tin",
        "\t\t\t\t    Source",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_model_tmdl() -> str:
    table_names = [t.name for t in TABLES] + [PERCENTILE_TABLE, MEASURE_TABLE]
    query_order = json.dumps(["DataFolder"] + [t.name for t in TABLES] + [MEASURE_TABLE])
    lines = [
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: en-US",
        "\tmaxParallelismPerRefresh: 1",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        f"annotation PBI_QueryOrder = {query_order}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        "annotation PBIDesktopVersion = 2.156.951.0 (26.07)",
        "",
    ]
    lines += [f"ref table {tmdl_name(name)}" for name in table_names]
    return "\n".join(lines) + "\n"


def write_expressions_tmdl(data_folder: str) -> str:
    value = data_folder.replace('"', '""')
    return (
        f'expression DataFolder = "{value}" meta [IsParameterQuery = true, '
        'Type = "Text", IsParameterQueryRequired = true]\n'
        f"\tlineageTag: {lineage('expression', 'DataFolder')}\n"
        "\n"
        "\tannotation PBI_ResultType = Text\n"
    )


def write_relationships_tmdl() -> str:
    blocks = []
    for from_table, from_column, to_table, to_column, active in RELATIONSHIPS:
        name = lineage("relationship", from_table, from_column, to_table, to_column)
        block = [f"relationship {name}"]
        if not active:
            block.append("\tisActive: false")
        block += [
            f"\tfromColumn: {tmdl_name(from_table)}.{tmdl_name(from_column)}",
            f"\ttoColumn: {tmdl_name(to_table)}.{tmdl_name(to_column)}",
        ]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# PBIR helpers
# ---------------------------------------------------------------------------


def literal(value: Any) -> dict:
    if isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, int):
        text = f"{value}L"
    elif isinstance(value, float):
        text = f"{value:g}D"
    else:
        text = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": text}}}


def number(value: float) -> dict:
    return {"expr": {"Literal": {"Value": f"{value:g}D"}}}


def color(hex_color: str) -> dict:
    return {"solid": {"color": literal(hex_color)}}


def column_ref(table: str, column: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def measure_ref(name: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": MEASURE_TABLE}}, "Property": name}}


def query_ref(field_ref: dict) -> str:
    inner = field_ref.get("Column") or field_ref["Measure"]
    return f"{inner['Expression']['SourceRef']['Entity']}.{inner['Property']}"


def projection(field_ref: dict, display_name: str | None = None) -> dict:
    inner = field_ref.get("Column") or field_ref["Measure"]
    result = {
        "field": field_ref,
        "queryRef": query_ref(field_ref),
        "nativeQueryRef": inner["Property"],
    }
    if display_name:
        result["displayName"] = display_name
    return result


def props(**values: Any) -> dict:
    return {"properties": values}


def rule_fill(measure: str) -> dict:
    """fx Rules colour: first matching rule wins, otherwise the default colour."""
    cases = [
        {
            "Condition": {
                "Comparison": {
                    "ComparisonKind": 2,
                    "Left": measure_ref(measure),
                    "Right": {"Literal": {"Value": f"{threshold:g}D"}},
                }
            },
            "Value": {"Literal": {"Value": f"'{hex_color}'"}},
        }
        for threshold, hex_color in RETURN_RATE_RULES
    ]
    conditional = {
        "Conditional": {
            "Cases": cases,
            "DefaultValue": {"Literal": {"Value": f"'{RETURN_RATE_RULE_DEFAULT}'"}},
        }
    }
    return {"solid": {"color": {"expr": conditional}}}


ALL_DATA_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def topn_filter(name: str, table: str, column: str, order_by: dict, count: int) -> dict:
    alias = table[0].lower()
    return {
        "name": name,
        "field": column_ref(table, column),
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {
                    "Name": "subquery",
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": [
                                    {"Name": alias, "Entity": table, "Type": 0},
                                    {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0},
                                ],
                                "Select": [
                                    {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": alias}},
                                            "Property": column,
                                        },
                                        "Name": "field",
                                    }
                                ],
                                "OrderBy": [
                                    {
                                        "Direction": 2,
                                        "Expression": {
                                            "Measure": {
                                                "Expression": {"SourceRef": {"Source": "m"}},
                                                "Property": order_by["Measure"]["Property"],
                                            }
                                        },
                                    }
                                ],
                                "Top": count,
                            }
                        }
                    },
                    "Type": 2,
                },
                {"Name": alias, "Entity": table, "Type": 0},
            ],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": alias}},
                                        "Property": column,
                                    }
                                }
                            ],
                            "Table": {"SourceRef": {"Source": "subquery"}},
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


def year_filter(name: str, years: list[int]) -> dict:
    return {
        "name": name,
        "field": column_ref("DimDate", "year"),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "d", "Entity": "DimDate", "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": "d"}},
                                        "Property": "year",
                                    }
                                }
                            ],
                            "Values": [[{"Literal": {"Value": f"{year}L"}}] for year in years],
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


# ---------------------------------------------------------------------------
# Visual builders
# ---------------------------------------------------------------------------


@dataclass
class Visual:
    name: str
    x: int
    y: int
    width: int
    height: int
    visual: dict
    filters: list[dict] = field(default_factory=list)
    kind: str = "chart"


def container_style(title: str | None, subtitle: str | None = None) -> dict:
    style: dict[str, list] = {
        "background": [props(show=literal(True), color=color(WHITE), transparency=number(0))],
        "border": [props(show=literal(True), color=color(BORDER), radius=number(6))],
        "visualHeader": [props(show=literal(False))],
        "dropShadow": [props(show=literal(False))],
        "padding": [props(top=number(4), bottom=number(4), left=number(8), right=number(8))],
    }
    if title:
        style["title"] = [
            props(
                show=literal(True),
                text=literal(title),
                fontSize=number(11),
                bold=literal(True),
                fontColor=color(INK),
                titleWrap=literal(False),
            )
        ]
    else:
        style["title"] = [props(show=literal(False))]
    if subtitle:
        style["subTitle"] = [
            props(
                show=literal(True),
                text=literal(subtitle),
                fontSize=number(9),
                fontColor=color(SLATE),
            )
        ]
    return style


def transparent_container() -> dict:
    return {
        "background": [props(show=literal(False))],
        "border": [props(show=literal(False))],
        "title": [props(show=literal(False))],
        "visualHeader": [props(show=literal(False))],
        "dropShadow": [props(show=literal(False))],
    }


def axis_objects(show_value_axis: bool = False) -> dict:
    return {
        "categoryAxis": [
            props(
                show=literal(True),
                fontSize=number(9),
                labelColor=color(SLATE),
                showAxisTitle=literal(False),
            )
        ],
        "valueAxis": [
            props(
                show=literal(show_value_axis),
                fontSize=number(9),
                labelColor=color(SLATE),
                showAxisTitle=literal(False),
                gridlineShow=literal(show_value_axis),
            )
        ],
    }


def data_labels(display_units: int = 0, precision: int | None = None) -> list[dict]:
    values: dict[str, Any] = {
        "show": literal(True),
        "fontSize": number(9),
        "color": color(INK_SECONDARY),
        "labelDisplayUnits": number(display_units),
    }
    if precision is not None:
        values["labelPrecision"] = literal(precision)
    return [props(**values)]


def text_paragraphs(paragraphs: list[tuple[str, int, bool, str]]) -> list[dict]:
    return [
        {
            "textRuns": [
                {
                    "value": text,
                    "textStyle": {
                        "fontFamily": "Segoe UI",
                        "fontSize": f"{size}pt",
                        "fontWeight": "bold" if bold else "normal",
                        "color": text_color,
                    },
                }
            ]
        }
        for text, size, bold, text_color in paragraphs
    ]


def textbox(
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    paragraphs: list[tuple[str, int, bool, str]],
    boxed: bool = False,
    kind: str = "text",
) -> Visual:
    container = container_style(None) if boxed else transparent_container()
    if boxed:
        container["padding"] = [
            props(top=number(10), bottom=number(10), left=number(14), right=number(14))
        ]
    visual = {
        "visualType": "textbox",
        "objects": {"general": [props(paragraphs=text_paragraphs(paragraphs))]},
        "visualContainerObjects": container,
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, height, visual, kind=kind)


def card(
    name: str,
    x: int,
    width: int,
    measure: str,
    label: str,
    display_units: int,
    precision: int,
    filters: list[dict] | None = None,
) -> Visual:
    visual = {
        "visualType": "card",
        "query": {
            "queryState": {"Values": {"projections": [projection(measure_ref(measure), label)]}}
        },
        "objects": {
            "labels": [
                props(
                    color=color(INK),
                    fontSize=number(CARD_VALUE_SIZE),
                    labelDisplayUnits=number(display_units),
                    labelPrecision=literal(precision),
                )
            ],
            "categoryLabels": [
                props(show=literal(True), color=color(SLATE), fontSize=number(CARD_LABEL_SIZE))
            ],
            "wordWrap": [props(show=literal(False))],
        },
        "visualContainerObjects": container_style(None),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, CARD_Y, width, CARD_HEIGHT, visual, filters or [], kind="card")


def bar_chart(
    name: str,
    x: int,
    y: int,
    width: int,
    title: str,
    subtitle: str,
    category: dict,
    measure: str,
    fill: str | dict,
    display_units: int = 0,
    precision: int | None = None,
    visual_type: str = "clusteredBarChart",
    tooltips: list[str] | None = None,
    sort_by_category: bool = False,
    measure_label: str | None = None,
    filters: list[dict] | None = None,
) -> Visual:
    query_state: dict[str, Any] = {
        "Category": {"projections": [projection(category)]},
        "Y": {"projections": [projection(measure_ref(measure), measure_label)]},
    }
    if tooltips:
        query_state["Tooltips"] = {
            "projections": [projection(measure_ref(m), _tooltip_label(m)) for m in tooltips]
        }
    sort_field = category if sort_by_category else measure_ref(measure)
    sort_direction = "Ascending" if sort_by_category else "Descending"
    fill_value = color(fill) if isinstance(fill, str) else fill
    data_point = [props(fill=fill_value)]
    if not isinstance(fill, str):
        data_point = [
            props(fill=color(RETURN_RATE_RULE_DEFAULT)),
            {"properties": {"fill": fill_value}, "selector": ALL_DATA_POINTS},
        ]
    objects = axis_objects()
    # A small preferred category width lets ten bars fit the row height
    # without the default minimum forcing a scrollbar.
    objects["categoryAxis"][0]["properties"].update(
        preferredCategoryWidth=number(BAR_CATEGORY_WIDTH),
        innerPadding=number(BAR_INNER_PADDING),
    )
    objects["labels"] = data_labels(display_units, precision)
    objects["dataPoint"] = data_point
    objects["legend"] = [props(show=literal(False))]
    visual = {
        "visualType": visual_type,
        "query": {
            "queryState": query_state,
            "sortDefinition": {
                "sort": [{"field": sort_field, "direction": sort_direction}],
                "isDefaultSort": True,
            },
        },
        "objects": objects,
        "visualContainerObjects": container_style(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, ROW_HEIGHT, visual, filters or [])


def _tooltip_label(measure: str) -> str | None:
    return RETURN_RATE_LABEL if measure == "Return Quantity Rate %" else None


def line_chart(
    name: str,
    x: int,
    y: int,
    width: int,
    title: str,
    subtitle: str,
    category: dict,
    measures: list[tuple[str, str]],
    series: dict | None = None,
    series_colors: list[tuple[str, str]] | None = None,
    value_format_units: int = 0,
) -> Visual:
    query_state: dict[str, Any] = {
        "Category": {"projections": [projection(category)]},
        "Y": {"projections": [projection(measure_ref(m), label) for m, label in measures]},
    }
    if series:
        query_state["Series"] = {"projections": [projection(series)]}
    objects = axis_objects(show_value_axis=True)
    objects["valueAxis"][0]["properties"]["labelDisplayUnits"] = number(value_format_units)
    objects["legend"] = [
        props(
            show=literal(len(measures) > 1 or series is not None),
            position=literal("Top"),
            fontSize=number(9),
            labelColor=color(INK_SECONDARY),
        )
    ]
    objects["lineStyles"] = [props(strokeWidth=literal(2))]
    data_point = []
    if series_colors:
        for selector_value, hex_color in series_colors:
            data_point.append(
                {"properties": {"fill": color(hex_color)}, "selector": {"metadata": selector_value}}
            )
    if data_point:
        objects["dataPoint"] = data_point
    visual = {
        "visualType": "lineChart",
        "query": {
            "queryState": query_state,
            "sortDefinition": {
                "sort": [{"field": category, "direction": "Ascending"}],
                "isDefaultSort": True,
            },
        },
        "objects": objects,
        "visualContainerObjects": container_style(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, ROW_HEIGHT, visual)


def scatter_chart(
    name: str,
    x: int,
    y: int,
    width: int,
    title: str,
    subtitle: str,
    details: dict,
    x_measure: str,
    y_measure: str,
    size_measure: str,
    x_label: str,
    y_label: str,
    point_color: str,
) -> Visual:
    query_state = {
        "Category": {"projections": [projection(details)]},
        "X": {"projections": [projection(measure_ref(x_measure), x_label)]},
        "Y": {"projections": [projection(measure_ref(y_measure), y_label)]},
        "Size": {"projections": [projection(measure_ref(size_measure))]},
    }
    objects = {
        "categoryAxis": [
            props(
                show=literal(True),
                fontSize=number(9),
                labelColor=color(SLATE),
                showAxisTitle=literal(True),
                titleFontSize=number(9),
                titleColor=color(SLATE),
                gridlineShow=literal(False),
            )
        ],
        "valueAxis": [
            props(
                show=literal(True),
                fontSize=number(9),
                labelColor=color(SLATE),
                showAxisTitle=literal(True),
                titleFontSize=number(9),
                titleColor=color(SLATE),
            )
        ],
        "dataPoint": [props(fill=color(point_color))],
        "categoryLabels": [props(show=literal(False))],
        "legend": [props(show=literal(False))],
    }
    visual = {
        "visualType": "scatterChart",
        "query": {"queryState": query_state},
        "objects": objects,
        "visualContainerObjects": container_style(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, ROW_HEIGHT, visual)


def column_chart(
    name: str,
    x: int,
    y: int,
    width: int,
    title: str,
    subtitle: str,
    category: dict,
    measures: list[tuple[str, str | None, str]],
    display_units: int = 0,
    precision: int | None = None,
    tooltips: list[str] | None = None,
) -> Visual:
    query_state: dict[str, Any] = {
        "Category": {"projections": [projection(category)]},
        "Y": {"projections": [projection(measure_ref(m), label) for m, label, _ in measures]},
    }
    if tooltips:
        query_state["Tooltips"] = {"projections": [projection(measure_ref(m)) for m in tooltips]}
    objects = axis_objects()
    objects["labels"] = data_labels(display_units, precision)
    objects["legend"] = [
        props(
            show=literal(len(measures) > 1),
            position=literal("Top"),
            fontSize=number(9),
            labelColor=color(INK_SECONDARY),
        )
    ]
    objects["dataPoint"] = [
        {"properties": {"fill": color(hex_color)}, "selector": {"metadata": query_ref(measure_ref(m))}}
        for m, _, hex_color in measures
    ]
    visual = {
        "visualType": "clusteredColumnChart",
        "query": {
            "queryState": query_state,
            "sortDefinition": {
                "sort": [{"field": category, "direction": "Ascending"}],
                "isDefaultSort": True,
            },
        },
        "objects": objects,
        "visualContainerObjects": container_style(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, ROW_HEIGHT, visual)


def detail_table(
    name: str,
    x: int,
    y: int,
    width: int,
    title: str,
    subtitle: str | None,
    columns: list[tuple[dict, str, int]],
    rule_measure: str,
    rule_target: str,
    sort_measure: str,
    filters: list[dict],
) -> Visual:
    projections = [projection(f, label) for f, label, _ in columns]
    objects: dict[str, list] = {
        "total": [props(totals=literal(False))],
        "columnHeaders": [
            props(fontSize=number(9), fontColor=color(INK), bold=literal(True), wordWrap=literal(False))
        ],
        "values": [
            props(fontSize=number(9), fontColor=color(INK_SECONDARY), wordWrap=literal(False)),
            {
                "properties": {"fontColor": rule_fill(rule_measure)},
                "selector": {**ALL_DATA_POINTS, "metadata": rule_target},
            },
        ],
        "grid": [props(rowPadding=number(2), gridVertical=literal(False))],
        "columnWidth": [
            {"properties": {"value": number(w)}, "selector": {"metadata": query_ref(f)}}
            for f, _, w in columns
        ],
    }
    visual = {
        "visualType": "tableEx",
        "query": {
            "queryState": {"Values": {"projections": projections}},
            "sortDefinition": {
                "sort": [{"field": measure_ref(sort_measure), "direction": "Descending"}],
                "isDefaultSort": True,
            },
        },
        "objects": objects,
        "visualContainerObjects": container_style(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, y, width, ROW_HEIGHT, visual, filters, kind="table")


def slicer(name: str, x: int, table: str, column: str, label: str, filters: list[dict] | None = None) -> Visual:
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [projection(column_ref(table, column))]}}},
        "objects": {
            "data": [props(mode=literal("Dropdown"))],
            "header": [
                props(
                    show=literal(True),
                    text=literal(label),
                    fontSize=number(9),
                    fontColor=color(SLATE),
                )
            ],
            "items": [props(fontSize=number(9), fontColor=color(INK))],
            "selection": [props(selectAllCheckboxEnabled=literal(True), singleSelect=literal(False))],
        },
        "visualContainerObjects": {
            **transparent_container(),
            "background": [props(show=literal(True), color=color(WHITE), transparency=number(0))],
        },
        "syncGroup": {"groupName": f"{table}.{column}", "fieldChanges": True, "filterChanges": True},
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, SLICER_Y, SLICER_WIDTH, SLICER_HEIGHT, visual, filters or [], kind="slicer")


def nav_button(name: str, x: int, label: str, target_page: str, active: bool) -> Visual:
    # Button objects keep `show` in a card-level entry and the formatting of
    # each button state in an entry with a state selector.
    default = {"id": "default"}
    visual = {
        "visualType": "actionButton",
        "objects": {
            "icon": [
                props(show=literal(False)),
                {"properties": {"shapeType": literal("blank")}, "selector": default},
            ],
            "text": [
                props(show=literal(True)),
                {
                    "properties": {
                        "text": literal(label),
                        "fontColor": color(TEAL if active else SLATE),
                        "fontSize": number(10),
                        "bold": literal(active),
                        "horizontalAlignment": literal("center"),
                    },
                    "selector": default,
                },
            ],
            "fill": [
                props(show=literal(True)),
                {
                    "properties": {
                        "fillColor": color("#E6F4F1" if active else WHITE),
                        "transparency": number(0),
                    },
                    "selector": default,
                },
            ],
            "outline": [props(show=literal(False))],
        },
        "visualContainerObjects": {
            "visualLink": [
                props(
                    show=literal(True),
                    type=literal("PageNavigation"),
                    navigationSection=literal(target_page),
                )
            ],
            "visualHeader": [props(show=literal(False))],
        },
        "drillFilterOtherVisuals": True,
    }
    return Visual(name, x, NAV_Y, NAV_WIDTH, NAV_HEIGHT, visual, kind="nav")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

PAGES = [
    ("p01_executive_overview", "Executive Overview", "Overview"),
    ("p02_sales_performance", "Sales Performance", "Sales"),
    ("p03_product_profitability", "Product & Profitability", "Product"),
    ("p04_customer_analysis", "Customer Analysis", "Customer"),
    ("p05_store_geography", "Store & Geographic Performance", "Stores"),
    ("p06_returns_detail", "Returns & Detailed Analysis", "Returns"),
]
SOURCE_FOOTER = (
    "Source: Maven Market sample data (Kaggle), Jan 1997 – Dec 1998, star schema in data/model. "
    "Gross product profit = revenue − product cost; it excludes operating costs."
)
RETURNS_FOOTER = (
    "Source: Maven Market sample data (Kaggle), Jan 1997 – Dec 1998. Return rate (proxy) = "
    "returned units ÷ units sold; returns cannot be linked to a customer or sales line."
)


def card_positions(count: int) -> list[tuple[int, int]]:
    width = (CONTENT_WIDTH - (count - 1) * GAP) // count
    positions = []
    for index in range(count):
        x = MARGIN + index * (width + GAP)
        positions.append((x, width))
    return positions


def page_frame(page_name: str, title: str, finding: str, footer: str) -> list[Visual]:
    visuals = [
        textbox("title", MARGIN, TITLE_Y, 600, TITLE_HEIGHT, [(title, 20, True, INK)], kind="title"),
        textbox(
            "finding",
            MARGIN,
            SUBTITLE_Y,
            CONTENT_WIDTH - 3 * SLICER_WIDTH - 2 * 12 - GAP,
            SUBTITLE_HEIGHT,
            [(finding, 11, False, INK_SECONDARY)],
            kind="subtitle",
        ),
        textbox(
            "footer",
            MARGIN,
            FOOTER_Y,
            CONTENT_WIDTH,
            FOOTER_HEIGHT,
            [(footer, 8, False, SLATE)],
            kind="footer",
        ),
    ]
    nav_x = MARGIN + CONTENT_WIDTH - (len(PAGES) * NAV_WIDTH + (len(PAGES) - 1) * NAV_GAP)
    for index, (target, _, short_label) in enumerate(PAGES):
        visuals.append(
            nav_button(
                f"nav_{index + 1:02d}",
                nav_x + index * (NAV_WIDTH + NAV_GAP),
                short_label,
                target,
                target == page_name,
            )
        )
    slicer_x = MARGIN + CONTENT_WIDTH - (3 * SLICER_WIDTH + 2 * 12)
    visuals += [
        slicer(
            "slicer_year",
            slicer_x,
            "DimDate",
            "year",
            "Year",
            [year_filter("slicer_year_scope", [1997, 1998])],
        ),
        slicer("slicer_country", slicer_x + SLICER_WIDTH + 12, "DimStore", "store_country", "Country"),
        slicer("slicer_region", slicer_x + 2 * (SLICER_WIDTH + 12), "DimStore", "sales_region", "Sales region"),
    ]
    return visuals


def build_pages(facts: dict[str, Any]) -> list[tuple[str, str, list[Visual]]]:
    left, right_wide = MARGIN, MARGIN + WIDE_WIDTH + GAP
    right_half = MARGIN + HALF_WIDTH + GAP
    half_right_width = CONTENT_WIDTH - HALF_WIDTH - GAP
    store = lambda c: column_ref("DimStore", c)  # noqa: E731
    product = lambda c: column_ref("DimProduct", c)  # noqa: E731
    customer = lambda c: column_ref("DimCustomer", c)  # noqa: E731
    date = lambda c: column_ref("DimDate", c)  # noqa: E731
    pages: list[tuple[str, str, list[Visual]]] = []

    def cards(specs: list[tuple[str, str, str, int, int]]) -> list[Visual]:
        return [
            card(name, x, width, measure, label, units, precision)
            for (name, measure, label, units, precision), (x, width) in zip(
                specs, card_positions(len(specs))
            )
        ]

    # 1. Executive Overview
    visuals = page_frame(
        "p01_executive_overview",
        "Executive Overview",
        facts["finding_overview"],
        SOURCE_FOOTER,
    )
    visuals += cards(
        [
            ("ov01_total_revenue", "Total Revenue", "Total revenue", 1_000_000, 2),
            ("ov02_gross_profit", "Gross Product Profit", "Gross product profit", 1_000_000, 2),
            ("ov03a_reported_growth", "Latest Year Revenue Growth %", "Reported growth, latest year", 0, 1),
            (
                "ov03b_same_store_growth",
                "Latest Year Same-Store Revenue Growth %",
                "Same-store growth, latest year",
                0,
                1,
            ),
            ("ov07_return_rate", "Return Quantity Rate %", RETURN_RATE_LABEL, 0, 1),
        ]
    )
    visuals += [
        line_chart(
            "ov04_monthly_revenue_profit",
            left,
            ROW_A_Y,
            WIDE_WIDTH,
            "Monthly revenue and gross product profit",
            "Both series in $; margin is stable because prices are fixed per product",
            date("year_month"),
            [("Total Revenue", "Revenue"), ("Gross Product Profit", "Gross product profit")],
            series_colors=[
                ("_Measures.Total Revenue", TEAL),
                ("_Measures.Gross Product Profit", BLUE),
            ],
            value_format_units=1000,
        ),
        bar_chart(
            "ov05_revenue_by_country",
            right_wide,
            ROW_A_Y,
            NARROW_WIDTH,
            "Revenue by country",
            "Click a bar to filter the page",
            store("store_country"),
            "Total Revenue",
            TEAL,
            display_units=1000,
            precision=0,
        ),
        bar_chart(
            "ov06_top_brands_revenue",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            f"Top {MAX_BARS} brands by revenue",
            "Drill through to Returns & Detailed Analysis for product detail",
            product("product_brand"),
            "Total Revenue",
            BLUE,
            display_units=1000,
            precision=1,
            filters=[
                topn_filter("ov06_top_bars", "DimProduct", "product_brand", measure_ref("Total Revenue"), MAX_BARS)
            ],
        ),
        textbox(
            "ov08_management_notes",
            right_half,
            ROW_B_Y,
            half_right_width,
            ROW_HEIGHT,
            [("Management notes (full period, 1997–1998)", 11, True, INK)]
            + [(f"• {note}", 10, False, INK_SECONDARY) for note in facts["management_notes"]],
            boxed=True,
            kind="chart",
        ),
    ]
    pages.append(("p01_executive_overview", "Executive Overview", visuals))

    # 2. Sales Performance
    visuals = page_frame(
        "p02_sales_performance", "Sales Performance", facts["finding_sales"], SOURCE_FOOTER
    )
    visuals += cards(
        [
            ("sa00a_revenue_ytd", "Revenue YTD", "Revenue, latest year to date", 1_000_000, 2),
            ("sa00b_reported_growth", "Latest Year Revenue Growth %", "Reported growth, latest year", 0, 1),
            (
                "sa00c_same_store_growth",
                "Latest Year Same-Store Revenue Growth %",
                "Same-store growth, latest year",
                0,
                1,
            ),
            ("sa00d_active_stores", "Active Stores", "Active stores", 1, 0),
        ]
    )
    visuals += [
        line_chart(
            "sa01_monthly_revenue_by_year",
            left,
            ROW_A_Y,
            WIDE_WIDTH,
            "Monthly revenue by year",
            "1997 compared with 1998; 1998 includes 11 additional stores",
            date("month_short_name"),
            [("Total Revenue", "Revenue")],
            series=date("year"),
            value_format_units=1000,
        ),
        bar_chart(
            "sa02_revenue_by_region",
            right_wide,
            ROW_A_Y,
            NARROW_WIDTH,
            "Revenue by sales region",
            "Click a region to filter the store ranking",
            store("sales_region"),
            "Total Revenue",
            BLUE,
            display_units=1000,
            precision=0,
        ),
        bar_chart(
            "sa03_store_revenue_ranking",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            f"Top {MAX_BARS} stores by revenue",
            "Right-click a store to drill through to returns",
            store("store_name"),
            "Total Revenue",
            TEAL,
            display_units=1000,
            precision=1,
            filters=[topn_filter("sa03_top_bars", "DimStore", "store_name", measure_ref("Total Revenue"), MAX_BARS)],
        ),
        column_chart(
            "sa04_growth_comparison",
            right_half,
            ROW_B_Y,
            half_right_width,
            "Reported vs same-store revenue growth",
            "Only years with a prior-year baseline are shown",
            date("year"),
            [
                ("Revenue Growth %", "Reported growth", GOLD),
                ("Same-Store Revenue Growth %", "Same-store growth", TEAL),
            ],
            precision=1,
        ),
    ]
    pages.append(("p02_sales_performance", "Sales Performance", visuals))

    # 3. Product & Profitability
    visuals = page_frame(
        "p03_product_profitability",
        "Product & Profitability",
        facts["finding_product"],
        SOURCE_FOOTER,
    )
    visuals += cards(
        [
            ("pr00a_active_products", "Active Products", "Products with sales", 1, 0),
            ("pr00b_gross_margin", "Gross Margin %", "Gross margin (product mix)", 0, 1),
            ("pr00c_quantity_sold", "Quantity Sold", "Units sold", 1, 0),
            ("pr00d_returned_quantity", "Returned Quantity", "Units returned", 1, 0),
        ]
    )
    visuals += [
        bar_chart(
            "pr01_top_products_revenue",
            left,
            ROW_A_Y,
            HALF_WIDTH,
            f"Top {MAX_BARS} products by revenue",
            "Revenue across the selected period",
            product("product_name"),
            "Total Revenue",
            TEAL,
            display_units=1000,
            precision=2,
            tooltips=["Gross Product Profit", "Gross Margin %", "Quantity Sold"],
            filters=[
                topn_filter("pr01_top_bars", "DimProduct", "product_name", measure_ref("Total Revenue"), MAX_BARS)
            ],
        ),
        scatter_chart(
            "pr02_brand_revenue_margin",
            right_half,
            ROW_A_Y,
            half_right_width,
            "Brand revenue vs gross margin",
            "One point per brand; bubble size = units sold",
            product("product_brand"),
            "Total Revenue",
            "Gross Margin %",
            "Quantity Sold",
            "Revenue",
            "Gross margin",
            BLUE,
        ),
        bar_chart(
            "pr03_top_brands_profit",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            f"Top {MAX_BARS} brands by gross product profit",
            "Profit before operating costs",
            product("product_brand"),
            "Gross Product Profit",
            BLUE,
            display_units=1000,
            precision=1,
            filters=[
                topn_filter(
                    "pr03_top_bars", "DimProduct", "product_brand", measure_ref("Gross Product Profit"), MAX_BARS
                )
            ],
        ),
        bar_chart(
            "pr04_product_return_risk",
            right_half,
            ROW_B_Y,
            half_right_width,
            "Highest product return rates (proxy)",
            "Products with 300+ units sold; red ≥ 0.5 pp above network",
            product("product_name"),
            "Product Return Rate (300+ Units) %",
            rule_fill("Return Rate vs Overall (pp)"),
            precision=2,
            measure_label=RETURN_RATE_LABEL,
            tooltips=["Quantity Sold", "Returned Quantity"],
            filters=[
                topn_filter(
                    "pr04_top_bars",
                    "DimProduct",
                    "product_name",
                    measure_ref("Product Return Rate (300+ Units) %"),
                    MAX_BARS,
                )
            ],
        ),
    ]
    pages.append(("p03_product_profitability", "Product & Profitability", visuals))

    # 4. Customer Analysis
    visuals = page_frame(
        "p04_customer_analysis", "Customer Analysis", facts["finding_customer"], SOURCE_FOOTER
    )
    visuals += cards(
        [
            ("cu00a_active_customers", "Active Customers", "Active customers", 1, 0),
            ("cu00b_revenue_per_customer", "Revenue per Active Customer", "Revenue per active customer", 1, 2),
            ("cu00c_repeat_rate", "Repeat Customer Rate %", "Repeat customer rate", 0, 1),
            (
                "cu00d_top10_share",
                "Top 10% Customer Revenue Contribution %",
                "Top 10% customer revenue share",
                0,
                1,
            ),
        ]
    )
    visuals += [
        column_chart(
            "cu01_revenue_by_tier",
            left,
            ROW_A_Y,
            HALF_WIDTH,
            "Revenue by membership tier",
            "Tooltip shows active customers per tier",
            customer("member_card"),
            [("Total Revenue", "Revenue", TEAL)],
            display_units=1000,
            precision=0,
            tooltips=["Active Customers"],
        ),
        column_chart(
            "cu02_revenue_per_customer",
            right_half,
            ROW_A_Y,
            half_right_width,
            "Revenue per active customer by tier",
            "Membership tiers in programme order",
            customer("member_card"),
            [("Revenue per Active Customer", "Revenue per customer", BLUE)],
            display_units=1,
            precision=0,
            tooltips=["Active Customers"],
        ),
        column_chart(
            "cu03_revenue_by_income",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            "Revenue by income band",
            "Yearly income bands from lowest to highest",
            customer("yearly_income"),
            [("Total Revenue", "Revenue", GOLD)],
            display_units=1000,
            precision=0,
        ),
        line_chart(
            "cu04_customer_concentration",
            right_half,
            ROW_B_Y,
            half_right_width,
            "Customer revenue concentration",
            "Cumulative revenue share by top customer percentile",
            column_ref(PERCENTILE_TABLE, PERCENTILE_COLUMN),
            [("Cumulative Customer Revenue Share %", "Cumulative revenue share")],
            series_colors=[("_Measures.Cumulative Customer Revenue Share %", TEAL)],
        ),
    ]
    pages.append(("p04_customer_analysis", "Customer Analysis", visuals))

    # 5. Store & Geographic Performance
    visuals = page_frame(
        "p05_store_geography",
        "Store & Geographic Performance",
        facts["finding_store"],
        SOURCE_FOOTER,
    )
    visuals += cards(
        [
            ("st00a_active_stores", "Active Stores", "Active stores", 1, 0),
            ("st00b_revenue_per_store", "Revenue per Active Store", "Revenue per active store", 1000, 1),
            ("st00c_revenue_per_sqft", "Revenue per Square Foot", "Revenue per sq ft", 1, 2),
            ("st00d_comparable_stores", "Comparable Stores", "Comparable stores", 1, 0),
        ]
    )
    visuals += [
        scatter_chart(
            "st01_store_size_revenue",
            left,
            ROW_A_Y,
            HALF_WIDTH,
            "Store size vs revenue",
            "One point per store; bubble size = units sold",
            store("store_name"),
            "Active Store Area",
            "Total Revenue",
            "Quantity Sold",
            "Store area (sq ft)",
            "Revenue",
            TEAL,
        ),
        bar_chart(
            "st02_revenue_by_store_type",
            right_half,
            ROW_A_Y,
            half_right_width,
            "Revenue by store type",
            "Click a format to filter the store rankings",
            store("store_type"),
            "Total Revenue",
            BLUE,
            display_units=1000,
            precision=0,
        ),
        bar_chart(
            "st03_top_stores_revenue",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            f"Top {MAX_BARS} stores by revenue",
            "Right-click a store to drill through to returns",
            store("store_name"),
            "Total Revenue",
            TEAL,
            display_units=1000,
            precision=1,
            filters=[topn_filter("st03_top_bars", "DimStore", "store_name", measure_ref("Total Revenue"), MAX_BARS)],
        ),
        bar_chart(
            "st04_revenue_per_sqft",
            right_half,
            ROW_B_Y,
            half_right_width,
            f"Top {MAX_BARS} stores by revenue per sq ft",
            "Revenue divided by total store area",
            store("store_name"),
            "Revenue per Square Foot",
            GOLD,
            display_units=1,
            precision=2,
            filters=[
                topn_filter(
                    "st04_top_bars", "DimStore", "store_name", measure_ref("Revenue per Square Foot"), MAX_BARS
                )
            ],
        ),
    ]
    pages.append(("p05_store_geography", "Store & Geographic Performance", visuals))

    # 6. Returns & Detailed Analysis
    visuals = page_frame(
        "p06_returns_detail",
        "Returns & Detailed Analysis",
        facts["finding_returns"],
        RETURNS_FOOTER,
    )
    visuals += cards(
        [
            ("re00a_returned_quantity", "Returned Quantity", "Units returned", 1, 0),
            ("re00b_return_rate", "Return Quantity Rate %", RETURN_RATE_LABEL, 0, 2),
            ("re00c_return_lines", "Return Lines", "Return records", 1, 0),
            ("re00d_returned_products", "Returned Products", "Products with a return", 1, 0),
        ]
    )
    visuals += [
        line_chart(
            "re01_monthly_returned_quantity",
            left,
            ROW_A_Y,
            WIDE_WIDTH,
            "Monthly returned units",
            "Returns follow sales volume; read with the return rate (proxy)",
            date("year_month"),
            [("Returned Quantity", "Units returned")],
            series_colors=[("_Measures.Returned Quantity", DARK_RED)],
        ),
        bar_chart(
            "re02_store_return_rate",
            right_wide,
            ROW_A_Y,
            NARROW_WIDTH,
            f"Top {MAX_BARS} stores by return rate (proxy)",
            "Red ≥ 0.5 pp, amber ≥ 0.15 pp above network",
            store("store_name"),
            "Return Quantity Rate %",
            rule_fill("Return Rate vs Overall (pp)"),
            precision=2,
            measure_label=RETURN_RATE_LABEL,
            tooltips=["Quantity Sold", "Returned Quantity"],
            filters=[
                topn_filter(
                    "re02_top_bars", "DimStore", "store_name", measure_ref("Return Quantity Rate %"), MAX_BARS
                )
            ],
        ),
        bar_chart(
            "re03_product_return_risk",
            left,
            ROW_B_Y,
            HALF_WIDTH,
            "Product return risk",
            "Products with 300+ units sold; red ≥ 0.5 pp above network",
            product("product_name"),
            "Product Return Rate (300+ Units) %",
            rule_fill("Return Rate vs Overall (pp)"),
            precision=2,
            measure_label=RETURN_RATE_LABEL,
            tooltips=["Quantity Sold", "Returned Quantity"],
            filters=[
                topn_filter(
                    "re03_top_bars",
                    "DimProduct",
                    "product_name",
                    measure_ref("Product Return Rate (300+ Units) %"),
                    MAX_BARS,
                )
            ],
        ),
        detail_table(
            "re04_return_detail",
            right_half,
            ROW_B_Y,
            half_right_width,
            f"Top {DETAIL_TABLE_ROWS} stores by returned units",
            None,
            [
                (store("store_name"), "Store", 70),
                (store("store_type"), "Store type", 124),
                (measure_ref("Quantity Sold"), "Units sold", 76),
                (measure_ref("Total Revenue"), "Revenue", 84),
                (measure_ref("Returned Quantity"), "Returned", 68),
                (measure_ref("Return Quantity Rate %"), RETURN_RATE_LABEL, 134),
            ],
            "Return Rate vs Overall (pp)",
            "_Measures.Return Quantity Rate %",
            "Returned Quantity",
            [
                topn_filter(
                    "re04_top_rows",
                    "DimStore",
                    "store_name",
                    measure_ref("Returned Quantity"),
                    DETAIL_TABLE_ROWS,
                )
            ],
        ),
    ]
    pages.append(("p06_returns_detail", "Returns & Detailed Analysis", visuals))
    return pages


def load_facts(root: Path) -> dict[str, Any]:
    eda = json.loads((root / "reports" / "eda_summary.json").read_text(encoding="utf-8"))
    with (root / "reports" / "store_performance.csv").open(encoding="utf-8", newline="") as file:
        stores = list(csv.DictReader(file))
    top_revenue = max(stores, key=lambda row: float(row["revenue"]))
    top_productivity = max(stores, key=lambda row: float(row["revenue_per_sqft"]))
    growth = eda["reported_revenue_growth_1998_pct"]
    same_store = eda["same_store_revenue_growth_1998_pct"]
    margin = eda["gross_margin_pct"]
    facts = {
        "finding_overview": (
            f"1998 revenue grew {growth:.1f}%, but the {eda['stores_1997']} comparable stores "
            f"grew only {same_store:.1f}%."
        ),
        "finding_sales": (
            f"Same-store revenue grew {same_store:.1f}% in 1998; the rest of the "
            f"{growth:.1f}% came from new stores."
        ),
        "finding_product": (
            f"Price and cost are fixed per product, so the {margin:.1f}% margin moves only "
            "with mix."
        ),
        "finding_customer": (
            f"The top 10% of customers generate {eda['top_10_customer_revenue_share_pct']:.1f}% "
            f"of revenue; {eda['highest_revenue_per_customer_membership']} members spend the most."
        ),
        "finding_store": (
            f"Size does not predict revenue; {top_revenue['store_name']} leads on both revenue "
            "and sales per sq ft."
            if top_revenue["store_name"] == top_productivity["store_name"]
            else f"Store size does not predict revenue; {top_revenue['store_name']} leads on "
            f"revenue and {top_productivity['store_name']} on sales per sq ft."
        ),
        "finding_returns": (
            f"Return rate (proxy) is {eda['return_rate_proxy_pct']:.1f}% of units; "
            f"{eda['highest_store_return_rate_store']} has the highest store rate "
            f"({eda['highest_store_return_rate_pct']:.2f}%)."
        ),
        "management_notes": [
            f"Network revenue grew {growth:.1f}% in 1998; comparable-store revenue grew "
            f"{same_store:.1f}%.",
            f"Gross margin ({margin:.1f}%) is set by fixed product prices and costs; it moves "
            "only with product mix.",
            f"The top 10% of active customers generated "
            f"{eda['top_10_customer_revenue_share_pct']:.1f}% of revenue.",
            f"Return rate (proxy) stayed near {eda['return_rate_proxy_pct']:.1f}% of units sold.",
            "Store size alone does not explain revenue; review productivity by store.",
        ],
    }
    return facts


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def visual_payload(page_name: str, visual: Visual, z_order: int) -> dict:
    payload: dict[str, Any] = {
        "$schema": SCHEMAS["visual"],
        "name": visual.name,
        "position": {
            "x": visual.x,
            "y": visual.y,
            "z": z_order * 1000,
            "height": visual.height,
            "width": visual.width,
            "tabOrder": z_order * 1000,
        },
        "visual": visual.visual,
    }
    if visual.filters:
        payload["filterConfig"] = {"filters": visual.filters}
    return payload


def drillthrough_filters() -> list[dict]:
    return [
        {
            "name": "drillthrough_store",
            "field": column_ref("DimStore", "store_name"),
            "type": "Categorical",
            "howCreated": "Drillthrough",
        },
        {
            "name": "drillthrough_product",
            "field": column_ref("DimProduct", "product_name"),
            "type": "Categorical",
            "howCreated": "Drillthrough",
        },
    ]


def page_payload(name: str, display_name: str) -> dict:
    payload: dict[str, Any] = {
        "$schema": SCHEMAS["page"],
        "name": name,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": CANVAS_HEIGHT,
        "width": CANVAS_WIDTH,
        "objects": {
            "background": [props(color=color(PAGE_BACKGROUND), transparency=number(0))],
            "outspace": [props(color=color(PAGE_BACKGROUND), transparency=number(0))],
        },
    }
    if name == "p06_returns_detail":
        payload["filterConfig"] = {"filters": drillthrough_filters()}
        payload["pageBinding"] = {
            "name": "returns_drillthrough",
            "type": "Drillthrough",
            "referenceScope": "Default",
            "parameters": [
                {
                    "name": "store_parameter",
                    "boundFilter": "drillthrough_store",
                    "fieldExpr": column_ref("DimStore", "store_name"),
                },
                {
                    "name": "product_parameter",
                    "boundFilter": "drillthrough_product",
                    "fieldExpr": column_ref("DimProduct", "product_name"),
                },
            ],
        }
    return payload


def build_semantic_model(root: Path, model_dir: Path, data_folder: str) -> None:
    measures = load_measures(root)
    definition = model_dir / "definition"
    for table in TABLES:
        header = csv_header(root / "data" / "model" / table.source_file)
        expected = [c.name for c in table.columns if c.name not in dict(table.added_columns)]
        if header != expected:
            raise ValueError(f"{table.source_file} columns {header} do not match model {expected}")
        write_text(definition / "tables" / f"{table.name}.tmdl", write_table_tmdl(table))
    write_text(
        definition / "tables" / f"{PERCENTILE_TABLE}.tmdl", write_percentile_table_tmdl()
    )
    write_text(
        definition / "tables" / f"{MEASURE_TABLE}.tmdl", write_measure_table_tmdl(measures)
    )
    write_text(definition / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    write_text(definition / "model.tmdl", write_model_tmdl())
    write_text(definition / "expressions.tmdl", write_expressions_tmdl(data_folder))
    write_text(definition / "relationships.tmdl", write_relationships_tmdl())
    write_json(
        model_dir / "definition.pbism",
        {"$schema": SCHEMAS["pbism"], "version": "4.2", "settings": {}},
    )


def lf_bytes(path: Path) -> bytes:
    """File content with LF line endings, so output does not depend on git checkout settings."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def base_theme_path(report_dir: Path) -> Path:
    return report_dir / "StaticResources" / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json"


def read_base_theme(report_dir: Path) -> bytes:
    """Read the base theme from Power BI Desktop, or reuse the committed copy."""
    for source in [BASE_THEME_SOURCE / f"{BASE_THEME}.json", base_theme_path(report_dir)]:
        if source.exists():
            return lf_bytes(source)
    raise FileNotFoundError(f"Base theme {BASE_THEME}.json not found in Power BI Desktop or {report_dir}")


def build_report(root: Path, report_dir: Path, base_theme_bytes: bytes) -> None:
    facts = load_facts(root)
    definition = report_dir / "definition"
    theme_source = root / "dashboard" / "maven_market_power_bi_theme.json"
    theme_name = theme_source.name
    registered = report_dir / "StaticResources" / "RegisteredResources" / theme_name
    registered.parent.mkdir(parents=True, exist_ok=True)
    registered.write_bytes(lf_bytes(theme_source))
    base_theme = base_theme_path(report_dir)
    base_theme.parent.mkdir(parents=True, exist_ok=True)
    base_theme.write_bytes(base_theme_bytes)

    write_json(
        report_dir / "definition.pbir",
        {
            "$schema": SCHEMAS["pbir"],
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{PROJECT_NAME}.SemanticModel"}},
        },
    )
    write_json(definition / "version.json", {"$schema": SCHEMAS["version"], "version": "2.0.0"})
    write_json(
        definition / "report.json",
        {
            "$schema": SCHEMAS["report"],
            "themeCollection": {
                "baseTheme": {
                    "name": BASE_THEME,
                    "reportVersionAtImport": THEME_VERSION,
                    "type": "SharedResources",
                },
                "customTheme": {
                    "name": theme_name,
                    "reportVersionAtImport": THEME_VERSION,
                    "type": "RegisteredResources",
                },
            },
            "resourcePackages": [
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [
                        {"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}
                    ],
                },
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [{"name": theme_name, "path": theme_name, "type": "CustomTheme"}],
                },
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
            },
        },
    )
    pages = build_pages(facts)
    write_json(
        definition / "pages" / "pages.json",
        {
            "$schema": SCHEMAS["pages"],
            "pageOrder": [name for name, _, _ in pages],
            "activePageName": pages[0][0],
        },
    )
    for name, display_name, visuals in pages:
        page_dir = definition / "pages" / name
        write_json(page_dir / "page.json", page_payload(name, display_name))
        for z_order, visual in enumerate(visuals):
            write_json(
                page_dir / "visuals" / visual.name / "visual.json",
                visual_payload(name, visual, z_order),
            )


def build_project(root: Path, output_dir: Path, data_folder: str) -> None:
    model_dir = output_dir / f"{PROJECT_NAME}.SemanticModel"
    report_dir = output_dir / f"{PROJECT_NAME}.Report"
    base_theme_bytes = read_base_theme(report_dir)
    # Remove generated content only; keep local Desktop state in .pbi/.
    for generated in [
        model_dir / "definition",
        report_dir / "definition",
        report_dir / "StaticResources",
    ]:
        if generated.exists():
            shutil.rmtree(generated)
    build_semantic_model(root, model_dir, data_folder)
    build_report(root, report_dir, base_theme_bytes)
    write_json(
        output_dir / f"{PROJECT_NAME}.pbip",
        {
            "$schema": SCHEMAS["pbip"],
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{PROJECT_NAME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--data-folder",
        default=str(root / "data" / "model"),
        help="Default value of the DataFolder parameter (folder with the model CSV files).",
    )
    args = parser.parse_args()
    build_project(root, root / "dashboard", args.data_folder)
    print(f"Power BI project written to {root / 'dashboard' / (PROJECT_NAME + '.pbip')}")


if __name__ == "__main__":
    main()
