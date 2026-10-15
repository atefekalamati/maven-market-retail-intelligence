# Stage 8 — Power BI Dashboard Design

## Goal

This stage turns the analytical model and KPI definitions into a six-page Power BI report. The report is designed for a laptop screen and uses a fixed 16:9 canvas of 1280 × 720 pixels.

The package contains the page plan, visual specifications, theme, wireframes and the additional DAX measures needed for interactions and time comparisons. The report itself is a Power BI project (`dashboard/MavenMarket.pbip`) with a TMDL semantic model and a PBIR report, generated from this design by `scripts/build_power_bi_report.py`. See [Implementation](#implementation).

## Report pages

1. **Executive Overview** — business scale, profitability, network growth and management notes.
2. **Sales Performance** — time trends, regional performance, store ranking and comparable-store growth.
3. **Product & Profitability** — product and brand contribution, margin position and return risk.
4. **Customer Analysis** — membership tiers, customer value, income bands and revenue concentration.
5. **Store & Geographic Performance** — store formats, size, productivity and geographic contribution.
6. **Returns & Detailed Analysis** — return trends, elevated return rates and record-level investigation.

## Page layout

- Canvas: 1280 × 720, 16:9.
- Outer margin: 32 pixels.
- Header: 80 pixels.
- KPI strip: 120–130 pixels.
- Main visual row: approximately 290 pixels.
- Secondary visual row: approximately 250 pixels.
- Spacing between visual containers: 14–18 pixels.
- Visual headers should be hidden unless users need export or drill controls.

## Global slicers

Use a collapsible filter panel or a compact row under the page header:

- Year
- Month
- Country
- Sales region
- Store type
- Membership tier
- Product brand

Do not place all slicers on every page. Keep Year, Country and Sales Region visible globally; expose page-specific filters only when they change a real decision.

## Interactions

- Country and region bars cross-filter store visuals.
- Store visuals support drill-through to the Returns & Detailed Analysis page.
- Product and brand visuals support drill-through to product details.
- Monthly trend charts cross-highlight the rest of the page.
- KPI cards respond to page filters but should not filter other visuals.
- The stock-date relationship in FactSales remains inactive; activate it only in measures that explicitly analyze stock dates.

## Navigation

Use six page-navigation buttons in the header. The selected page uses the teal accent; inactive pages use slate text. Add a Reset Filters bookmark to each page after the final slicer state has been agreed.

## Visual rules

- Use cards for single KPIs and charts for comparisons or patterns.
- Revenue and gross product profit may be shown together because both are monetary measures.
- Reported growth and same-store growth must appear together whenever network growth is discussed.
- Do not use `Sales Lines` as an order count.
- Do not label `Average Revenue per Sales Line` as Average Order Value.
- Product and store return rates must include a volume filter or quantity context to avoid highlighting small denominators.
- Net profit, sales targets and customer-level returns are outside the available data.

## Theme

Import `dashboard/maven_market_power_bi_theme.json` from **View → Themes → Browse for themes**. The palette uses teal for the primary series, blue for profit or comparison series, gold for contextual comparisons and dark red only for return-risk views.

## Build order

1. Load the six Star Schema tables.
2. Confirm relationships and mark `DimDate[date]` as the date table.
3. Create a dedicated Measures table.
4. Add Stage 7 KPI measures.
5. Add `dax/08_dashboard_measures.dax`.
6. Import the report theme.
7. Build the Executive Overview page first.
8. Copy the header, navigation and filter panel to the other pages.
9. Build page visuals from `dashboard_visual_specification.csv`.
10. Configure interactions, drill-through and tooltips.
11. Validate totals against the Stage 7 KPI snapshot.
12. Capture final screenshots only after desktop and laptop readability checks.

## Baseline values for validation

- Total Revenue: $1.76M
- Gross Product Profit: $1.05M
- Gross Margin: 59.7%
- Reported Revenue Growth: 112.2%
- Same-Store Revenue Growth: 8.4%
- Active Customers: 8,842
- Return Quantity Rate: 1.0%

These values represent the full 1997–1998 dataset with no page filters. Filtered report views will differ.

## Implementation

### Files

```text
dashboard/
├── MavenMarket.pbip                 # open this file in Power BI Desktop
├── MavenMarket.SemanticModel/       # TMDL model
│   └── definition/
│       ├── expressions.tmdl         # DataFolder parameter
│       ├── relationships.tmdl
│       └── tables/*.tmdl
└── MavenMarket.Report/              # PBIR report: 6 pages, 121 visuals
    ├── definition/pages/<page>/visuals/<visual>/visual.json
    └── StaticResources/             # base theme and the Maven Market theme
```

The project files are generated, not edited by hand. Change the design in `scripts/build_power_bi_report.py` (layout, visuals) or in `dax/` (measures), then rebuild:

```powershell
python scripts/build_power_bi_report.py
```

The build is deterministic: identifiers are derived from names, and no timestamps are written.

### Semantic model

- Six import tables read the `data/model` CSV files through the `DataFolder` text parameter. The default value is the absolute path of this repository's `data/model` folder; change it under **Transform data → Edit parameters** on another machine.
- `_Measures` holds all 63 measures from `dax/07_kpi_measures.dax` and `dax/08_dashboard_measures.dax`, in the display folders from the build guide.
- Relationships follow `reports/model_relationships.csv`: single-direction one-to-many, with the stock-date relationship inactive.
- `DimDate` is marked as the date table (`DimDate[date]`). Auto date/time is off. `maxParallelismPerRefresh` is 1. Implicit measures are disabled.
- `CustomerPercentile` is a calculated table (1–100) used by the customer concentration curve.

### Report rules

- Card values are 20 pt with 9 pt labels. Every page has a title, a one-line finding subtitle and a source footer.
- Every visual sits inside the 1280 × 720 canvas, and no two visuals overlap.
- Table totals are off, and tables limit their rows so they fit without scrollbars.
- Bar charts show at most seven bars. At Power BI's minimum bar thickness (20 px), seven is the most a 238 px chart fits without a scrollbar.
- Return-rate colours use fx rules on `[Return Rate vs Overall (pp)]`: dark red at ≥ 0.50 pp above the network rate, amber at ≥ 0.15 pp, slate otherwise. These are the same thresholds as `[Return Review Flag]`.
- `Return Quantity Rate %` is labelled **Return rate (proxy)** everywhere.

### Deviations from the visual specification

| Spec | Implemented | Reason |
|---|---|---|
| Top 8 / Top 10 bar charts | Top 7 | Larger rankings need a scrollbar at this row height. |
| OV-03 / SA growth cards on `[Revenue Growth %]` | `[Latest Year Revenue Growth %]`, `[Latest Year Same-Store Revenue Growth %]` | Without a year filter, `[Revenue Growth %]` compares 1997–1998 with 1996–1997 (212%). The latest-year measures give the 1998 values (112.2%, 8.4%) and are blank when no prior year exists. |
| RE-04 row-level transaction table | Top 6 stores by returned units | A row-level table cannot fit without scrollbars. Drill-through from store and product visuals still filters this page. |
| CU-03 horizontal bar | Column chart in income order | Eight bands do not fit as bars without a scrollbar. |
| PR-04 / RE-03 minimum-volume filter | `[Product Return Rate (300+ Units) %]` | A measure-level threshold works together with the Top N filter. |
| Product and store tooltip pages | Tooltip fields on the visuals | Not built. Create them in Desktop if needed. |
| Reset Filters bookmark | Not built | Add it after the final slicer state is agreed, as planned above. |

### Validation

| Check | Command | Result |
|---|---|---|
| PBIR files against Microsoft's JSON schemas | `python -m pytest tests/test_layout.py` | passed |
| TMDL parse with Power BI Desktop's Tabular Object Model | `python -m pytest tests/test_model.py` | passed |
| All 63 measures on the Power BI Desktop engine | `python scripts/validate_power_bi_measures.py --refresh` (report open in Desktop) | 124 of 124 checks passed |
| Layout rules, pipeline reconciliation | `python -m pytest` | passed |

Measure results are in `reports/power_bi_measure_validation.csv`. Seventy-three checks compare KPI measures with `reports/kpi_baseline_snapshot.csv` (full period, 1997, 1998). Fifty-one checks compare the remaining measures with values calculated in pandas from the model CSV files. Per-unit ratios such as Revenue per Active Customer are compared to four decimal places, because the engine returns `DIVIDE(fixed decimal, whole number)` as a fixed decimal number.

The vendored schemas in `tests/schemas/` can be refreshed with `python tests/fetch_pbir_schemas.py`.

### Export

`dashboard/dashboard.pdf` was exported from Power BI Desktop (**File → Export → Export to PDF**) after a full refresh. `python scripts/export_dashboard_images.py` removes the PDF's creation timestamp and renders the six pages to `images/dashboard/`.

The model tables carry `annotation PBI_ResultType = Table`. Without it, Power BI Desktop evaluates every query in parallel when the file opens, which can exhaust memory on an 8–16 GB machine.

