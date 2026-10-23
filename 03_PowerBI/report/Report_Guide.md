# Step 6 — Report pages

**Open:** `03_PowerBI\Talent_Learning_Dashboard.pbip`. There are 8 pages and 77 visuals.
**Validation: 43/43 checks passed** (`03_PowerBI\validation\validation_report_step6.txt`):
- Every file passes Microsoft's official report schemas.
- Every field used exists in the model.
- The layout has no overlaps.
- 7,614 displayed values match pandas calculations from the raw CSV.
- Every page was opened in Power BI and checked for error messages, chart titles and card values.

Drill-through was also tested by hand: right-clicking Sales Representative leads to Employee Details with 83 employees, 33 leavers and 39.8% attrition, and the Back button returns to the previous page.

## Pages
| # | Page | What it answers | Visuals |
|---|---|---|---|
| 1 | **Overview** | How big is attrition and where is it concentrated? | 6 KPI cards; attrition by job role, department, tenure, overtime and training level |
| 2 | **Insights & Actions** | What should HR do about it? | 4 live KPI cards; 4 evidence-based recommendations (full write-up in `04_Docs/Insights_and_Recommendations.md`) |
| 3 | **Attrition Drivers** | Which groups leave most? | Overtime / tenure / satisfaction cards; attrition by age, job level, stock options, marital status, travel and income |
| 4 | **Training & Learning** | Who gets trained, and does it relate to attrition? | Training KPIs; employees and attrition by training band; trainings per employee by role, department and tenure |
| 5 | **Satisfaction & Performance** | Do ratings predict attrition? | Satisfaction KPIs; attrition by job satisfaction, work-life balance, environment satisfaction and performance |
| 6 | **Job Role Summary** | Which roles need attention first? | Matrix of 9 key measures per role, sorted by attrition gap; gap-vs-company bar chart |
| 7 | **Employee Details** | Who exactly is in this group? | Drill-through page: cards and an employee list for the job role you drilled from |
| 8 | **Data Quality** | Can I trust the numbers? | The 35 `QA_Checks`, recalculated on every refresh |

Every analysis page has **Department** and **Job role** slicers (drop-downs, top right).

## How to use
- **Filter:** use the slicers, or click a bar to cross-filter the other visuals on the page.
- **Drill through:** right-click any job role (a bar or a matrix row) and choose **Drill through → Employee Details**.
- **Back button:** in Power BI Desktop, **Ctrl+click** buttons. In the published report, a normal click works.
- In Attrition vs Company (pts), a value of **-0.0%** means very slightly below the company rate (Research Scientist: -0.03 points).

## Key findings to present (all verified against the raw data)
1. **Overtime is the strongest driver.** Attrition is 30.5% with overtime vs 10.4% without (2.9x), and 28.3% of staff work overtime.
2. **The first year is critical.** Attrition is 34.9% at 0–1 years of tenure vs 8.1% at 11+ years, so onboarding and mentoring is the lever.
3. **Sales Representatives are the hotspot.** They have 39.8% attrition, +23.6 points above the company rate. Laboratory Technicians (+7.8) and HR (+7.0) follow.
4. **Satisfaction matters.** Low job satisfaction means 22.8% attrition vs 11.3% at Very High, and bad work-life balance means 31.3%.
5. **Training is a weaker signal than it looks.** The no-training group has 27.8% attrition, but it is only 54 people. Trainings per employee are flat across tenure (2.76–2.93), so new joiners get no extra learning support.
6. **Performance rating does not predict attrition** (16.1% vs 16.4%), which suggests the rating scale doesn't separate people well.

## Design choices (interview talking points)
- One question per page, with KPI cards on top and detail below, read left to right.
- Each chart title states the question; redundant axis titles are removed.
- Bands and ratings appear in logical order (thanks to the sort-by columns from Step 4), not alphabetically.
- The employee table uses the raw fact columns (Sum per employee), so each person shows their real age and income, and there is no misleading totals row.
- The report is self-auditing: the Data Quality page shows the model's 35 automatic checks.
- Everything is generated from `03_PowerBI/report/build_report.py`, so the whole report can be rebuilt and version-controlled.
