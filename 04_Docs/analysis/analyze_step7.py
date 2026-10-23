"""
Step 7 - insight analysis. Computes every number used in the insights document and the report page,
straight from the RAW CSV (independent of Power BI), and writes 04_Docs/insights_facts.json.

For each driver: group size, leavers, attrition rate, 95% Wilson confidence interval, difference vs the
rest in percentage points, rate ratio, chi-square / Fisher test. Plus: overtime effect inside each job role
and department (does it hold everywhere?), a multivariate logistic regression (does each driver still
matter when the others are controlled for?), and illustrative "what if" sizing for each recommendation.
Run from the project root:  python 04_Docs/analysis/analyze_step7.py
"""
import json, math, os, sys
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
raw = pd.read_csv(os.path.join(ROOT, "01_Data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv"), encoding="utf-8-sig")
d = raw.copy()
d["left"] = (d.Attrition == "Yes").astype(int)
d["ot"] = (d.OverTime == "Yes").astype(int)
N, L = len(d), int(d.left.sum())
COMPANY = L / N

def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

def group(mask, label):
    g, rest = d[mask], d[~mask]
    k, n = int(g.left.sum()), len(g)
    kr, nr = int(rest.left.sum()), len(rest)
    table = [[k, n - k], [kr, nr - kr]]
    chi2, p, _, exp = stats.chi2_contingency(table, correction=False)
    if (np.array(exp) < 5).any():
        _, p = stats.fisher_exact(table)
    lo, hi = wilson(k, n)
    return {"label": label, "n": n, "leavers": k, "rate": k / n, "ci_low": lo, "ci_high": hi,
            "rest_n": nr, "rest_rate": kr / nr, "diff_pts": (k / n - kr / nr) * 100,
            "vs_company_pts": (k / n - COMPANY) * 100, "rate_ratio": (k / n) / (kr / nr) if kr else None,
            "p_value": float(p), "share_of_staff": n / N, "share_of_leavers": k / L}

F = {"company": {"headcount": N, "leavers": L, "attrition_rate": COMPANY}}
F["drivers"] = {
    "overtime": group(d.ot == 1, "Works overtime"),
    "early_tenure": group(d.YearsAtCompany <= 1, "0-1 years at the company"),
    "sales_rep": group(d.JobRole == "Sales Representative", "Sales Representatives"),
    "low_job_sat": group(d.JobSatisfaction == 1, "Low job satisfaction"),
    "bad_wlb": group(d.WorkLifeBalance == 1, "Bad work-life balance"),
    "single": group(d.MaritalStatus == "Single", "Single"),
    "age_18_25": group(d.Age <= 25, "Aged 18-25"),
    "job_level_1": group(d.JobLevel == 1, "Job level 1"),
    "no_stock": group(d.StockOptionLevel == 0, "No stock options"),
    "travel_freq": group(d.BusinessTravel == "Travel_Frequently", "Travels frequently"),
    "income_lt3k": group(d.MonthlyIncome < 3000, "Monthly income under 3,000"),
    "no_training": group(d.TrainingTimesLastYear == 0, "No training last year"),
    "high_training": group(d.TrainingTimesLastYear >= 5, "5-6 trainings last year"),
    "outstanding_perf": group(d.PerformanceRating == 4, "Outstanding performance rating"),
}
F["overtime_rates"] = {"ot": F["drivers"]["overtime"]["rate"], "no_ot": F["drivers"]["overtime"]["rest_rate"],
                       "ratio": F["drivers"]["overtime"]["rate_ratio"], "share_ot": d.ot.mean()}

# ---------------------------------------------------------------- overtime inside each role / department
def ot_within(col):
    out = {}
    for v, g in d.groupby(col):
        a, b = g[g.ot == 1], g[g.ot == 0]
        out[v] = {"n": len(g), "ot_share": g.ot.mean(), "rate_ot": a.left.mean() if len(a) else None,
                  "rate_no_ot": b.left.mean() if len(b) else None, "n_ot": len(a), "n_no_ot": len(b)}
    return out
F["overtime_by_role"] = ot_within("JobRole")
F["overtime_by_department"] = ot_within("Department")
F["overtime_holds_in_all_roles"] = all(v["rate_ot"] > v["rate_no_ot"] for v in F["overtime_by_role"].values())
F["overtime_holds_in_all_departments"] = all(v["rate_ot"] > v["rate_no_ot"] for v in F["overtime_by_department"].values())
# Mantel-Haenszel common odds ratio for overtime, stratified by job role
strata = [np.array([[((g.ot == 1) & (g.left == 1)).sum(), ((g.ot == 1) & (g.left == 0)).sum()],
                    [((g.ot == 0) & (g.left == 1)).sum(), ((g.ot == 0) & (g.left == 0)).sum()]]) for _, g in d.groupby("JobRole")]
mh = sm.stats.StratifiedTable(strata)
F["overtime_mh_or_by_role"] = {"or": float(mh.oddsratio_pooled), "ci_low": float(mh.oddsratio_pooled_confint()[0]),
                               "ci_high": float(mh.oddsratio_pooled_confint()[1]), "p_value": float(mh.test_null_odds().pvalue)}

# ---------------------------------------------------------------- combined risk segment
seg = d[(d.ot == 1) & (d.YearsAtCompany <= 1)]
F["segment_ot_early"] = {"n": len(seg), "leavers": int(seg.left.sum()), "rate": seg.left.mean()}
seg2 = d[(d.ot == 1) & (d.JobRole == "Sales Representative")]
F["segment_ot_salesrep"] = {"n": len(seg2), "leavers": int(seg2.left.sum()), "rate": seg2.left.mean()}

# ---------------------------------------------------------------- multivariate logistic regression
X = pd.DataFrame({
    "Overtime": d.ot, "Tenure 0-1 yrs": (d.YearsAtCompany <= 1).astype(int),
    "Low job satisfaction": (d.JobSatisfaction == 1).astype(int), "Bad work-life balance": (d.WorkLifeBalance == 1).astype(int),
    "Low environment satisfaction": (d.EnvironmentSatisfaction == 1).astype(int),
    "Sales Representative": (d.JobRole == "Sales Representative").astype(int), "Job level 1": (d.JobLevel == 1).astype(int),
    "No stock options": (d.StockOptionLevel == 0).astype(int), "Single": (d.MaritalStatus == "Single").astype(int),
    "Travels frequently": (d.BusinessTravel == "Travel_Frequently").astype(int), "No training last year": (d.TrainingTimesLastYear == 0).astype(int),
})
model = sm.Logit(d.left, sm.add_constant(X)).fit(disp=0)
ci = model.conf_int()
F["logit"] = {"n": int(model.nobs), "pseudo_r2": float(model.prsquared), "auc": None, "terms": {}}
for t in X.columns:
    F["logit"]["terms"][t] = {"odds_ratio": float(np.exp(model.params[t])), "ci_low": float(np.exp(ci.loc[t, 0])),
                              "ci_high": float(np.exp(ci.loc[t, 1])), "p_value": float(model.pvalues[t])}
from sklearn.metrics import roc_auc_score
F["logit"]["auc"] = float(roc_auc_score(d.left, model.predict(sm.add_constant(X))))
F["logit"]["max_vif"] = None
from statsmodels.stats.outliers_influence import variance_inflation_factor
Xc = sm.add_constant(X).astype(float)
F["logit"]["max_vif"] = float(max(variance_inflation_factor(Xc.values, i) for i in range(1, Xc.shape[1])))

# ---------------------------------------------------------------- training / learning detail
F["training"] = {
    "per_employee": d.TrainingTimesLastYear.mean(),
    "by_tenure_band": {k: float(v) for k, v in d.groupby(pd.cut(d.YearsAtCompany, [-1, 1, 5, 10, 99],
                                                                  labels=["0-1 yrs", "2-5 yrs", "6-10 yrs", "11+ yrs"]),
                                                           observed=True).TrainingTimesLastYear.mean().items()},
    "spearman_training_vs_left": dict(zip(["rho", "p_value"], map(float, stats.spearmanr(d.TrainingTimesLastYear, d.left)))),
    "chi2_bands_p": float(stats.chi2_contingency(pd.crosstab(pd.cut(d.TrainingTimesLastYear, [-1, 0, 2, 4, 6]), d.left))[1]),
}

# ---------------------------------------------------------------- Sales Representative profile vs company
sr = d[d.JobRole == "Sales Representative"]
F["sales_rep_profile"] = {
    "n": len(sr), "avg_income": sr.MonthlyIncome.mean(), "company_avg_income": d.MonthlyIncome.mean(),
    "share_job_level_1": (sr.JobLevel == 1).mean(), "company_share_job_level_1": (d.JobLevel == 1).mean(),
    "share_no_stock": (sr.StockOptionLevel == 0).mean(), "company_share_no_stock": (d.StockOptionLevel == 0).mean(),
    "avg_age": sr.Age.mean(), "company_avg_age": d.Age.mean(),
    "avg_tenure": sr.YearsAtCompany.mean(), "company_avg_tenure": d.YearsAtCompany.mean(),
    "overtime_share": sr.ot.mean(),
}

# ---------------------------------------------------------------- illustrative "what if" sizing (NOT causal estimates)
o = F["overtime_by_role"]
F["what_if"] = {
    # crude: overtime workers at the no-overtime rate
    "overtime_crude": F["drivers"]["overtime"]["n"] * (F["overtime_rates"]["ot"] - F["overtime_rates"]["no_ot"]),
    # role-adjusted: same, but each role compared with its own no-overtime rate (more conservative)
    "overtime_role_adjusted": sum(v["n_ot"] * (v["rate_ot"] - v["rate_no_ot"]) for v in o.values()),
    # early tenure at the 2-5 years rate
    "early_tenure": F["drivers"]["early_tenure"]["n"] * (F["drivers"]["early_tenure"]["rate"]
                                                        - d[(d.YearsAtCompany >= 2) & (d.YearsAtCompany <= 5)].left.mean()),
    "rate_2_5_yrs": d[(d.YearsAtCompany >= 2) & (d.YearsAtCompany <= 5)].left.mean(),
    # low job satisfaction at the company-average rate
    "low_job_sat": F["drivers"]["low_job_sat"]["n"] * (F["drivers"]["low_job_sat"]["rate"] - COMPANY),
    "sales_rep_halved_gap": F["drivers"]["sales_rep"]["n"] * (F["drivers"]["sales_rep"]["rate"] - COMPANY) / 2,
}

def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(x) for x in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o
out = os.path.join(ROOT, "04_Docs", "insights_facts.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(clean(F), open(out, "w"), indent=2)
print(json.dumps(clean({k: F[k] for k in ["company", "overtime_rates", "overtime_mh_or_by_role", "segment_ot_early",
                                          "segment_ot_salesrep", "what_if", "training", "sales_rep_profile"]}), indent=1))
print("overtime holds in all roles:", F["overtime_holds_in_all_roles"], "| all departments:", F["overtime_holds_in_all_departments"])
for k, v in F["drivers"].items():
    print(f"{k:17s} n={v['n']:4d} rate={v['rate']:.3f} [{v['ci_low']:.3f},{v['ci_high']:.3f}] diff={v['diff_pts']:+.1f}pts p={v['p_value']:.2g}")
print("logit AUC", round(F['logit']['auc'], 3), "pseudoR2", round(F['logit']['pseudo_r2'], 3), "maxVIF", round(F['logit']['max_vif'], 2))
for t, v in F["logit"]["terms"].items():
    print(f"  {t:28s} OR={v['odds_ratio']:.2f} [{v['ci_low']:.2f},{v['ci_high']:.2f}] p={v['p_value']:.2g}")
