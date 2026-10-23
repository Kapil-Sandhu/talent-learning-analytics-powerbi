"""
Step 7 - write the insights & recommendations document and the text for the dashboard's "Insights & Actions" page.
Every number is taken from 04_Docs/insights_facts.json (computed by analyze_step7.py from the raw CSV) through the
helpers below, which also log it in 04_Docs/analysis/number_manifest.json - so validate_step7.py can prove that
no number in the document was typed by hand.
Run from the project root:  python 04_Docs/analysis/build_insights.py
"""
import json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
F = json.load(open(os.path.join(ROOT, "04_Docs", "insights_facts.json")))
MANIFEST = []

def get(path):
    v = F
    for k in path.split("."):
        v = v[k]
    return v
from decimal import Decimal, ROUND_HALF_UP
def r(x, dp):
    """Round half away from zero, exactly like Power BI's display formatting (Python's default is half-to-even)."""
    q = Decimal(1).scaleb(-dp)
    return Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP) if x >= 0 else -Decimal(repr(-x)).quantize(q, rounding=ROUND_HALF_UP)
def put(text, path, value):
    MANIFEST.append({"text": text, "path": path, "value": value}); return text
def pct(path, dp=1):
    v = get(path); return put(f"{r(v * 100, dp)}%", path, v)
def pts(path, dp=1):
    v = get(path); return put(("+" if v >= 0 else "") + f"{r(v, dp)} pts", path, v)
def num(path, dp=0):
    v = get(path); return put(f"{r(v, dp):,}", path, v)
def ratio(path, dp=1):
    v = get(path); return put(f"{r(v, dp)}x", path, v)
def orr(path, dp=1):
    v = get(path); return put(f"{r(v, dp)}", path, v)
def pval(path):
    v = get(path); return put("p < 0.001" if v < 0.001 else f"p = {r(v, 3)}", path, v)
def ci(path, dp=1):
    lo, hi = get(path + ".ci_low"), get(path + ".ci_high")
    a, b = f"{r(lo * 100, dp)}", f"{r(hi * 100, dp)}"
    put(a, path + ".ci_low", lo); put(b, path + ".ci_high", hi)
    return f"95% CI {a}-{b}%"
def orci(path, dp=1):
    lo, hi = get(path + ".ci_low"), get(path + ".ci_high")
    a, b = f"{r(lo, dp)}", f"{r(hi, dp)}"
    put(a, path + ".ci_low", lo); put(b, path + ".ci_high", hi)
    return f"{a}-{b}"

D = "drivers"
T = "logit.terms"
roles_ot = sorted(F["overtime_by_role"].items(), key=lambda kv: -kv[1]["rate_ot"])
exception = [k for k, v in F["overtime_by_role"].items() if v["rate_ot"] <= v["rate_no_ot"]]
n_roles = len(F["overtime_by_role"])

md = []
A = md.append
A("# Talent & Learning Analytics - Insights and Recommendations")
A("")
A(f"**Audience:** HR, Talent and Learning & Development leads. **Data:** IBM HR Analytics sample "
  f"({num('company.headcount')} employees, fictional), point-in-time snapshot. **Dashboard:** `03_PowerBI/Talent_Learning_Dashboard.pbip`.")
A("")
A("> These are **associations in a snapshot, not proven causes**. Each one is a strong lead to test "
  "(for example with a pilot and a control group) before rolling it out widely.")
A("")
A("## Executive summary")
A(f"- **{pct('company.attrition_rate')} of employees left** ({num('company.leavers')} of {num('company.headcount')}).")
A(f"- **Overtime is the strongest driver.** Attrition is {pct('overtime_rates.ot')} with overtime vs {pct('overtime_rates.no_ot')} without "
  f"({ratio('overtime_rates.ratio')}). The effect holds after controlling for job role, tenure, satisfaction, level and pay factors "
  f"(odds ratio {orr(T + '.Overtime.odds_ratio')}).")
A(f"- **The first year is the riskiest time.** {pct(D + '.early_tenure.rate')} of employees in their first 0-1 years left. "
  f"With overtime on top, it is {pct('segment_ot_early.rate')}.")
A(f"- **Sales Representatives are the hotspot** at {pct(D + '.sales_rep.rate')} attrition ({pts(D + '.sales_rep.vs_company_pts')} vs the company). "
  "They are mostly junior, low-paid and new.")
A(f"- **Engagement matters.** Low job satisfaction ({pct(D + '.low_job_sat.rate')}) and bad work-life balance ({pct(D + '.bad_wlb.rate')}) "
  "both go with much higher attrition.")
A("- **Learning data is too thin to steer on.** Only a training count is recorded, and new joiners get no more training than long-tenured staff.")
A("")
A("## Key findings")
A("")
A("| Group | Employees | Attrition | vs rest | Significance | Adjusted odds ratio* |")
A("|---|---|---|---|---|---|")
rows = [("overtime", "Overtime"), ("early_tenure", "Tenure 0-1 yrs"), ("sales_rep", "Sales Representative"),
        ("bad_wlb", "Bad work-life balance"), ("low_job_sat", "Low job satisfaction"), ("job_level_1", "Job level 1"),
        ("no_stock", "No stock options"), ("travel_freq", "Travels frequently"), ("no_training", "No training last year")]
for key, term in rows:
    p = f"{D}.{key}"
    A(f"| {get(p + '.label')} | {num(p + '.n')} | {pct(p + '.rate')} ({ci(p)}) | {pts(p + '.diff_pts')} | {pval(p + '.p_value')} | "
      f"{orr(T + '.' + term + '.odds_ratio')} ({orci(T + '.' + term)}) |")
A("")
A(f"\\* From a logistic regression with all listed factors together (AUC {orr('logit.auc', 2)}). An odds ratio above 1 means higher odds "
  "of leaving *after* the other factors are taken into account.")
A("")
A("**Overtime, role by role.** Overtime goes with higher attrition in "
  f"{put(str(n_roles - len(exception)), 'overtime_holds_count', n_roles - len(exception))} of {put(str(n_roles), 'roles_count', n_roles)} job roles"
  + (f". The exception is {exception[0]}, a small group ({num('overtime_by_role.' + exception[0] + '.n_ot')} on overtime)." if exception else ".")
  + f" Adjusted for job role, overtime means {orr('overtime_mh_or_by_role.or')} times higher odds of leaving "
  f"(95% CI {orci('overtime_mh_or_by_role')}). Highest attrition with overtime:")
for k, v in roles_ot[:5]:
    A(f"- {k}: {pct('overtime_by_role.' + k + '.rate_ot')} with overtime vs {pct('overtime_by_role.' + k + '.rate_no_ot')} without")
A("")
A(f"**Sales Representative profile vs company.** Average monthly income is {num('sales_rep_profile.avg_income')} vs {num('sales_rep_profile.company_avg_income')}. "
  f"{pct('sales_rep_profile.share_job_level_1')} are at job level 1 vs {pct('sales_rep_profile.company_share_job_level_1')}, and "
  f"{pct('sales_rep_profile.share_no_stock')} have no stock options vs {pct('sales_rep_profile.company_share_no_stock')}. "
  f"Average tenure is {num('sales_rep_profile.avg_tenure', 1)} years vs {num('sales_rep_profile.company_avg_tenure', 1)}. "
  f"With overtime, {pct('segment_ot_salesrep.rate')} of Sales Representatives left "
  f"({num('segment_ot_salesrep.leavers')} of {num('segment_ot_salesrep.n')}).")
A("")
A("**What did *not* drive attrition**")
A(f"- **Performance rating:** Outstanding performers leave at {pct(D + '.outstanding_perf.rate')} vs {pct(D + '.outstanding_perf.rest_rate')} "
  f"({pval(D + '.outstanding_perf.p_value')}). The rating does not tell us who will stay, which suggests the scale needs calibrating.")
A(f"- **Marital status:** Single employees leave more ({pct(D + '.single.rate')}), but the effect disappears once stock options and "
  f"other factors are controlled for (odds ratio {orr(T + '.Single.odds_ratio', 2)}, {pval(T + '.Single.p_value')}). "
  "It is a stand-in for other factors, not a driver itself.")
A(f"- **Training:** the no-training group leaves more ({pct(D + '.no_training.rate')}), but it is only {num(D + '.no_training.n')} people, "
  f"so the uncertainty is wide ({ci(D + '.no_training')}). Treat it as indicative.")
A("")
A("## Recommendations")
A("")
A("### 1. Reduce sustained overtime in the highest-risk roles")
A(f"- **Why:** overtime is the strongest factor ({ratio('overtime_rates.ratio')} attrition; odds ratio {orr(T + '.Overtime.odds_ratio')} after controls), "
  f"and {pct('overtime_rates.share_ot')} of staff work overtime.")
A(f"- **What:** monthly overtime reviews per team; workload rebalancing and backfill hiring. Start with Sales Representatives, "
  f"Laboratory Technicians, Human Resources, Research Scientists and Sales Executives (highest attrition with overtime).")
A("- **Track:** `Overtime %`, `Attrition Rate - Overtime`, `Overtime Attrition Ratio` (dashboard: Attrition Drivers page).")
A(f"- **Illustrative size:** if overtime workers in each role left at the rate of their no-overtime colleagues, about "
  f"{num('what_if.overtime_role_adjusted')} of the {num('company.leavers')} leavers would not have left. This is an upper bound, not a forecast.")
A("")
A("### 2. Make the first year stick: onboarding, mentoring and front-loaded learning")
A(f"- **Why:** {pct(D + '.early_tenure.rate')} attrition in the first 0-1 years, and {pct('segment_ot_early.rate')} when combined with overtime. "
  f"New joiners get about the same training as everyone else ({num('training.by_tenure_band.0-1 yrs', 2)} trainings in year 0-1 vs "
  f"{num('training.by_tenure_band.2-5 yrs', 2)} in years 2-5).")
A("- **What:** a structured 90-day onboarding plan, a buddy or mentor for every new hire, a front-loaded learning path in the first "
  "6 months, no routine overtime in the first year, and stay-interviews at 3 and 9 months.")
A("- **Track:** `Early Tenure Attrition Rate (0-1 yrs)`, plus `Training per Employee` filtered to tenure 0-1 yrs (Training & Learning page).")
A(f"- **Illustrative size:** bringing year 0-1 attrition down to the years 2-5 level ({pct('what_if.rate_2_5_yrs')}) would mean about "
  f"{num('what_if.early_tenure')} fewer leavers.")
A("")
A("### 3. Targeted retention plan for Sales Representatives")
A(f"- **Why:** {pct(D + '.sales_rep.rate')} attrition ({pts(D + '.sales_rep.vs_company_pts')} vs company). The group is mostly level 1 "
  f"({pct('sales_rep_profile.share_job_level_1')}) and earns about {num('sales_rep_profile.avg_income')} vs {num('sales_rep_profile.company_avg_income')} on average.")
A("- **What:** benchmark pay and incentives, a visible career path to Sales Executive, stock or bonus eligibility, "
  "and coaching from experienced Sales Executives.")
A("- **Track:** `Attrition Rate` and `Attrition vs Company (pts)` for Sales Representative (Job Role Summary page; drill through for names).")
A(f"- **Illustrative size:** halving their gap to the company rate means about {num('what_if.sales_rep_halved_gap')} fewer leavers "
  f"in a group of {num(D + '.sales_rep.n')}.")
A("")
A("### 4. Act on engagement signals early")
A(f"- **Why:** low job satisfaction means {pct(D + '.low_job_sat.rate')} attrition vs {pct(D + '.low_job_sat.rest_rate')} for everyone else. "
  f"Bad work-life balance means {pct(D + '.bad_wlb.rate')}. Low environment satisfaction has an odds ratio of {orr(T + '.Low environment satisfaction.odds_ratio')} after controls.")
A("- **What:** quarterly pulse surveys, with manager follow-up within 30 days for teams that score Low. Flexible-work options where "
  "work-life balance is rated Bad.")
A("- **Track:** `% Low Job Satisfaction`, `Attrition Rate - Low Job Satisfaction`, `Avg Work-Life Balance` (Satisfaction & Performance page).")
A("")
A("### 5. Improve the learning and people data")
A("- **Why:** training is recorded only as a count (0-6), performance ratings barely vary (only 3 or 4) and do not relate to attrition, "
  "and the snapshot has no dates.")
A("- **What:** record course type, hours and completion in the LMS. Calibrate performance ratings. Add hire, exit and course dates so the "
  "dashboard can show trends and measure whether actions 1-4 work.")
A("")
A("## Method")
A("- All figures were computed from the raw CSV with pandas, and reconciled with the Power BI model's DAX measures (see `validation_report_step7.txt`).")
A("- 95% confidence intervals are Wilson intervals. Group-vs-rest tests are chi-square tests (Fisher's exact test for small cells).")
A(f"- The multivariate check is a logistic regression with {put(str(len(F['logit']['terms'])), 'logit_terms', len(F['logit']['terms']))} factors "
  f"(AUC {orr('logit.auc', 2)}, pseudo R-squared {orr('logit.pseudo_r2', 2)}, max VIF {orr('logit.max_vif', 1)} - no problematic collinearity). "
  "The overtime-by-role effect uses a Mantel-Haenszel odds ratio stratified by job role.")
A("- The illustrative sizes are simple what-if arithmetic. They assume the gap would fully close, so treat them as upper bounds.")
A("")
A("## Limitations")
A("- This is a fictional sample dataset (IBM). Re-run the pipeline on real HR data before drawing real conclusions.")
A("- A single snapshot: there are no trends and no before/after comparison. Leavers and stayers are observed at the same moment.")
A("- These are associations, not causes. Several factors overlap: junior, young, low-paid and new tend to go together.")
A(f"- Some groups are small (no training: {num(D + '.no_training.n')}, Sales Representatives: {num(D + '.sales_rep.n')}, "
  f"Human Resources department: {num('overtime_by_department.Human Resources.n')}). Read their rates with the confidence intervals.")

doc = "\n".join(md) + "\n"
open(os.path.join(ROOT, "04_Docs", "Insights_and_Recommendations.md"), "w", encoding="utf-8").write(doc)

# ------------------------------------------------------------------ text for the "Insights & Actions" dashboard page
PAGE = {"cards": ["Overtime Attrition Ratio", "Early Tenure Attrition Rate (0-1 yrs)", "Attrition Rate - Low Job Satisfaction", "Company Attrition Rate"],
        "panels": [
            {"title": "1. Reduce sustained overtime",
             "lines": [f"Attrition {pct('overtime_rates.ot')} with overtime vs {pct('overtime_rates.no_ot')} without; holds after controlling for role, tenure and pay.",
                       "Action: monthly overtime reviews, rebalance workload. Start with Sales Reps, Lab Technicians, HR, Research Scientists."]},
            {"title": "2. Make the first year stick",
             "lines": [f"{pct(D + '.early_tenure.rate')} of 0-1 year employees left ({pct('segment_ot_early.rate')} with overtime). New joiners get no extra training.",
                       "Action: 90-day onboarding, mentor per new hire, front-loaded learning path, no routine overtime in year 1."]},
            {"title": "3. Retention plan for Sales Representatives",
             "lines": [f"{pct(D + '.sales_rep.rate')} attrition ({pts(D + '.sales_rep.vs_company_pts')}); {pct('sales_rep_profile.share_job_level_1')} are level 1, "
                       f"avg income {num('sales_rep_profile.avg_income')} vs {num('sales_rep_profile.company_avg_income')}.",
                       "Action: pay and incentive benchmark, career path to Sales Executive, coaching."]},
            {"title": "4. Act on engagement signals",
             "lines": [f"Low job satisfaction: {pct(D + '.low_job_sat.rate')} attrition; bad work-life balance: {pct(D + '.bad_wlb.rate')}.",
                       "Action: quarterly pulse survey, manager follow-up within 30 days, flexible work options."]}],
        "footnote": "Associations in a fictional snapshot (IBM sample), not proven causes - test actions with a pilot first. "
                    "Also improve learning data: course type, hours, completion, dates. Full analysis: 04_Docs/Insights_and_Recommendations.md"}
json.dump(PAGE, open(os.path.join(ROOT, "04_Docs", "insights_page.json"), "w", encoding="utf-8"), indent=2)
os.makedirs(os.path.join(ROOT, "04_Docs", "analysis"), exist_ok=True)
json.dump(MANIFEST, open(os.path.join(ROOT, "04_Docs", "analysis", "number_manifest.json"), "w"), indent=1)
print(f"document: {len(doc.splitlines())} lines, {len(MANIFEST)} numbers logged")
