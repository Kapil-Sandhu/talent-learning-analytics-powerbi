# Step 3 — Power Query: setup guide

All 25 queries in this folder were tested in the real Power Query engine (Excel, same engine as Power BI).
Every output table matched the independent Python check cell by cell, and all 35 QA checks passed.
See `../validation/validation_report_step3.txt`.

## 0. Before you start
- Install **Power BI Desktop** (free, Microsoft Store). It is not installed on this computer yet.
- Keep the folder structure as it is; the queries read
  `01_Data\raw\WA_Fn-UseC_-HR-Employee-Attrition.csv` and `01_Data\lookups\HR_Lookups.xlsx`.

## 1. Query map (build order = file number)

| # | Query | Role | Load? | Rows | Cols |
|---|---|---|---|---|---|
| 00 | ProjectFolder | Parameter: project root folder | – | – | – |
| 01 | fnGetLookup | Function: read one table from HR_Lookups.xlsx | No | – | – |
| 02 | fnBandKey | Function: value → band key (errors if no band fits) | No | – | – |
| 10 | src_HR | Raw CSV, UTF-8, 35 explicit types | **No** | 1,470 | 35 |
| 11–15 | lkp_Education, lkp_Satisfaction, lkp_WorkLifeBalance, lkp_PerformanceRating, lkp_BusinessTravel | Code → label lookups | **No** | 5/4/4/4/3 | 3 |
| 16–19 | lkp_AgeBand, lkp_TenureBand, lkp_IncomeBand, lkp_TrainingBand | Band lookups (Band, Min, Max, BandKey) | **No** | 5/4/5/4 | 4 |
| 20 | stg_HR | Cleaned + flags + band keys + labels | **No** | 1,470 | 43 |
| 30 | DimDepartment | Dimension | Yes | 3 | 2 |
| 31 | DimJobRole | Dimension | Yes | 9 | 2 |
| 32 | DimEducation | Dimension | Yes | 5 | 2 |
| 33 | DimJobSatisfaction | Dimension | Yes | 4 | 2 |
| 34 | DimAgeBand | Dimension | Yes | 5 | 4 |
| 35 | DimTenureBand | Dimension | Yes | 4 | 4 |
| 36 | DimIncomeBand | Dimension | Yes | 5 | 4 |
| 37 | DimTrainingBand | Dimension | Yes | 4 | 4 |
| 38 | DimEmployee | Employee attributes (slicers, drill-through) | Yes | 1,470 | 20 |
| 40 | FactEmployee | Fact table: keys + numbers for DAX | Yes | 1,470 | 28 |
| 50 | QA_Checks | 35 automatic checks, must all be PASS | Yes (hide) | 35 | 5 |

## 2. Build it in Power BI Desktop (about 20 minutes)
1. Open Power BI Desktop → **Home → Transform data**. This opens the Power Query Editor.
2. **Create the parameter:** Home → Manage Parameters → New.
   Name `ProjectFolder`, Type **Text**, Current value `D:\Ai Projects\Power BI\` → OK.
3. **For every other file, in number order (01 → 50):**
   1. Home → New Source → **Blank Query**.
   2. Home → **Advanced Editor**, delete what is there, paste the whole file content, then click **Done**.
   3. Rename the query (right-click → Rename) to the exact name on the file's first line, e.g. `fnGetLookup`.
      Names must match exactly, because the queries refer to each other by name.
4. **Turn off loading for staging queries.** Right-click each query marked *do not load* (src_HR, all lkp_*, stg_HR) and untick **Enable load**. The staging queries then appear in italics.
5. Optional, but it looks professional: right-click → **Move to group** to create the groups
   `Parameters`, `Functions`, `Staging`, `Model`, `QA`.
6. **Privacy prompt.** If Power BI asks about privacy levels, set both files to the **same level** (e.g. Organizational).
7. **Home → Close & Apply.**
8. In **Data view**, open `QA_Checks`. All 35 rows must say **PASS**.
   Then, in Report view, right-click `QA_Checks` → **Hide in report view**.
9. Save as `03_PowerBI\Talent_Learning_Dashboard.pbix`.

If a query shows an error: check its name spelling first, then that the `ProjectFolder` value is correct.

## 3. What each design choice is for (interview talking points)
- **Parameter for the folder.** Moving the project means changing one value. Both file paths work with or without a trailing backslash; that bug was found and fixed during testing.
- **Explicit data types on all 35 columns.** Nothing depends on automatic type detection, which can guess wrong or break when the data changes.
- **UTF-8 (65001) encoding.** It removes the hidden BOM character in front of the first header (`Age`).
- **Six columns dropped.** Three are constants (`EmployeeCount`, `Over18`, `StandardHours`); three are undocumented rates (`DailyRate`, `HourlyRate`, `MonthlyRate`).
- **Lookups live in Excel tables, not in code.** HR can rename a label or move a band boundary without touching M.
- **`fnBandKey` raises an error** if a value fits no band or two bands. Bad band definitions fail loudly instead of silently producing blanks.
- **Merge Queries (left outer join)** turn rating codes into labels; Merge Queries also look up the surrogate keys in the fact table.
- **Staging is separate from the model.** Only clean dimension and fact tables reach the model; staging queries are not loaded.
- **`QA_Checks` is a self-testing model.** Every refresh re-checks row counts, duplicates, nulls, orphan keys and control totals.

## 4. Relationships for Step 4 (preview)
All 9 relationships are many-to-one, single direction (dimension → `FactEmployee`), including DimEmployee. Built and validated in Step 4; see `../model/Model_Design.md`.

| From (1 side) | To (many side) |
|---|---|
| DimDepartment[DepartmentKey] | FactEmployee[DepartmentKey] |
| DimJobRole[JobRoleKey] | FactEmployee[JobRoleKey] |
| DimEducation[EducationKey] | FactEmployee[EducationKey] |
| DimJobSatisfaction[JobSatisfactionKey] | FactEmployee[JobSatisfactionKey] |
| DimAgeBand[AgeBandKey] | FactEmployee[AgeBandKey] |
| DimTenureBand[TenureBandKey] | FactEmployee[TenureBandKey] |
| DimIncomeBand[IncomeBandKey] | FactEmployee[IncomeBandKey] |
| DimTrainingBand[TrainingBandKey] | FactEmployee[TrainingBandKey] |
| DimEmployee[EmployeeID] | FactEmployee[EmployeeID] |
