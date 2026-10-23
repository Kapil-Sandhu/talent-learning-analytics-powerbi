# Talent & Learning Analytics - Insights and Recommendations

**Audience:** HR, Talent and Learning & Development leads. **Data:** IBM HR Analytics sample (1,470 employees, fictional), point-in-time snapshot. **Dashboard:** `03_PowerBI/Talent_Learning_Dashboard.pbip`.

> These are **associations in a snapshot, not proven causes**. Each one is a strong lead to test (for example with a pilot and a control group) before rolling it out widely.

## Executive summary
- **16.1% of employees left** (237 of 1,470).
- **Overtime is the strongest driver.** Attrition is 30.5% with overtime vs 10.4% without (2.9x). The effect holds after controlling for job role, tenure, satisfaction, level and pay factors (odds ratio 5.0).
- **The first year is the riskiest time.** 34.9% of employees in their first 0-1 years left. With overtime on top, it is 55.1%.
- **Sales Representatives are the hotspot** at 39.8% attrition (+23.6 pts vs the company). They are mostly junior, low-paid and new.
- **Engagement matters.** Low job satisfaction (22.8%) and bad work-life balance (31.3%) both go with much higher attrition.
- **Learning data is too thin to steer on.** Only a training count is recorded, and new joiners get no more training than long-tenured staff.

## Key findings

| Group | Employees | Attrition | vs rest | Significance | Adjusted odds ratio* |
|---|---|---|---|---|---|
| Works overtime | 416 | 30.5% (95% CI 26.3-35.1%) | +20.1 pts | p < 0.001 | 5.0 (3.6-7.0) |
| 0-1 years at the company | 215 | 34.9% (95% CI 28.8-41.5%) | +22.0 pts | p < 0.001 | 2.9 (1.9-4.2) |
| Sales Representatives | 83 | 39.8% (95% CI 29.9-50.5%) | +25.1 pts | p < 0.001 | 2.7 (1.5-4.7) |
| Bad work-life balance | 80 | 31.3% (95% CI 22.2-42.1%) | +16.0 pts | p < 0.001 | 3.0 (1.6-5.3) |
| Low job satisfaction | 289 | 22.8% (95% CI 18.4-28.0%) | +8.4 pts | p < 0.001 | 2.2 (1.5-3.2) |
| Job level 1 | 543 | 26.3% (95% CI 22.8-30.2%) | +16.2 pts | p < 0.001 | 2.5 (1.8-3.5) |
| No stock options | 631 | 24.4% (95% CI 21.2-27.9%) | +14.5 pts | p < 0.001 | 2.5 (1.5-4.0) |
| Travels frequently | 277 | 24.9% (95% CI 20.2-30.3%) | +10.8 pts | p < 0.001 | 2.2 (1.5-3.3) |
| No training last year | 54 | 27.8% (95% CI 17.6-40.9%) | +12.1 pts | p = 0.018 | 2.6 (1.2-5.2) |

\* From a logistic regression with all listed factors together (AUC 0.82). An odds ratio above 1 means higher odds of leaving *after* the other factors are taken into account.

**Overtime, role by role.** Overtime goes with higher attrition in 8 of 9 job roles. The exception is Healthcare Representative, a small group (37 on overtime). Adjusted for job role, overtime means 4.3 times higher odds of leaving (95% CI 3.2-5.8). Highest attrition with overtime:
- Sales Representative: 66.7% with overtime vs 28.8% without
- Laboratory Technician: 50.0% with overtime vs 15.7% without
- Human Resources: 38.5% with overtime vs 17.9% without
- Research Scientist: 34.0% with overtime vs 7.2% without
- Sales Executive: 33.0% with overtime vs 11.2% without

**Sales Representative profile vs company.** Average monthly income is 2,626 vs 6,503. 91.6% are at job level 1 vs 36.9%, and 53.0% have no stock options vs 42.9%. Average tenure is 2.9 years vs 7.0. With overtime, 66.7% of Sales Representatives left (16 of 24).

**What did *not* drive attrition**
- **Performance rating:** Outstanding performers leave at 16.4% vs 16.1% (p = 0.912). The rating does not tell us who will stay, which suggests the scale needs calibrating.
- **Marital status:** Single employees leave more (25.5%), but the effect disappears once stock options and other factors are controlled for (odds ratio 1.25, p = 0.381). It is a stand-in for other factors, not a driver itself.
- **Training:** the no-training group leaves more (27.8%), but it is only 54 people, so the uncertainty is wide (95% CI 17.6-40.9%). Treat it as indicative.

## Recommendations

### 1. Reduce sustained overtime in the highest-risk roles
- **Why:** overtime is the strongest factor (2.9x attrition; odds ratio 5.0 after controls), and 28.3% of staff work overtime.
- **What:** monthly overtime reviews per team; workload rebalancing and backfill hiring. Start with Sales Representatives, Laboratory Technicians, Human Resources, Research Scientists and Sales Executives (highest attrition with overtime).
- **Track:** `Overtime %`, `Attrition Rate - Overtime`, `Overtime Attrition Ratio` (dashboard: Attrition Drivers page).
- **Illustrative size:** if overtime workers in each role left at the rate of their no-overtime colleagues, about 85 of the 237 leavers would not have left. This is an upper bound, not a forecast.

### 2. Make the first year stick: onboarding, mentoring and front-loaded learning
- **Why:** 34.9% attrition in the first 0-1 years, and 55.1% when combined with overtime. New joiners get about the same training as everyone else (2.93 trainings in year 0-1 vs 2.76 in years 2-5).
- **What:** a structured 90-day onboarding plan, a buddy or mentor for every new hire, a front-loaded learning path in the first 6 months, no routine overtime in the first year, and stay-interviews at 3 and 9 months.
- **Track:** `Early Tenure Attrition Rate (0-1 yrs)`, plus `Training per Employee` filtered to tenure 0-1 yrs (Training & Learning page).
- **Illustrative size:** bringing year 0-1 attrition down to the years 2-5 level (15.5%) would mean about 42 fewer leavers.

### 3. Targeted retention plan for Sales Representatives
- **Why:** 39.8% attrition (+23.6 pts vs company). The group is mostly level 1 (91.6%) and earns about 2,626 vs 6,503 on average.
- **What:** benchmark pay and incentives, a visible career path to Sales Executive, stock or bonus eligibility, and coaching from experienced Sales Executives.
- **Track:** `Attrition Rate` and `Attrition vs Company (pts)` for Sales Representative (Job Role Summary page; drill through for names).
- **Illustrative size:** halving their gap to the company rate means about 10 fewer leavers in a group of 83.

### 4. Act on engagement signals early
- **Why:** low job satisfaction means 22.8% attrition vs 14.5% for everyone else. Bad work-life balance means 31.3%. Low environment satisfaction has an odds ratio of 2.8 after controls.
- **What:** quarterly pulse surveys, with manager follow-up within 30 days for teams that score Low. Flexible-work options where work-life balance is rated Bad.
- **Track:** `% Low Job Satisfaction`, `Attrition Rate - Low Job Satisfaction`, `Avg Work-Life Balance` (Satisfaction & Performance page).

### 5. Improve the learning and people data
- **Why:** training is recorded only as a count (0-6), performance ratings barely vary (only 3 or 4) and do not relate to attrition, and the snapshot has no dates.
- **What:** record course type, hours and completion in the LMS. Calibrate performance ratings. Add hire, exit and course dates so the dashboard can show trends and measure whether actions 1-4 work.

## Method
- All figures were computed from the raw CSV with pandas, and reconciled with the Power BI model's DAX measures (see `validation_report_step7.txt`).
- 95% confidence intervals are Wilson intervals. Group-vs-rest tests are chi-square tests (Fisher's exact test for small cells).
- The multivariate check is a logistic regression with 11 factors (AUC 0.82, pseudo R-squared 0.24, max VIF 2.7 - no problematic collinearity). The overtime-by-role effect uses a Mantel-Haenszel odds ratio stratified by job role.
- The illustrative sizes are simple what-if arithmetic. They assume the gap would fully close, so treat them as upper bounds.

## Limitations
- This is a fictional sample dataset (IBM). Re-run the pipeline on real HR data before drawing real conclusions.
- A single snapshot: there are no trends and no before/after comparison. Leavers and stayers are observed at the same moment.
- These are associations, not causes. Several factors overlap: junior, young, low-paid and new tend to go together.
- Some groups are small (no training: 54, Sales Representatives: 83, Human Resources department: 63). Read their rates with the confidence intervals.
