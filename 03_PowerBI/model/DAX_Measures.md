# Step 5 — DAX measures

All 33 measures live in the **`_Measures`** table (calculator icon in the Data pane), grouped in 6 display folders.
The single source of truth is `measures_spec.py`; `add_measures.py` writes them into the model.
Validation: **60/60 checks passed**. Every Step 2 KPI is reproduced exactly, and about 50,000 measure values were checked against pandas calculations from the raw CSV.
See `../validation/validation_report_step5.txt`.

## Design rules (good interview material)
1. **`DIVIDE()` for every ratio.** An empty or zero denominator returns BLANK instead of an error or infinity.
2. **Counts return 0, not blank, when employees are selected but none match.** A team with no leavers shows *0.0%* attrition, not an empty cell. An empty selection still returns BLANK.
3. **`KEEPFILTERS()` on segment filters.** If a visual is already filtered on the same column (e.g. an OverTimeFlag axis), the measure intersects with it instead of silently overwriting it. Validated: 'Employees with No Training' shows 54 only on the 0-trainings row, not on every row.
4. **Only the company baseline removes filters (`REMOVEFILTERS()`).** That makes 'Attrition vs Company (pts)' an honest comparison: Sales is +4.5 pts above the company's 16.1%.
5. **Measures build on measures** (`[Attrition Rate] = DIVIDE([Leavers], [Headcount])`). Logic is defined once and reused.

## All measures (value = whole company)


### 1 Headcount & Attrition

| Measure | Value | What it means |
|---|---|---|
| **Headcount** | 1,470 | Number of employees in the current filter context (leavers included). |
| **Leavers** | 237 | Employees who left (AttritionFlag = 1). 0 when nobody in the selection left. |
| **Active Employees** | 1,233 | Employees still employed. |
| **Attrition Rate** | 16.1% | Leavers / Headcount. |
| **Retention Rate** | 83.9% | Active Employees / Headcount (= 1 - Attrition Rate). |
| **Company Attrition Rate** | 16.1% | Attrition rate of the whole company, ignoring every filter and slicer. Baseline for comparisons. |
| **Attrition vs Company (pts)** | +0.0 pts | Selected attrition rate minus company attrition rate, in percentage points. Positive = worse than company. |

### 2 Tenure

| Measure | Value | What it means |
|---|---|---|
| **Avg Tenure (Years)** | 7.0 | Average years at the company. |
| **Median Tenure (Years)** | 5.0 | Median years at the company (robust to very long tenures). |
| **Avg Tenure of Leavers (Years)** | 5.1 | Average years at the company of employees who left. |
| **Early Tenure Attrition Rate (0-1 yrs)** | 34.9% | Attrition rate of employees in their first 0-1 years. Basis for the onboarding recommendation. |
| **Avg Years Since Promotion** | 2.2 | Average years since the last promotion. |

### 3 Training & Learning

| Measure | Value | What it means |
|---|---|---|
| **Total Trainings** | 4,115 | Total trainings attended last year. |
| **Training per Employee** | 2.80 | Average trainings per employee last year (Total Trainings / Headcount). |
| **Employees with No Training** | 54 | Employees who attended no training last year. |
| **% No Training** | 3.7% | Share of employees with no training last year. |
| **% High Training (5-6)** | 12.5% | Share of employees with 5-6 trainings last year. |
| **Attrition Rate - No Training** | 27.8% | Attrition rate of employees with no training last year (small group - treat as indicative). |

### 4 Overtime

| Measure | Value | What it means |
|---|---|---|
| **Overtime Employees** | 416 | Employees working overtime. 0 when nobody in the selection works overtime. |
| **Overtime %** | 28.3% | Share of employees working overtime. |
| **Attrition Rate - Overtime** | 30.5% | Attrition rate of employees who work overtime. |
| **Attrition Rate - No Overtime** | 10.4% | Attrition rate of employees who do not work overtime. |
| **Overtime Attrition Ratio** | 2.9x | How many times higher attrition is with overtime than without (e.g. 2.9x). |

### 5 Satisfaction & Performance

| Measure | Value | What it means |
|---|---|---|
| **Avg Job Satisfaction** | 2.73 | Average job satisfaction, 1 (Low) to 4 (Very High). |
| **% Low Job Satisfaction** | 19.7% | Share of employees rating job satisfaction 'Low' (1). |
| **Attrition Rate - Low Job Satisfaction** | 22.8% | Attrition rate of employees with 'Low' job satisfaction. |
| **Avg Environment Satisfaction** | 2.72 | Average environment satisfaction, 1 (Low) to 4 (Very High). |
| **Avg Work-Life Balance** | 2.76 | Average work-life balance, 1 (Bad) to 4 (Best). |
| **Avg Job Involvement** | 2.73 | Average job involvement, 1 (Low) to 4 (Very High). |
| **Avg Performance Rating** | 3.15 | Average performance rating (only 3 = Excellent and 4 = Outstanding occur). |

### 6 Demographics & Pay

| Measure | Value | What it means |
|---|---|---|
| **Avg Age** | 36.9 | Average employee age. |
| **Avg Monthly Income** | 6,503 | Average monthly income (currency not stated in the source data). |
| **Avg Salary Hike (%)** | 15.2 | Average last salary increase in percent (e.g. 15.2 = 15.2%). |

## DAX code

**Headcount**  (format `#,##0`)
```DAX
COUNTROWS ( FactEmployee )
```

**Leavers**  (format `#,##0`)
```DAX
SUM ( FactEmployee[AttritionFlag] )
```

**Active Employees**  (format `#,##0`)
```DAX
[Headcount] - [Leavers]
```

**Attrition Rate**  (format `0.0%`)
```DAX
DIVIDE ( [Leavers], [Headcount] )
```

**Retention Rate**  (format `0.0%`)
```DAX
DIVIDE ( [Active Employees], [Headcount] )
```

**Company Attrition Rate**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], REMOVEFILTERS () )
```

**Attrition vs Company (pts)**  (format `+0.0%;-0.0%;0.0%`)
```DAX
VAR rate = [Attrition Rate]
RETURN
    IF ( NOT ISBLANK ( rate ), rate - [Company Attrition Rate] )
```

**Avg Tenure (Years)**  (format `0.0`)
```DAX
AVERAGE ( FactEmployee[YearsAtCompany] )
```

**Median Tenure (Years)**  (format `0.0`)
```DAX
MEDIAN ( FactEmployee[YearsAtCompany] )
```

**Avg Tenure of Leavers (Years)**  (format `0.0`)
```DAX
CALCULATE ( [Avg Tenure (Years)], KEEPFILTERS ( FactEmployee[AttritionFlag] = 1 ) )
```

**Early Tenure Attrition Rate (0-1 yrs)**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[YearsAtCompany] <= 1 ) )
```

**Avg Years Since Promotion**  (format `0.0`)
```DAX
AVERAGE ( FactEmployee[YearsSinceLastPromotion] )
```

**Total Trainings**  (format `#,##0`)
```DAX
SUM ( FactEmployee[TrainingTimesLastYear] )
```

**Training per Employee**  (format `0.00`)
```DAX
DIVIDE ( [Total Trainings], [Headcount] )
```

**Employees with No Training**  (format `#,##0`)
```DAX
VAR hc = [Headcount]
RETURN
    IF (
        NOT ISBLANK ( hc ),
        COALESCE ( CALCULATE ( [Headcount], KEEPFILTERS ( FactEmployee[TrainingTimesLastYear] = 0 ) ), 0 )
    )
```

**% No Training**  (format `0.0%`)
```DAX
DIVIDE ( [Employees with No Training], [Headcount] )
```

**% High Training (5-6)**  (format `0.0%`)
```DAX
VAR high =
    CALCULATE ( [Headcount], KEEPFILTERS ( FactEmployee[TrainingTimesLastYear] >= 5 ) )
RETURN
    DIVIDE ( COALESCE ( high, 0 ), [Headcount] )
```

**Attrition Rate - No Training**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[TrainingTimesLastYear] = 0 ) )
```

**Overtime Employees**  (format `#,##0`)
```DAX
SUM ( FactEmployee[OverTimeFlag] )
```

**Overtime %**  (format `0.0%`)
```DAX
DIVIDE ( [Overtime Employees], [Headcount] )
```

**Attrition Rate - Overtime**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[OverTimeFlag] = 1 ) )
```

**Attrition Rate - No Overtime**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[OverTimeFlag] = 0 ) )
```

**Overtime Attrition Ratio**  (format `0.0"x"`)
```DAX
DIVIDE ( [Attrition Rate - Overtime], [Attrition Rate - No Overtime] )
```

**Avg Job Satisfaction**  (format `0.00`)
```DAX
AVERAGE ( FactEmployee[JobSatisfactionScore] )
```

**% Low Job Satisfaction**  (format `0.0%`)
```DAX
VAR low =
    CALCULATE ( [Headcount], KEEPFILTERS ( FactEmployee[JobSatisfactionScore] = 1 ) )
RETURN
    DIVIDE ( COALESCE ( low, 0 ), [Headcount] )
```

**Attrition Rate - Low Job Satisfaction**  (format `0.0%`)
```DAX
CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[JobSatisfactionScore] = 1 ) )
```

**Avg Environment Satisfaction**  (format `0.00`)
```DAX
AVERAGE ( FactEmployee[EnvironmentSatisfactionScore] )
```

**Avg Work-Life Balance**  (format `0.00`)
```DAX
AVERAGE ( FactEmployee[WorkLifeBalanceScore] )
```

**Avg Job Involvement**  (format `0.00`)
```DAX
AVERAGE ( FactEmployee[JobInvolvementScore] )
```

**Avg Performance Rating**  (format `0.00`)
```DAX
AVERAGE ( FactEmployee[PerformanceRatingScore] )
```

**Avg Age**  (format `0.0`)
```DAX
AVERAGE ( FactEmployee[Age] )
```

**Avg Monthly Income**  (format `#,##0`)
```DAX
AVERAGE ( FactEmployee[MonthlyIncome] )
```

**Avg Salary Hike (%)**  (format `0.0`)
```DAX
AVERAGE ( FactEmployee[PercentSalaryHike] )
```

## Likely interview questions
- **What does CALCULATE do?** It evaluates an expression in a modified filter context, e.g. `CALCULATE([Attrition Rate], KEEPFILTERS(FactEmployee[OverTimeFlag] = 1))` is the attrition rate of overtime workers.
- **REMOVEFILTERS vs ALL?** `REMOVEFILTERS()` only removes filters, so it is used as a CALCULATE modifier. `ALL()` can also return a table. Here, `REMOVEFILTERS()` gives the company baseline.
- **Why KEEPFILTERS?** Without it, CALCULATE replaces an existing filter on the same column, so a chart with an OverTimeFlag axis would show the same number on every bar.
- **Why SUM(AttritionFlag) instead of COUNTROWS with a filter?** SUM returns 0 for a group with no leavers, which keeps the rates at 0.0% instead of blank.
- **Measure vs calculated column?** Measures are computed at query time for the current filter context and store nothing. Columns are computed at refresh and stored per row. Everything here is a measure.
