"""
Step 7 validation - insights & recommendations.
  A. Reproducibility : key statistics re-computed with an INDEPENDENT implementation (hand-written Wilson CI, 2x2 chi-square,
                       Mantel-Haenszel; logistic regression re-fitted with scikit-learn) == insights_facts.json
  B. Power BI recon  : every key rate / count / profile number == the live Power BI model (DAX), incl. the exact text
                       Power BI displays (FORMAT) == the text in the document
  C. Number audit    : every number in the document comes from the facts file (no hand-typed numbers), every logged
                       number appears in the document, every logged value == facts value
  D. Content         : 5 recommendations with Why / What / Track; every measure named exists in the model; every
                       dashboard page named exists; causal disclaimer + limitations present; no claims beyond the data
  E. Dashboard page  : "Insights & Actions" panel numbers are all logged numbers; (rendering etc. via validate_step6)
Usage:
  python validate_step7.py <root> --make-queries <queries.json>
  python validate_step7.py <root> <model_offline.json> <dax_results.json> <report.txt>
"""
import json, math, os, re, sys
import numpy as np
import pandas as pd

ROOT = sys.argv[1]
DOCS = os.path.join(ROOT, "04_Docs")
F = json.load(open(os.path.join(DOCS, "insights_facts.json"), encoding="utf-8"))
SR = "'DimJobRole'[JobRole] = \"Sales Representative\""
SEG = {  # facts path prefix -> DAX filter(s)
    "drivers.overtime": "'FactEmployee'[OverTimeFlag] = 1",
    "drivers.early_tenure": "'FactEmployee'[YearsAtCompany] <= 1",
    "drivers.sales_rep": SR,
    "drivers.low_job_sat": "'FactEmployee'[JobSatisfactionScore] = 1",
    "drivers.bad_wlb": "'DimEmployee'[WorkLifeBalance] = \"Bad\"",
    "drivers.single": "'DimEmployee'[MaritalStatus] = \"Single\"",
    "drivers.age_18_25": "'DimAgeBand'[AgeBand] = \"18-25\"",
    "drivers.job_level_1": "'DimEmployee'[JobLevel] = 1",
    "drivers.no_stock": "'DimEmployee'[StockOptionLevel] = 0",
    "drivers.travel_freq": "'DimEmployee'[BusinessTravel] = \"Travels Frequently\"",
    "drivers.income_lt3k": "'DimIncomeBand'[IncomeBand] = \"Under 3,000\"",
    "drivers.no_training": "'FactEmployee'[TrainingTimesLastYear] = 0",
    "drivers.high_training": "'FactEmployee'[TrainingTimesLastYear] >= 5",
    "drivers.outstanding_perf": "'DimEmployee'[PerformanceRating] = \"Outstanding\"",
    "segment_ot_early": "'FactEmployee'[OverTimeFlag] = 1, 'FactEmployee'[YearsAtCompany] <= 1",
    "segment_ot_salesrep": "'FactEmployee'[OverTimeFlag] = 1, " + SR,
}

def make_queries(path):
    cols = []
    for i, (k, flt) in enumerate(SEG.items()):
        cols += [f'"r{i}", CALCULATE([Attrition Rate], {flt})', f'"f{i}", FORMAT(CALCULATE([Attrition Rate], {flt}), "0.0%")',
                 f'"n{i}", CALCULATE([Headcount], {flt})', f'"l{i}", CALCULATE([Leavers], {flt})']
    q = {"segments": "EVALUATE ROW(" + ", ".join(cols) + ")",
         "company": 'EVALUATE ROW("rate", [Attrition Rate], "hc", [Headcount], "leavers", [Leavers], "ot", [Attrition Rate - Overtime], '
                    '"noot", [Attrition Rate - No Overtime], "ratio", [Overtime Attrition Ratio], "ratio_f", FORMAT([Overtime Attrition Ratio], "0.0"), '
                    '"share_ot", [Overtime %], "share_ot_f", FORMAT([Overtime %], "0.0%"), "early_m", [Early Tenure Attrition Rate (0-1 yrs)], '
                    '"lowjs_m", [Attrition Rate - Low Job Satisfaction], "notrain_m", [Attrition Rate - No Training], '
                    '"rate_2_5", CALCULATE([Attrition Rate], \'DimTenureBand\'[TenureBand] = "2-5 yrs"), '
                    '"rate_f", FORMAT([Attrition Rate], "0.0%"), "tpe", [Training per Employee], '
                    '"sr_vs", CALCULATE([Attrition vs Company (pts)], ' + SR + '), '
                    '"sr_income", CALCULATE([Avg Monthly Income], ' + SR + '), "income", [Avg Monthly Income], '
                    '"sr_tenure", CALCULATE([Avg Tenure (Years)], ' + SR + '), "tenure", [Avg Tenure (Years)], '
                    '"sr_lvl1", DIVIDE(CALCULATE([Headcount], ' + SR + ', \'DimEmployee\'[JobLevel] = 1), CALCULATE([Headcount], ' + SR + ')), '
                    '"lvl1", DIVIDE(CALCULATE([Headcount], \'DimEmployee\'[JobLevel] = 1), [Headcount]), '
                    '"sr_nostock", DIVIDE(CALCULATE([Headcount], ' + SR + ', \'DimEmployee\'[StockOptionLevel] = 0), CALCULATE([Headcount], ' + SR + ')), '
                    '"nostock", DIVIDE(CALCULATE([Headcount], \'DimEmployee\'[StockOptionLevel] = 0), [Headcount]), '
                    '"sr_ot", CALCULATE([Overtime %], ' + SR + '))',
         "ot_by_role": 'EVALUATE SUMMARIZECOLUMNS(\'DimJobRole\'[JobRole], "ot", [Attrition Rate - Overtime], "noot", [Attrition Rate - No Overtime], '
                       '"n_ot", [Overtime Employees], "hc", [Headcount], "ot_f", FORMAT([Attrition Rate - Overtime], "0.0%"), '
                       '"noot_f", FORMAT([Attrition Rate - No Overtime], "0.0%"))',
         "ot_by_dept": 'EVALUATE SUMMARIZECOLUMNS(\'DimDepartment\'[Department], "ot", [Attrition Rate - Overtime], "noot", [Attrition Rate - No Overtime], "hc", [Headcount])',
         "training_by_tenure": 'EVALUATE SUMMARIZECOLUMNS(\'DimTenureBand\'[TenureBand], "tpe", [Training per Employee], "tpe_f", FORMAT([Training per Employee], "0.00"))'}
    json.dump(q, open(path, "w"), indent=1)
    print(f"{len(q)} queries written to {path}")

if len(sys.argv) > 2 and sys.argv[2] == "--make-queries":
    make_queries(sys.argv[3]); sys.exit(0)

MODEL, DAX, REPORT = sys.argv[2:5]
res, out = [], []
def check(sec, name, ok, detail=""):
    res.append(bool(ok)); out.append(f"[{'PASS' if ok else 'FAIL'}] {sec}: {name}" + (f" - {detail}" if detail else ""))
def close(a, b, tol=1e-9):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol * max(1, abs(float(b)))

raw = pd.read_csv(os.path.join(ROOT, "01_Data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv"), encoding="utf-8-sig")
d = raw.assign(left=(raw.Attrition == "Yes").astype(int), ot=(raw.OverTime == "Yes").astype(int))
MASK = {"drivers.overtime": d.ot == 1, "drivers.early_tenure": d.YearsAtCompany <= 1, "drivers.sales_rep": d.JobRole == "Sales Representative",
        "drivers.low_job_sat": d.JobSatisfaction == 1, "drivers.bad_wlb": d.WorkLifeBalance == 1, "drivers.single": d.MaritalStatus == "Single",
        "drivers.age_18_25": d.Age <= 25, "drivers.job_level_1": d.JobLevel == 1, "drivers.no_stock": d.StockOptionLevel == 0,
        "drivers.travel_freq": d.BusinessTravel == "Travel_Frequently", "drivers.income_lt3k": d.MonthlyIncome < 3000,
        "drivers.no_training": d.TrainingTimesLastYear == 0, "drivers.high_training": d.TrainingTimesLastYear >= 5,
        "drivers.outstanding_perf": d.PerformanceRating == 4}
def get(path):
    v = F
    for k in path.split("."): v = v[k]
    return v

# ------------------------------------------------------------------ A. independent re-implementation
S = "A. Reproducibility"
def wilson(k, n, z=1.959963984540054):
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h
def chi2_2x2(a, b, c, dd):
    n = a + b + c + dd
    return n * (a * dd - b * c) ** 2 / ((a + b) * (c + dd) * (a + c) * (b + dd))
bad = []
for key, m in MASK.items():
    g, rest = d[m], d[~m]
    k, n, kr, nr = int(g.left.sum()), len(g), int(rest.left.sum()), len(rest)
    f = get(key)
    lo, hi = wilson(k, n)
    exp = {"n": n, "leavers": k, "rate": k / n, "rest_rate": kr / nr, "diff_pts": (k / n - kr / nr) * 100, "ci_low": lo, "ci_high": hi,
           "vs_company_pts": (k / n - d.left.mean()) * 100}
    for fld, e in exp.items():
        if not close(f[fld], e, 1e-7): bad.append(f"{key}.{fld}: facts {f[fld]} vs {e}")
    # chi-square p from hand-computed statistic (1 df); Fisher used by analysis only for small expected counts
    x2 = chi2_2x2(k, n - k, kr, nr - kr)
    p_hand = math.erfc(math.sqrt(x2 / 2))
    exp_min = min(n * (k + kr) / (n + nr), n * (n + nr - k - kr) / (n + nr), nr * (k + kr) / (n + nr), nr * (n + nr - k - kr) / (n + nr))
    if exp_min >= 5 and not close(f["p_value"], p_hand, 1e-6) and not (f["p_value"] < 1e-12 and p_hand < 1e-12):
        bad.append(f"{key}.p_value: facts {f['p_value']} vs hand {p_hand}")
check(S, f"{len(MASK)} driver groups: n, leavers, rate, CI, differences, p-values == independent hand-written formulas", not bad, "; ".join(bad[:4]))
num = den = 0.0
for _, g in d.groupby("JobRole"):
    a = ((g.ot == 1) & (g.left == 1)).sum(); b = ((g.ot == 1) & (g.left == 0)).sum()
    c = ((g.ot == 0) & (g.left == 1)).sum(); dd = ((g.ot == 0) & (g.left == 0)).sum(); t = len(g)
    num += a * dd / t; den += b * c / t
check(S, "Mantel-Haenszel overtime odds ratio (by job role) == hand formula", close(F["overtime_mh_or_by_role"]["or"], num / den, 1e-9),
      f"{F['overtime_mh_or_by_role']['or']} vs {num / den}")
from sklearn.linear_model import LogisticRegression
X = pd.DataFrame({"Overtime": d.ot, "Tenure 0-1 yrs": (d.YearsAtCompany <= 1).astype(int), "Low job satisfaction": (d.JobSatisfaction == 1).astype(int),
                  "Bad work-life balance": (d.WorkLifeBalance == 1).astype(int), "Low environment satisfaction": (d.EnvironmentSatisfaction == 1).astype(int),
                  "Sales Representative": (d.JobRole == "Sales Representative").astype(int), "Job level 1": (d.JobLevel == 1).astype(int),
                  "No stock options": (d.StockOptionLevel == 0).astype(int), "Single": (d.MaritalStatus == "Single").astype(int),
                  "Travels frequently": (d.BusinessTravel == "Travel_Frequently").astype(int), "No training last year": (d.TrainingTimesLastYear == 0).astype(int)})
lr = LogisticRegression(penalty=None, max_iter=5000, tol=1e-10).fit(X, d.left)
ors = dict(zip(X.columns, np.exp(lr.coef_[0])))
dev = {t: (F["logit"]["terms"][t]["odds_ratio"], ors[t]) for t in X.columns if abs(F["logit"]["terms"][t]["odds_ratio"] / ors[t] - 1) > 1e-3}
check(S, "Logistic-regression odds ratios re-fitted independently (scikit-learn) == statsmodels results", not dev, str(dev))
tb = d.groupby(pd.cut(d.YearsAtCompany, [-1, 1, 5, 10, 99], labels=["0-1 yrs", "2-5 yrs", "6-10 yrs", "11+ yrs"]), observed=True).TrainingTimesLastYear.mean()
check(S, "Training per employee by tenure band == independent recompute", all(close(F["training"]["by_tenure_band"][k], v) for k, v in tb.items()))
sr = d[d.JobRole == "Sales Representative"]
check(S, "Sales Representative profile == independent recompute",
      close(F["sales_rep_profile"]["avg_income"], sr.MonthlyIncome.mean()) and close(F["sales_rep_profile"]["share_job_level_1"], (sr.JobLevel == 1).mean())
      and close(F["sales_rep_profile"]["share_no_stock"], (sr.StockOptionLevel == 0).mean()) and close(F["sales_rep_profile"]["avg_tenure"], sr.YearsAtCompany.mean()))
wi = F["what_if"]
role_adj = sum(((g.ot == 1).sum()) * (g[g.ot == 1].left.mean() - g[g.ot == 0].left.mean()) for _, g in d.groupby("JobRole"))
check(S, "What-if sizes == independent arithmetic", close(wi["overtime_role_adjusted"], role_adj) and
      close(wi["early_tenure"], (d.YearsAtCompany <= 1).sum() * (d[d.YearsAtCompany <= 1].left.mean() - d[(d.YearsAtCompany >= 2) & (d.YearsAtCompany <= 5)].left.mean())))

# ------------------------------------------------------------------ B. Power BI reconciliation
S = "B. Power BI"
R = json.load(open(DAX, encoding="utf-8-sig"))
check(S, "All reconciliation DAX queries ran in Power BI", not R["errors"], str(R["errors"])[:300])
def rows(k):
    q = R["queries"][k]; cols = [c[1:-1] if c.startswith("[") and c.endswith("]") else c for c in q["columns"]]
    return [dict(zip(cols, r)) for r in q["rows"]]
seg = rows("segments")[0]
manifest = json.load(open(os.path.join(DOCS, "analysis", "number_manifest.json")))
text_by_path = {}
for m in manifest: text_by_path.setdefault(m["path"], set()).add(m["text"])
bad, fmt_bad = [], []
for i, key in enumerate(SEG):
    f = get(key)
    if not (close(seg[f"r{i}"], f["rate"]) and seg[f"n{i}"] == f["n"] and seg[f"l{i}"] == f["leavers"]):
        bad.append(f"{key}: PBI rate {seg[f'r{i}']} n {seg[f'n{i}']} vs facts {f['rate']} {f['n']}")
    shown = seg[f"f{i}"]
    if key + ".rate" in text_by_path and shown not in text_by_path[key + ".rate"]:
        fmt_bad.append(f"{key}: Power BI shows {shown}, document says {text_by_path[key + '.rate']}")
check(S, f"{len(SEG)} segment rates, headcounts and leavers == Power BI model", not bad, "; ".join(bad[:4]))
check(S, "Every segment rate in the document is written exactly as Power BI displays it (same rounding)", not fmt_bad, "; ".join(fmt_bad[:4]))
c = rows("company")[0]
pairs = {"company.attrition_rate": c["rate"], "company.headcount": c["hc"], "company.leavers": c["leavers"],
         "overtime_rates.ot": c["ot"], "overtime_rates.no_ot": c["noot"], "overtime_rates.ratio": c["ratio"], "overtime_rates.share_ot": c["share_ot"],
         "drivers.early_tenure.rate": c["early_m"], "drivers.low_job_sat.rate": c["lowjs_m"], "drivers.no_training.rate": c["notrain_m"],
         "what_if.rate_2_5_yrs": c["rate_2_5"], "training.per_employee": c["tpe"], "drivers.sales_rep.vs_company_pts": c["sr_vs"] * 100,
         "sales_rep_profile.avg_income": c["sr_income"], "sales_rep_profile.company_avg_income": c["income"],
         "sales_rep_profile.avg_tenure": c["sr_tenure"], "sales_rep_profile.company_avg_tenure": c["tenure"],
         "sales_rep_profile.share_job_level_1": c["sr_lvl1"], "sales_rep_profile.company_share_job_level_1": c["lvl1"],
         "sales_rep_profile.share_no_stock": c["sr_nostock"], "sales_rep_profile.company_share_no_stock": c["nostock"],
         "sales_rep_profile.overtime_share": c["sr_ot"]}
bad = [f"{p}: facts {get(p)} vs Power BI {v}" for p, v in pairs.items() if not close(get(p), v, 1e-7)]
check(S, f"{len(pairs)} headline numbers (company, overtime, measures, Sales Rep profile) == Power BI measures", not bad, "; ".join(bad[:4]))
check(S, "Document's overtime ratio and share match Power BI's displayed text",
      c["ratio_f"] + "x" in text_by_path.get("overtime_rates.ratio", set()) and c["share_ot_f"] in text_by_path.get("overtime_rates.share_ot", set()),
      f"{c['ratio_f']}x / {c['share_ot_f']} vs {text_by_path.get('overtime_rates.ratio')} / {text_by_path.get('overtime_rates.share_ot')}")
bad = []
for r in rows("ot_by_role"):
    f = F["overtime_by_role"][r["DimJobRole[JobRole]"]]
    if not (close(r["ot"], f["rate_ot"]) and close(r["noot"], f["rate_no_ot"]) and r["n_ot"] == f["n_ot"] and r["hc"] == f["n"]): bad.append(r["DimJobRole[JobRole]"])
    for fld, pth in (("ot_f", "rate_ot"), ("noot_f", "rate_no_ot")):
        p = f"overtime_by_role.{r['DimJobRole[JobRole]']}.{pth}"
        if p in text_by_path and r[fld] not in text_by_path[p]: bad.append(f"{p}: shows {r[fld]} vs doc {text_by_path[p]}")
check(S, "Overtime attrition in all 9 job roles == Power BI (values and displayed text)", not bad and len(rows("ot_by_role")) == 9, str(bad[:4]))
bad = [r["DimDepartment[Department]"] for r in rows("ot_by_dept") if not (close(r["ot"], F["overtime_by_department"][r["DimDepartment[Department]"]]["rate_ot"])
       and close(r["noot"], F["overtime_by_department"][r["DimDepartment[Department]"]]["rate_no_ot"]))]
check(S, "Overtime attrition in all 3 departments == Power BI", not bad, str(bad))
bad = [r for r in rows("training_by_tenure") if not close(r["tpe"], F["training"]["by_tenure_band"][r["DimTenureBand[TenureBand]"]])]
check(S, "Training per employee by tenure band == Power BI", not bad, str(bad))

# ------------------------------------------------------------------ C. number audit
S = "C. Number audit"
doc = open(os.path.join(DOCS, "Insights_and_Recommendations.md"), encoding="utf-8").read()
ALLOWED = {"0-1", "2-5", "1-4", "0-6", "90-day", "6", "3", "9", "30", "4", "95%", "1", "5", "18-25", "1-6", "2", "8"}  # policy / scale literals
logged = [m["text"] for m in manifest]
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"   # 2,626 / 6502.9 / 0.03 (a trailing comma is punctuation, not part of the number)
NB = r"(?<![A-Za-z_\d.,])"                                    # token must not continue a word or another number
TOKEN_RE = re.compile(rf"{NB}(?:(?:{NUM})-(?:{NUM})%?|[+-]?(?:{NUM})%?(?:x| pts|-day)?)(?![_\d])")  # (?!_): skip identifiers like 03_PowerBI  # ranges (21.2-27.9%, 0-1) first, then signed numbers
def tokenize(s): return TOKEN_RE.findall(s)
tokens = tokenize(doc.replace("`", " "))
CI_PAIRS = {}
for m in manifest:
    if m["path"].endswith((".ci_low", ".ci_high")): CI_PAIRS.setdefault(m["path"].rsplit(".", 1)[0], {})[m["path"].rsplit(".", 1)[1]] = m["text"]
CI_TEXTS = {f"{v['ci_low']}-{v['ci_high']}" for v in CI_PAIRS.values() if len(v) == 2}
def explained(tok):
    t = tok.strip()
    if t in ALLOWED: return True
    if re.fullmatch(rf"(?:{NUM})-(?:{NUM})%?", t):            # a range is explained only as the low-high of ONE logged CI
        return t.rstrip("%") in CI_TEXTS
    return any(t == L or t in L.split() or t.lstrip("+") == L.lstrip("+").replace(" pts", "") or t == L.replace(" pts", "") for L in logged)
unexplained = sorted({t for t in tokens if not explained(t)})
check(S, f"Every one of the {len(tokens)} numbers in the document comes from the facts file or is a policy/scale literal", not unexplained, str(unexplained[:15]))
missing = [m["text"] for m in manifest if m["text"] not in doc and m["text"] not in json.dumps(json.load(open(os.path.join(DOCS, "insights_page.json"))))]
check(S, f"All {len(manifest)} logged numbers actually appear in the document / dashboard page", not missing, str(missing[:6]))
wrong = [m for m in manifest if isinstance(m["value"], (int, float)) and not isinstance(m["value"], bool)
         and m["path"] not in ("overtime_holds_count", "roles_count", "logit_terms") and not close(get(m["path"]), m["value"], 1e-12)]
check(S, "Every logged value == the value in insights_facts.json", not wrong, str(wrong[:3]))
check(S, "Counts in text: overtime holds in 8 of 9 roles == facts",
      sum(v["rate_ot"] > v["rate_no_ot"] for v in F["overtime_by_role"].values()) == next(m["value"] for m in manifest if m["path"] == "overtime_holds_count"))

# ------------------------------------------------------------------ D. content
S = "D. Content"
recs = re.findall(r"^### (\d)\. (.+)$", doc, re.M)
check(S, "5 numbered recommendations", [r[0] for r in recs] == list("12345"), str(recs))
blocks = re.split(r"^### \d\. ", doc, flags=re.M)[1:]
lacking = [i + 1 for i, b in enumerate(blocks) if not ("**Why:**" in b and "**What:**" in b and ("**Track:**" in b or i == 4))]
check(S, "Each recommendation has Why / What / Track (data recommendation: Why / What)", not lacking, str(lacking))
model = json.load(open(MODEL, encoding="utf-8-sig"))
measures = {m["name"] for m in model["measures"]}
named = set(re.findall(r"`([^`]+)`", doc)) - {"03_PowerBI/Talent_Learning_Dashboard.pbip", "validation_report_step7.txt"}
not_found = sorted(n for n in named if n not in measures)
check(S, f"All {len(named)} measures named in the document exist in the Power BI model", not not_found, str(not_found))
spec = json.load(open(os.path.join(ROOT, "03_PowerBI", "report", "report_spec.json"), encoding="utf-8"))
page_names = {p["name"] for p in spec["pages"]}
mentioned = set(re.findall(r"\(([A-Z][A-Za-z &]+) page", doc)) | set(re.findall(r"dashboard: ([A-Z][A-Za-z &]+) page", doc))
check(S, f"Every dashboard page referenced exists ({sorted(mentioned)})", mentioned and mentioned <= page_names, str(mentioned - page_names))
check(S, "Causal disclaimer + limitations + method section present",
      "not proven causes" in doc and "## Limitations" in doc and "## Method" in doc and "fictional" in doc)
check(S, "Illustrative sizes are labelled as upper bounds / not forecasts", "upper bound" in doc and "not a forecast" in doc)
check(S, "No time-based claims the snapshot cannot support (per year / per month / trend)",
      not re.search(r"per (year|month|quarter)|year[- ]over[- ]year|trend(ed|ing)? (up|down)", doc.split("## Limitations")[0].split("## Method")[0], re.I))

# ------------------------------------------------------------------ E. dashboard page text
S = "E. Insights page"
page = json.load(open(os.path.join(DOCS, "insights_page.json"), encoding="utf-8"))
ptoks = tokenize(" ".join(page["cards"] + [page.get("footnote", "")] + [x for pnl in page["panels"] for x in [pnl.get("title", "")] + pnl.get("lines", [])]))
un = sorted({t for t in ptoks if not explained(t) and t not in {"04", "1", "2", "3"}})
check(S, "Every number on the Insights & Actions page comes from the facts file", not un, str(un))
check(S, "Page has 4 panels and 4 live measure cards that exist in the model",
      len(page["panels"]) == 4 and len(page["cards"]) == 4 and set(page["cards"]) <= measures)
ins = [p for p in spec["pages"] if p["name"] == "Insights & Actions"]
check(S, "Page is in the report as page 2 with its 4 panels + 4 cards", ins and spec["pages"][1]["name"] == "Insights & Actions"
      and sum(v["type"] == "card" for v in ins[0]["visuals"]) == 4 and sum(1 for v in ins[0]["visuals"] if v.get("title")) == 4)

passed, total = sum(res), len(res)
text = f"STEP 7 VALIDATION: {passed}/{total} checks passed\n\n" + "\n".join(out)
print(text)
open(REPORT, "w", encoding="utf-8").write(text + "\n")
sys.exit(0 if passed == total else 1)
