# Step 4 — Data model (star schema)

**File to open:** `03_PowerBI\Talent_Learning_Dashboard.pbip` (double-click, or open it from Power BI Desktop with File → Open).

This is a **Power BI Project (PBIP)**: the model is stored as readable text (TMDL) instead of one binary .pbix.
It holds the same thing as a .pbix and opens the same way, and every change shows up line by line on GitHub.
Validation: **68/68 checks passed**, including a full refresh and DAX tests inside your Power BI Desktop.
See `03_PowerBI\validation\validation_report_step4.txt`.

## First time you open it
1. Open the `.pbip`. The model opens without data, because data is never stored in the project files.
2. Click **Home → Refresh**. It takes about 15 seconds and loads all 1,470 employees.
3. Press **Ctrl+S**. Power BI then saves a local data cache, so the next open is instant. The cache is git-ignored.
4. Want a single file to email or upload? Use **File → Save as → Power BI file (.pbix)**.

## Star schema

```
 DimDepartment   DimJobRole   DimEducation   DimJobSatisfaction   DimEmployee
        \             |             |               |                 /
         \            |             |               |                /
          '-------------------- FactEmployee --------------------'
         /            |             |               |
 DimAgeBand    DimTenureBand   DimIncomeBand   DimTrainingBand

 + _Measures (home of the DAX measures, Step 5)   + QA_Checks (hidden, 35 self-tests)
```

| # | From (many side) | To (one side) | Cardinality | Filter direction |
|---|---|---|---|---|
| 1 | FactEmployee[DepartmentKey] | DimDepartment[DepartmentKey] | many-to-one | Single (dim → fact) |
| 2 | FactEmployee[JobRoleKey] | DimJobRole[JobRoleKey] | many-to-one | Single |
| 3 | FactEmployee[EducationKey] | DimEducation[EducationKey] | many-to-one | Single |
| 4 | FactEmployee[JobSatisfactionKey] | DimJobSatisfaction[JobSatisfactionKey] | many-to-one | Single |
| 5 | FactEmployee[AgeBandKey] | DimAgeBand[AgeBandKey] | many-to-one | Single |
| 6 | FactEmployee[TenureBandKey] | DimTenureBand[TenureBandKey] | many-to-one | Single |
| 7 | FactEmployee[IncomeBandKey] | DimIncomeBand[IncomeBandKey] | many-to-one | Single |
| 8 | FactEmployee[TrainingBandKey] | DimTrainingBand[TrainingBandKey] | many-to-one | Single |
| 9 | FactEmployee[EmployeeID] | DimEmployee[EmployeeID] | many-to-one* | Single |

\* There is one row per employee on both sides. Power BI would suggest one-to-one, which forces two-way filtering.
Many-to-one with single direction keeps every relationship in the model consistent. Filters always flow from a dimension into the fact table, never backwards, so there are no ambiguous filter paths.

## Model settings
- **Sort by column**, so bands and ratings appear in logical order instead of alphabetical:
  - EducationLevel → EducationKey
  - JobSatisfaction → JobSatisfactionKey
  - AgeBand, TenureBand, IncomeBand, TrainingBand → their Key
  - DimEmployee: BusinessTravel, EnvironmentSatisfaction, RelationshipSatisfaction, JobInvolvement, WorkLifeBalance and PerformanceRating → their `…Sort` column
- **Hidden from report authors:**
  - all key columns
  - all `…Sort` columns
  - the Min/Max band bounds
  - FactEmployee[EmployeeID] (use DimEmployee[EmployeeID])
  - the QA_Checks table
  - the `_Measures` placeholder column
- **Default summarization:** IDs, keys, levels and sort columns are set to *Don't summarize*. Flags, trainings and income are *Sum*. Age, years and scores are *Average*. This stops nonsense like "Sum of Age".
- **Keys:** each dimension's key column is marked as its key (`isKey`).
- **Auto date/time is off.** The data has no dates, so there are no hidden auto date tables.
- **Descriptions** on the tables and main columns show up as tooltips in the Fields pane.

## Interview talking points
- **Why a star schema on one flat file?** Clean slicers, simple DAX, and room to add real HR tables later (courses, hires, exits) as new facts that share these dimensions.
- **Why single-direction filtering?** It is predictable and fast, and avoids ambiguity. The validation proves filters flow dimension → fact only.
- **Why surrogate keys?** Integer keys are fast to join and independent of label text, so renaming "Sales" would not break anything.
- **Why PBIP/TMDL?** It allows source control and code review of the model, and the whole model can be regenerated from `model/build_pbip.py`.
