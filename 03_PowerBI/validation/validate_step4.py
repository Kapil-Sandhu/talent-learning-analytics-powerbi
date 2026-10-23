"""
Step 4 validation - data model (PBIP / TMDL) loaded in Power BI Desktop.
  A. Project files   : PBIP / report / semantic-model files exist and are valid JSON / follow the official schemas
  B. Offline TMDL    : Microsoft's TmdlSerializer parsed the model; parsed metadata == design spec
  C. Live model      : metadata inside the OPEN Power BI Desktop == design spec (nothing dropped or altered)
  D. Refresh + data  : full refresh in Power BI succeeded; row counts; QA_Checks all PASS inside Power BI
  E. Relationships   : 9 x many-to-one, single direction, active; no orphan keys; filters flow dim -> fact only
  F. Filter results  : headcount / leavers / trainings by every dimension (via relationships) == independent pandas
Usage: python validate_step4.py <project_root> <offline.json> <live.json> <report.txt>
"""
import json, os, sys
import pandas as pd

ROOT, OFF, LIVE, REPORT = sys.argv[1:5]
sys.path.insert(0, os.path.join(ROOT, "03_PowerBI", "validation"))
import mirror_step3 as mirror
mirror.CSV = os.path.join(ROOT, "01_Data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv")
mirror.LKP = os.path.join(ROOT, "01_Data/lookups/HR_Lookups.xlsx")
_, _, MT = mirror.build()
PB = os.path.join(ROOT, "03_PowerBI")
SPEC = json.load(open(os.path.join(PB, "model", "model_spec.json")))
off = json.load(open(OFF, encoding="utf-8-sig"))
live = json.load(open(LIVE, encoding="utf-8-sig"))

res, out = [], []
def check(sec, name, ok, detail=""):
    res.append(bool(ok)); out.append(f"[{'PASS' if ok else 'FAIL'}] {sec}: {name}" + (f" - {detail}" if detail else ""))

# ------------------------------------------------------------------ A. project files
S = "A. Project files"
N = "Talent_Learning_Dashboard"
need = [f"{N}.pbip", f"{N}.Report/definition.pbir", f"{N}.Report/.platform", f"{N}.Report/definition/version.json",
        f"{N}.Report/definition/report.json", f"{N}.Report/definition/pages/pages.json",
        f"{N}.Report/StaticResources/SharedResources/BaseThemes/CY24SU10.json",
        f"{N}.SemanticModel/definition.pbism", f"{N}.SemanticModel/.platform",
        f"{N}.SemanticModel/definition/database.tmdl", f"{N}.SemanticModel/definition/model.tmdl",
        f"{N}.SemanticModel/definition/relationships.tmdl", f"{N}.SemanticModel/definition/expressions.tmdl", ".gitignore"]
missing = [p for p in need if not os.path.isfile(os.path.join(PB, p))]
check(S, f"All {len(need)} required project files exist", not missing, str(missing))
bad = []
for dp, _, fs in os.walk(PB):
    for f in fs:
        if f.endswith((".json", ".pbip", ".pbir", ".pbism", ".platform")) and "validation" not in dp:
            try: json.load(open(os.path.join(dp, f), encoding="utf-8-sig"))
            except Exception as e: bad.append(f"{f}: {e}")
check(S, "Every JSON project file parses", not bad, "; ".join(bad))
pbip = json.load(open(os.path.join(PB, f"{N}.pbip")))
check(S, ".pbip points to the report folder", pbip["artifacts"][0]["report"]["path"] == f"{N}.Report")
pbir = json.load(open(os.path.join(PB, f"{N}.Report/definition.pbir")))
check(S, "definition.pbir binds the report to the local semantic model (byPath)",
      pbir["datasetReference"]["byPath"]["path"] == f"../{N}.SemanticModel" and os.path.isdir(os.path.join(PB, f"{N}.SemanticModel")))
pbism = json.load(open(os.path.join(PB, f"{N}.SemanticModel/definition.pbism")))
check(S, "definition.pbism version >= 4.0 (required for TMDL)", float(pbism["version"]) >= 4.0)
pages = json.load(open(os.path.join(PB, f"{N}.Report/definition/pages/pages.json")))
check(S, "Report page listed in pages.json exists", all(os.path.isfile(os.path.join(PB, f"{N}.Report/definition/pages/{p}/page.json")) for p in pages["pageOrder"]))
gi = open(os.path.join(PB, ".gitignore")).read()
check(S, ".gitignore excludes data cache + local settings (safe for GitHub)", "cache.abf" in gi and "localSettings.json" in gi)
tmdl_tables = sorted(f[:-5] for f in os.listdir(os.path.join(PB, f"{N}.SemanticModel/definition/tables")))
check(S, "One TMDL file per model table (12)", tmdl_tables == sorted(k for k in SPEC if not k.startswith("_r")), str(tmdl_tables))

SCH = os.path.join(PB, "validation", "step4_schema_results.json")
if os.path.isfile(SCH):
    sres = json.load(open(SCH, encoding="utf-8-sig"))
    files_needed = {"report.json", "pages.json", "version.json", "page.json", "definition.pbir", "definition.pbism", ".platform"}
    check(S, f"All {len(sres)} report/project JSON files pass Microsoft's official JSON schemas",
          sres and all(r["ok"] for r in sres) and files_needed <= {os.path.basename(r["file"]) for r in sres},
          "; ".join(f"{r['file']}: {r['errors']}" for r in sres if not r["ok"]))
else:
    check(S, "Official JSON-schema results present (run check_report_schemas.py)", False, SCH)
rep = json.load(open(os.path.join(PB, f"{N}.Report/definition/report.json"), encoding="utf-8-sig"))
check(S, "report.json has the required layoutOptimization property", rep.get("layoutOptimization") in ("None", "PhonePortrait"))

# ------------------------------------------------------------------ helpers to compare metadata with the spec
DT = {"Int64": "int64", "String": "string", "Double": "double"}
SB = {"None": "none", "Sum": "sum", "Average": "average"}
def compare(meta, label):
    S = label
    tabs = {t["name"]: t for t in meta["tables"]}
    exp_tables = {k for k in SPEC if not k.startswith("_r")}
    check(S, "Table set == design (12 tables, no auto date tables)", set(tabs) == exp_tables, f"diff={set(tabs) ^ exp_tables}")
    for tn in sorted(exp_tables & set(tabs)):
        t, sp = tabs[tn], SPEC[tn]
        problems = []
        if bool(t["isHidden"]) != sp["hidden"]:
            problems.append(f"table hidden={t['isHidden']}")
        cols = {c["name"]: c for c in t["columns"]}
        if list(cols) != list(sp["columns"]):
            problems.append(f"columns {list(cols)} != {list(sp['columns'])}")
        for cn, p in sp["columns"].items():
            c = cols.get(cn)
            if not c:
                continue
            if DT.get(c["dataType"], c["dataType"]) != p["dataType"]: problems.append(f"{cn}.dataType={c['dataType']}")
            if bool(c["isHidden"]) != p["isHidden"]: problems.append(f"{cn}.isHidden={c['isHidden']}")
            if bool(c["isKey"]) != p["isKey"]: problems.append(f"{cn}.isKey={c['isKey']}")
            if SB.get(c["summarizeBy"], c["summarizeBy"]) != p["summarizeBy"]: problems.append(f"{cn}.summarizeBy={c['summarizeBy']}")
            if (c.get("sortByColumn") or None) != p.get("sortByColumn"): problems.append(f"{cn}.sortBy={c.get('sortByColumn')}")
            if "formatString" in p and c.get("formatString") != p["formatString"]: problems.append(f"{cn}.format={c.get('formatString')}")
        check(S, f"{tn}: {len(sp['columns'])} columns - types, hidden, key, summarize, sort-by, format == design", not problems, "; ".join(problems))
    rels = sorted((r["from"], r["to"], r["fromCardinality"].lower(), r["toCardinality"].lower(), r["crossFilter"].lower(), r["active"])
                  for r in meta["relationships"])
    exp = sorted((r["from"], r["to"], "many", "one", "onedirection", True) for r in SPEC["_relationships"])
    check(S, "Relationships == design (9 x many-to-one, single direction, active)", rels == exp, f"got={rels}")

# ------------------------------------------------------------------ B. offline TMDL (official serializer)
S = "B. Offline TMDL"
check(S, "Microsoft TmdlSerializer parsed the model folder without errors", off["ok"], str(off.get("error")))
if off["ok"]:
    compare(off, S)
    ex = {e["name"]: e["kind"] for e in off["expressions"]}
    expected_ex = ["ProjectFolder", "fnGetLookup", "fnBandKey", "src_HR", "lkp_Education", "lkp_Satisfaction", "lkp_WorkLifeBalance",
                   "lkp_PerformanceRating", "lkp_BusinessTravel", "lkp_AgeBand", "lkp_TenureBand", "lkp_IncomeBand", "lkp_TrainingBand", "stg_HR"]
    check(S, "14 non-loaded queries (parameter, functions, staging) stored as M expressions",
          list(ex) == expected_ex and set(ex.values()) == {"M"}, str(ex))
    parts_ok = all(len(t["partitions"]) == 1 and t["partitions"][0]["kind"] == "M" and t["partitions"][0]["mode"] == "Import"
                   for t in off["tables"])
    check(S, "Every table has exactly one Import-mode Power Query (M) partition", parts_ok)

# ------------------------------------------------------------------ C. live model in Power BI Desktop
S = "C. Live model"
compare(live, S)

# ------------------------------------------------------------------ D. refresh + data
S = "D. Refresh + data"
Q = live["queries"]
if live["refresh"]:
    check(S, "Full refresh inside Power BI Desktop succeeded", live["refresh"] == "OK", str(live["refresh"]))
else:
    check(S, "Model opened from the saved data cache (no refresh needed) - data checked below", True, "no refresh in this run")
check(S, "All 22 DAX test queries ran without error", not live["errors"] and len(Q) == 22, str(live["errors"]))
rc = dict(zip([c.strip("[]") for c in Q["rowcounts"]["columns"]], Q["rowcounts"]["rows"][0]))
exp_rc = {t: len(MT[t]) for t in MT} | {"QA_Checks": 35, "_Measures": 0}
bad = {t: (rc.get(t) or 0, n) for t, n in exp_rc.items() if (rc.get(t) or 0) != n}
check(S, "Row count of every table == expected (FactEmployee 1,470 ... _Measures 0)", not bad, str(bad))
qa = Q["qa_checks"]["rows"]
fails = [r for r in qa if r[4] != "PASS"]
check(S, "QA_Checks inside Power BI: 35 checks, all PASS", len(qa) == 35 and not fails, str(fails))
tot = dict(zip([c.strip("[]") for c in Q["totals"]["columns"]], Q["totals"]["rows"][0]))
fe = MT["FactEmployee"]
check(S, "Control totals (headcount, leavers, trainings, income, tenure) == Step 2/3",
      tot == {"Headcount": 1470, "Leavers": int(fe.AttritionFlag.sum()), "Trainings": int(fe.TrainingTimesLastYear.sum()),
              "Income": int(fe.MonthlyIncome.sum()), "Tenure": int(fe.YearsAtCompany.sum())}, str(tot))

# ------------------------------------------------------------------ E. relationship behaviour
S = "E. Relationships"
orph = dict(zip([c.strip("[]") for c in Q["orphans"]["columns"]], Q["orphans"]["rows"][0]))
check(S, "No fact row without a matching dimension row (all 9 relationships)", all((v or 0) == 0 for v in orph.values()) and len(orph) == 9, str(orph))
d = dict(zip([c.strip("[]") for c in Q["direction"]["columns"]], Q["direction"]["rows"][0]))
check(S, "Filter flows dimension -> fact (Sales filter gives 446 fact rows)", d["FactRowsWhenDeptFiltered"] == 446, str(d))
check(S, "Filter does NOT flow fact -> dimension (single direction; DimDepartment stays 3 rows)", d["DeptRowsWhenFactFiltered"] == 3, str(d))
check(S, "Filter does NOT flow fact -> DimEmployee (stays 1,470 rows)", d["EmployeeRowsWhenFactFiltered"] == 1470, str(d))

# ------------------------------------------------------------------ F. results through the relationships == pandas
S = "F. Filter results"
def frame(qname):
    q = Q[qname]
    return pd.DataFrame(q["rows"], columns=[c.split("[")[-1].strip("]") for c in q["columns"]])
J = fe.merge(MT["DimEmployee"], on="EmployeeID")
for dim in ["DimDepartment", "DimJobRole", "DimEducation", "DimJobSatisfaction", "DimAgeBand", "DimTenureBand", "DimIncomeBand", "DimTrainingBand"]:
    J = J.merge(MT[dim], on=MT[dim].columns[0])
label = {"DimDepartment": "Department", "DimJobRole": "JobRole", "DimEducation": "EducationLevel", "DimJobSatisfaction": "JobSatisfaction",
         "DimAgeBand": "AgeBand", "DimTenureBand": "TenureBand", "DimIncomeBand": "IncomeBand", "DimTrainingBand": "TrainingBand",
         "DimEmployee": "EmployeeStatus"}
for dim, col in label.items():
    got = frame(f"by_{dim}").set_index(col).sort_index()
    exp = J.groupby(col).agg(Headcount=("EmployeeID", "count"), Leavers=("AttritionFlag", "sum"), Trainings=("TrainingTimesLastYear", "sum")).sort_index()
    ok = list(got.index) == list(exp.index) and (got[["Headcount", "Leavers", "Trainings"]].astype(int).values == exp.values).all()
    check(S, f"By {dim}[{col}]: headcount, leavers, trainings == pandas ({len(exp)} members, no blank member)", ok,
          "" if ok else f"got={got.to_dict()} exp={exp.to_dict()}")
for col in ["OverTime", "BusinessTravel", "WorkLifeBalance", "EnvironmentSatisfaction", "PerformanceRating", "Gender", "MaritalStatus"]:
    got = frame(f"by_DimEmployee_{col}").set_index(col).sort_index()
    exp = J.groupby(col).agg(Headcount=("EmployeeID", "count"), Leavers=("AttritionFlag", "sum")).sort_index()
    ok = list(got.index) == list(exp.index) and (got[["Headcount", "Leavers"]].astype(int).values == exp.values).all()
    check(S, f"By DimEmployee[{col}]: headcount, leavers == pandas", ok, "" if ok else f"got={got.to_dict()} exp={exp.to_dict()}")
got = frame("two_dims").set_index(["Department", "TenureBand"]).sort_index()
exp = J.groupby(["Department", "TenureBand"]).agg(Headcount=("EmployeeID", "count"), Leavers=("AttritionFlag", "sum")).sort_index()
ok = list(got.index) == list(exp.index) and (got[["Headcount", "Leavers"]].astype(int).values == exp.values).all()
check(S, f"Two dimensions at once (Department x TenureBand, {len(exp)} cells) == pandas", ok)
check(S, "Step 2 headline still holds through the model: Sales attrition 20.6%",
      round(frame("by_DimDepartment").set_index("Department").loc["Sales"].pipe(lambda r: r.Leavers / r.Headcount), 3) == 0.206)

passed, total = sum(res), len(res)
text = f"STEP 4 VALIDATION: {passed}/{total} checks passed\n\n" + "\n".join(out)
print(text)
open(REPORT, "w", encoding="utf-8").write(text + "\n")
sys.exit(0 if passed == total else 1)
