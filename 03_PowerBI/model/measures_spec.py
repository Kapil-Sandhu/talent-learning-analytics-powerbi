"""
Step 5 - single source of truth for every DAX measure in the model.
Used by add_measures.py (writes _Measures.tmdl), the docs generator and validate_step5.py.

Design rules applied to every measure:
  * DIVIDE() for every ratio, so a 0 or empty denominator gives BLANK instead of an error / infinity.
  * Counts are 0 (not blank) when employees are in context but none match, so rates show 0.0% instead of blank.
  * Segment filters use KEEPFILTERS(), so a visual already filtered on the same column is respected (intersection),
    not silently overridden.
  * Only the company baseline removes filters (REMOVEFILTERS()).
"""

F1, F2, F3, F4, F5, F6 = ("1 Headcount & Attrition", "2 Tenure", "3 Training & Learning", "4 Overtime",
                          "5 Satisfaction & Performance", "6 Demographics & Pay")
CNT, PCT, PTS, DEC1, DEC2, MONEY, RATIO = "#,##0", "0.0%", "+0.0%;-0.0%;0.0%", "0.0", "0.00", "#,##0", '0.0"x"'

def seg_count(cond):
    """Employees matching a condition; 0 if employees are in context but none match; blank if no employees."""
    return ["VAR hc = [Headcount]",
            "RETURN",
            "    IF (",
            "        NOT ISBLANK ( hc ),",
            f"        COALESCE ( CALCULATE ( [Headcount], KEEPFILTERS ( {cond} ) ), 0 )",
            "    )"]

MEASURES = [
    # ---------------------------------------------------------------- 1 Headcount & Attrition
    dict(name="Headcount", folder=F1, fmt=CNT, expr=["COUNTROWS ( FactEmployee )"],
         desc="Number of employees in the current filter context (leavers included)."),
    dict(name="Leavers", folder=F1, fmt=CNT, expr=["SUM ( FactEmployee[AttritionFlag] )"],
         desc="Employees who left (AttritionFlag = 1). 0 when nobody in the selection left."),
    dict(name="Active Employees", folder=F1, fmt=CNT, expr=["[Headcount] - [Leavers]"],
         desc="Employees still employed."),
    dict(name="Attrition Rate", folder=F1, fmt=PCT, expr=["DIVIDE ( [Leavers], [Headcount] )"],
         desc="Leavers / Headcount."),
    dict(name="Retention Rate", folder=F1, fmt=PCT, expr=["DIVIDE ( [Active Employees], [Headcount] )"],
         desc="Active Employees / Headcount (= 1 - Attrition Rate)."),
    dict(name="Company Attrition Rate", folder=F1, fmt=PCT, expr=["CALCULATE ( [Attrition Rate], REMOVEFILTERS () )"],
         desc="Attrition rate of the whole company, ignoring every filter and slicer. Baseline for comparisons."),
    dict(name="Attrition vs Company (pts)", folder=F1, fmt=PTS,
         expr=["VAR rate = [Attrition Rate]", "RETURN", "    IF ( NOT ISBLANK ( rate ), rate - [Company Attrition Rate] )"],
         desc="Selected attrition rate minus company attrition rate, in percentage points. Positive = worse than company."),
    # ---------------------------------------------------------------- 2 Tenure
    dict(name="Avg Tenure (Years)", folder=F2, fmt=DEC1, expr=["AVERAGE ( FactEmployee[YearsAtCompany] )"],
         desc="Average years at the company."),
    dict(name="Median Tenure (Years)", folder=F2, fmt=DEC1, expr=["MEDIAN ( FactEmployee[YearsAtCompany] )"],
         desc="Median years at the company (robust to very long tenures)."),
    dict(name="Avg Tenure of Leavers (Years)", folder=F2, fmt=DEC1,
         expr=["CALCULATE ( [Avg Tenure (Years)], KEEPFILTERS ( FactEmployee[AttritionFlag] = 1 ) )"],
         desc="Average years at the company of employees who left."),
    dict(name="Early Tenure Attrition Rate (0-1 yrs)", folder=F2, fmt=PCT,
         expr=["CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[YearsAtCompany] <= 1 ) )"],
         desc="Attrition rate of employees in their first 0-1 years. Basis for the onboarding recommendation."),
    dict(name="Avg Years Since Promotion", folder=F2, fmt=DEC1, expr=["AVERAGE ( FactEmployee[YearsSinceLastPromotion] )"],
         desc="Average years since the last promotion."),
    # ---------------------------------------------------------------- 3 Training & Learning
    dict(name="Total Trainings", folder=F3, fmt=CNT, expr=["SUM ( FactEmployee[TrainingTimesLastYear] )"],
         desc="Total trainings attended last year."),
    dict(name="Training per Employee", folder=F3, fmt=DEC2, expr=["DIVIDE ( [Total Trainings], [Headcount] )"],
         desc="Average trainings per employee last year (Total Trainings / Headcount)."),
    dict(name="Employees with No Training", folder=F3, fmt=CNT, expr=seg_count("FactEmployee[TrainingTimesLastYear] = 0"),
         desc="Employees who attended no training last year."),
    dict(name="% No Training", folder=F3, fmt=PCT, expr=["DIVIDE ( [Employees with No Training], [Headcount] )"],
         desc="Share of employees with no training last year."),
    dict(name="% High Training (5-6)", folder=F3, fmt=PCT,
         expr=["VAR high =", "    CALCULATE ( [Headcount], KEEPFILTERS ( FactEmployee[TrainingTimesLastYear] >= 5 ) )",
               "RETURN", "    DIVIDE ( COALESCE ( high, 0 ), [Headcount] )"],
         desc="Share of employees with 5-6 trainings last year."),
    dict(name="Attrition Rate - No Training", folder=F3, fmt=PCT,
         expr=["CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[TrainingTimesLastYear] = 0 ) )"],
         desc="Attrition rate of employees with no training last year (small group - treat as indicative)."),
    # ---------------------------------------------------------------- 4 Overtime
    dict(name="Overtime Employees", folder=F4, fmt=CNT, expr=["SUM ( FactEmployee[OverTimeFlag] )"],
         desc="Employees working overtime. 0 when nobody in the selection works overtime."),
    dict(name="Overtime %", folder=F4, fmt=PCT, expr=["DIVIDE ( [Overtime Employees], [Headcount] )"],
         desc="Share of employees working overtime."),
    dict(name="Attrition Rate - Overtime", folder=F4, fmt=PCT,
         expr=["CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[OverTimeFlag] = 1 ) )"],
         desc="Attrition rate of employees who work overtime."),
    dict(name="Attrition Rate - No Overtime", folder=F4, fmt=PCT,
         expr=["CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[OverTimeFlag] = 0 ) )"],
         desc="Attrition rate of employees who do not work overtime."),
    dict(name="Overtime Attrition Ratio", folder=F4, fmt=RATIO,
         expr=["DIVIDE ( [Attrition Rate - Overtime], [Attrition Rate - No Overtime] )"],
         desc="How many times higher attrition is with overtime than without (e.g. 2.9x)."),
    # ---------------------------------------------------------------- 5 Satisfaction & Performance
    dict(name="Avg Job Satisfaction", folder=F5, fmt=DEC2, expr=["AVERAGE ( FactEmployee[JobSatisfactionScore] )"],
         desc="Average job satisfaction, 1 (Low) to 4 (Very High)."),
    dict(name="% Low Job Satisfaction", folder=F5, fmt=PCT,
         expr=["VAR low =", "    CALCULATE ( [Headcount], KEEPFILTERS ( FactEmployee[JobSatisfactionScore] = 1 ) )",
               "RETURN", "    DIVIDE ( COALESCE ( low, 0 ), [Headcount] )"],
         desc="Share of employees rating job satisfaction 'Low' (1)."),
    dict(name="Attrition Rate - Low Job Satisfaction", folder=F5, fmt=PCT,
         expr=["CALCULATE ( [Attrition Rate], KEEPFILTERS ( FactEmployee[JobSatisfactionScore] = 1 ) )"],
         desc="Attrition rate of employees with 'Low' job satisfaction."),
    dict(name="Avg Environment Satisfaction", folder=F5, fmt=DEC2, expr=["AVERAGE ( FactEmployee[EnvironmentSatisfactionScore] )"],
         desc="Average environment satisfaction, 1 (Low) to 4 (Very High)."),
    dict(name="Avg Work-Life Balance", folder=F5, fmt=DEC2, expr=["AVERAGE ( FactEmployee[WorkLifeBalanceScore] )"],
         desc="Average work-life balance, 1 (Bad) to 4 (Best)."),
    dict(name="Avg Job Involvement", folder=F5, fmt=DEC2, expr=["AVERAGE ( FactEmployee[JobInvolvementScore] )"],
         desc="Average job involvement, 1 (Low) to 4 (Very High)."),
    dict(name="Avg Performance Rating", folder=F5, fmt=DEC2, expr=["AVERAGE ( FactEmployee[PerformanceRatingScore] )"],
         desc="Average performance rating (only 3 = Excellent and 4 = Outstanding occur)."),
    # ---------------------------------------------------------------- 6 Demographics & Pay
    dict(name="Avg Age", folder=F6, fmt=DEC1, expr=["AVERAGE ( FactEmployee[Age] )"], desc="Average employee age."),
    dict(name="Avg Monthly Income", folder=F6, fmt=MONEY, expr=["AVERAGE ( FactEmployee[MonthlyIncome] )"],
         desc="Average monthly income (currency not stated in the source data)."),
    dict(name="Avg Salary Hike (%)", folder=F6, fmt=DEC1, expr=["AVERAGE ( FactEmployee[PercentSalaryHike] )"],
         desc="Average last salary increase in percent (e.g. 15.2 = 15.2%)."),
]

# Step 2 KPI_Summary row -> measure (reconciliation map: every Step 2 KPI must be reproduced exactly)
KPI_MAP = {
    "Headcount": "Headcount", "Leavers": "Leavers", "Active Employees": "Active Employees",
    "Attrition Rate": "Attrition Rate", "Avg Tenure (years)": "Avg Tenure (Years)",
    "Median Tenure (years)": "Median Tenure (Years)", "Avg Tenure - Leavers (years)": "Avg Tenure of Leavers (Years)",
    "Avg Age": "Avg Age", "Avg Monthly Income": "Avg Monthly Income", "Total Trainings Last Year": "Total Trainings",
    "Training per Employee": "Training per Employee", "% Zero Training": "% No Training", "Overtime %": "Overtime %",
    "Attrition Rate - Overtime": "Attrition Rate - Overtime", "Attrition Rate - No Overtime": "Attrition Rate - No Overtime",
    "Avg Job Satisfaction (1-4)": "Avg Job Satisfaction", "% Low Job Satisfaction": "% Low Job Satisfaction",
    "Avg Years Since Last Promotion": "Avg Years Since Promotion", "Avg Performance Rating": "Avg Performance Rating",
}
