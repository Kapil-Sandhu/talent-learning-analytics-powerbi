# Talent & Learning Analytics Dashboard — System Design

**Tools:** Power BI, Excel, Power Query, DAX
**Dataset:** IBM HR Analytics Employee Attrition & Performance (Kaggle) — 1,470 employees × 35 columns
**Goal:** Track headcount, attrition, training activity, performance and job satisfaction by department, role and tenure; identify attrition drivers and give recommendations to HR stakeholders.

---

## 1. Architecture

```
┌─────────────────────┐    ┌──────────────────────┐
│ 1. SOURCE           │    │ 2. EXCEL             │
│ IBM HR CSV          │    │ - Data profiling     │
│ (1,470 × 35)        │    │   (pivot tables)     │
└─────────┬───────────┘    │ - Lookup tables      │
          │                │   (code → label)     │
          ▼                └──────────┬───────────┘
┌──────────────────────────────────────▼─────────┐
│ 3. POWER QUERY (ETL)                           │
│ clean → set types → map codes → build bands    │
│ (age, tenure, income) → split into dims + fact │
└─────────────────────┬──────────────────────────┘
                      ▼
┌────────────────────────────────────────────────┐
│ 4. DATA MODEL (star schema)                    │
│   DimDepartment  DimJobRole  DimEducation      │
│   DimJobSatisfaction        DimEmployee (1:1)  │
│              \      |      /                   │
│               FactEmployee (1 row/employee)    │
│              /      |      \                   │
│   DimAgeBand  DimTenureBand  DimIncomeBand     │
│   DimTrainingBand        (+ QA_Checks, hidden) │
└─────────────────────┬──────────────────────────┘
                      ▼
┌────────────────────────────────────────────────┐
│ 5. DAX MEASURES (_Measures table)              │
│ Headcount, Attrition %, Avg Tenure,            │
│ Training/Employee, Overtime %, vs-Company gap  │
└─────────────────────┬──────────────────────────┘
                      ▼
┌────────────────────────────────────────────────┐
│ 6. REPORT: Overview │ Attrition │ Training &   │
│ Learning │ Satisfaction & Performance │        │
│ Employee drill-through                         │
└─────────────────────┬──────────────────────────┘
                      ▼
   7. OUTPUTS: .pbix · PDF export · 5-slide deck
               · user guide · GitHub README
```

### Key design decisions (be ready to explain these)

- **Why a star schema on one flat file?** 1,470 rows don't strictly need one. Splitting into dimensions + a fact table gives clean slicers, simpler DAX, and a model that scales if real HRIS tables (courses, hires, exits) are added later.
- **The data is a snapshot — there are no dates.** No time intelligence, no "attrition trend over months". If asked: it's point-in-time data.
- **"Training activity" = `TrainingTimesLastYear` (0–6).** It's the only learning field. It supports "training per employee" and "% with zero training".

---

## 2. Folder structure

```
Power BI/
├── 01_Data/raw/          ← original CSV, never edited
├── 01_Data/lookups/      ← HR_Lookups.xlsx
├── 02_Excel_Profiling/   ← profiling workbook
├── 03_PowerBI/           ← Talent_Learning_Dashboard.pbix
├── 04_Docs/              ← user guide, DAX reference
├── 05_Presentation/      ← findings deck
├── screenshots/
├── System Design.md      ← this file
└── README.md
```

---

## 3. Step-by-step build

### Step 1 — Get the data and set up folders (30 min)
- Download "IBM HR Analytics Employee Attrition & Performance" from Kaggle.
- Put the CSV in `01_Data/raw/` and create the folder structure above.

### Step 2 — Profile the data in Excel (1–2 h)
- Pivot tables: attrition by department, by overtime, by job satisfaction — first look at the drivers.
- Note the constant columns to drop: `EmployeeCount`, `Over18`, `StandardHours`.
- Create `HR_Lookups.xlsx` with mapping tables:
  - Education 1–5 → Below College, College, Bachelor, Master, Doctor
  - Satisfaction / involvement 1–4 → Low, Medium, High, Very High
  - Work-life balance 1–4 → Bad, Good, Better, Best
  - Performance rating 1–4 → Low, Good, Excellent, Outstanding (only 3 and 4 occur)
  - Business travel codes → No Travel, Travels Rarely, Travels Frequently
  - Band tables: Age, Tenure, Income, Training (inclusive Min/Max + SortOrder)

### Step 3 — Power Query ETL (2–3 h)
- Import the CSV and lookups; set data types.
- Drop constant columns (`EmployeeCount`, `Over18`, `StandardHours`) and the undocumented rate columns (`DailyRate`, `HourlyRate`, `MonthlyRate`); use `EmployeeNumber` as `EmployeeID`.
- Set file origin to UTF-8 (65001) on import - the CSV starts with a BOM before `Age`.
- Add `AttritionFlag` (Yes → 1, No → 0) and `OverTimeFlag`.
- Add bands:
  - Age: 18–25, 26–35, 36–45, 46–55, 55+
  - Tenure (YearsAtCompany): 0–1, 2–5, 6–10, 11+ years
  - Monthly income bands
- Merge in lookup labels.
- Create dimension tables as **reference queries** (Remove Other Columns → Remove Duplicates → add key).
- Fact table keeps only keys + numeric columns.
- **Built and validated:** 25 queries in `03_PowerBI/PowerQuery/` (1 parameter, 2 functions, 10 staging, 11 loaded).
  Setup guide: `03_PowerBI/PowerQuery/README_PowerQuery_Setup.md`.
- Final model tables: FactEmployee (1,470 × 28), DimEmployee (1,470 × 20), DimDepartment, DimJobRole, DimEducation,
  DimJobSatisfaction, DimAgeBand, DimTenureBand, DimIncomeBand, DimTrainingBand, plus QA_Checks (35 self-tests, hidden).
- Job satisfaction (key driver) has its own dimension; the other ratings are labelled attributes of DimEmployee
  with *Sort columns for correct ordering.

### Step 4 — Data model (1 h)
- One-to-many relationships from each dimension to `FactEmployee`, single-direction filtering.
- Hide key columns from report view.
- Set **sort by column** on bands (so "0–1 yrs" sorts before "10+").
- Create an empty `_Measures` table to hold all measures.
- **Built and validated:** Power BI Project `03_PowerBI/Talent_Learning_Dashboard.pbip` (TMDL text format, Git-friendly).
  9 many-to-one single-direction relationships (incl. DimEmployee), sort-by columns, hidden keys, default summarization,
  `_Measures` home table, auto date/time off. Design notes: `03_PowerBI/model/Model_Design.md`.
- First open: Home -> Refresh, then Ctrl+S. For a single file: File -> Save as -> .pbix.

### Step 5 — DAX measures (2 h)

```DAX
Headcount         = COUNTROWS(FactEmployee)

Leavers           = CALCULATE([Headcount], FactEmployee[AttritionFlag] = 1)

Active Employees  = [Headcount] - [Leavers]

Attrition Rate    = DIVIDE([Leavers], [Headcount])

Avg Tenure        = AVERAGE(FactEmployee[YearsAtCompany])

Training per Emp  = DIVIDE(SUM(FactEmployee[TrainingTimesLastYear]), [Headcount])

% Zero Training   = DIVIDE(
                        CALCULATE([Headcount], FactEmployee[TrainingTimesLastYear] = 0),
                        [Headcount]
                    )

Overtime %        = DIVIDE(CALCULATE([Headcount], FactEmployee[OverTimeFlag] = 1), [Headcount])

Company Attrition = CALCULATE([Attrition Rate], REMOVEFILTERS())

Attrition vs Company = [Attrition Rate] - [Company Attrition]
```

Understand every measure well enough to explain it — `CALCULATE` and `REMOVEFILTERS` are the most common interview questions.
- **Built and validated:** 33 measures in `_Measures` (6 display folders) - definitions in `03_PowerBI/model/measures_spec.py`,
  documentation + DAX code in `03_PowerBI/model/DAX_Measures.md`. Rules: DIVIDE for ratios, 0-not-blank counts,
  KEEPFILTERS on segment filters, REMOVEFILTERS only for the company baseline.

### Step 6 — Report pages (4–6 h)
1. **Overview** — KPI cards (headcount, attrition %, avg tenure, training/employee); slicers for department, role, gender.
2. **Attrition** — rate by department, role, tenure band, overtime; matrix with conditional formatting.
3. **Training & Learning** — training-times distribution, attrition by training level, % zero training by role. *(Most relevant page for a DHL talent & learning role.)*
4. **Satisfaction & Performance** — job / environment / work-life-balance ratings vs attrition.
5. **Employee drill-through** — right-click a role or department to see its employee list.

Polish: one consistent colour theme, tooltips, bookmarks or a reset-filters button.
- **Built and validated:** 8 pages / 77 visuals - Overview, Insights & Actions (added in Step 7), Attrition Drivers, Training & Learning, Satisfaction & Performance,
  Job Role Summary, Employee Details (drill-through on job role, with Back button), Data Quality. Generated by
  `03_PowerBI/report/build_report.py`; guide + key findings in `03_PowerBI/report/Report_Guide.md`.

### Step 7 — Insights and recommendations (1–2 h)
Drivers the dataset supports (confirm exact numbers from your own model):
- **Overtime** — roughly 30% attrition with overtime vs ~10% without.
- **Low job satisfaction** — highest attrition at satisfaction level 1.
- **Early tenure** — employees in their first 0–2 years leave most.

Example recommendations:
- Onboarding + mentoring programme for the first two years.
- Overtime review for high-risk roles.
- Targeted training for roles with low training activity.

### Step 8 — Documentation and deliverables (2–3 h)
- **5-slide deck:** problem → data → model → findings → recommendations.
- **User guide (1–2 pages):** using slicers and drill-through, KPI definitions.
- **GitHub README:** screenshots, model diagram, DAX reference, how to open the file. The repo must be public and look finished (it's linked on the CV).

### Step 9 — Interview prep (1 h)
Practise a 2-minute dashboard walkthrough and answers to:
- "Why a star schema?"
- "Explain this DAX measure."
- "What would you do with real DHL data?"

**Total estimated effort: ~2–3 focused days.**

---

## 4. Progress checklist

- [x] 1. Data downloaded, folders created (validated 36/36 - `01_Data/validation_report_step1.txt`)
- [x] 2. Excel profiling + lookup workbook (validated 137/137 - `02_Excel_Profiling/validation_report_step2.txt`)
- [x] 3. Power Query ETL (validated 126/126 incl. run in the real Power Query engine - `03_PowerBI/validation/validation_report_step3.txt`)
- [x] 4. Star schema model (validated 68/68 incl. refresh + DAX tests inside Power BI Desktop - `03_PowerBI/validation/validation_report_step4.txt`)
- [x] 5. DAX measures (validated 60/60: all Step 2 KPIs reproduced, 50,523 values vs raw CSV - `03_PowerBI/validation/validation_report_step5.txt`)
- [x] 6. Report pages (validated 43/43 after adding the Insights page: official schemas, fields, layout, 7,614 values vs raw CSV, all 8 pages rendered in Power BI, drill-through tested by hand - `03_PowerBI/validation/validation_report_step6.txt`)
- [x] 7. Insights & recommendations (validated 28/28 + 18/18 planted faults caught: stats re-computed independently, every number reconciled with Power BI incl. displayed rounding, no hand-typed numbers - `04_Docs/Insights_and_Recommendations.md`, `04_Docs/analysis/validation_report_step7.txt`)
- [x] 8. Deck, user guide, README, GitHub-ready repo (validated 45/45 + 27/27 planted faults caught: every number traced to its source and re-checked, DAX reference == model, links and paths exist, git dry run clean - `04_Docs/analysis/validation_report_step8.txt`; upload to GitHub is the next step)
- [ ] 9. Interview walkthrough practised
