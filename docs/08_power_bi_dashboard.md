# Stage 8 — Power BI Dashboard Design

## Goal

This stage turns the analytical model and KPI definitions into a six-page Power BI report. The report is designed for a laptop screen and uses a fixed 16:9 canvas of 1280 × 720 pixels.

The package contains the page plan, visual specifications, theme, wireframes and the additional DAX measures needed for interactions and time comparisons. It does not contain a `.pbix` file; the report must be assembled in Power BI Desktop using the model created in Stage 5.

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
