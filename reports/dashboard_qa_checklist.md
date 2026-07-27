# Dashboard QA Checklist

## Model

- [ ] All dimension-to-fact relationships are one-to-many.
- [ ] Cross-filter direction is single.
- [ ] The transaction-date relationship is active.
- [ ] The stock-date relationship is inactive.
- [ ] DimDate is marked as the date table.
- [ ] Month and year-month labels use the correct sort columns.

## Measures

- [ ] Full-period values match the Stage 7 KPI snapshot.
- [ ] Revenue Growth % is blank when no previous-year period exists.
- [ ] Same-Store Revenue Growth % only uses comparable stores.
- [ ] Sales Lines is not presented as Total Orders.
- [ ] Gross Product Profit is not presented as Net Profit.
- [ ] Return rates include quantity context.

## Layout and readability

- [ ] Each page has one clear management question.
- [ ] KPI cards fit without clipped labels.
- [ ] All charts have a descriptive title.
- [ ] Currency and percentage formats are consistent.
- [ ] Long product and store names remain readable.
- [ ] Visuals remain usable on a 1366 × 768 laptop screen.
- [ ] Color is not the only way risk or selection is communicated.

## Interaction

- [ ] KPI cards do not cross-filter other visuals.
- [ ] Bar and line charts filter the intended visuals only.
- [ ] Drill-through retains the selected store or product context.
- [ ] Tooltip pages show the correct entity.
- [ ] Reset Filters bookmarks restore the agreed default state.
- [ ] Navigation buttons point to the correct pages.

## Final review

- [ ] Executive Overview can be understood in under one minute.
- [ ] Reported growth and same-store growth are shown together.
- [ ] No unsupported targets or thresholds are presented as facts.
- [ ] Screenshots do not contain edit-mode panes or selection borders.
- [ ] The final `.pbix` and exported PDF use the same page order.
