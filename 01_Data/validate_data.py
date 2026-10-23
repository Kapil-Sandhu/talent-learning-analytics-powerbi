"""
Step 1 validation - Talent & Learning Analytics Dashboard
Checks the folder structure and the raw IBM HR Attrition CSV.
Run:  python 01_Data/validate_data.py   (from the project root)
Uses only the Python standard library.
"""
import csv, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "01_Data", "raw", "WA_Fn-UseC_-HR-Employee-Attrition.csv")
REPORT = os.path.join(ROOT, "01_Data", "validation_report_step1.txt")

FOLDERS = ["01_Data/raw", "01_Data/lookups", "02_Excel_Profiling", "03_PowerBI",
           "04_Docs", "05_Presentation", "screenshots"]

EXPECTED_COLS = ["Age", "Attrition", "BusinessTravel", "DailyRate", "Department",
    "DistanceFromHome", "Education", "EducationField", "EmployeeCount", "EmployeeNumber",
    "EnvironmentSatisfaction", "Gender", "HourlyRate", "JobInvolvement", "JobLevel",
    "JobRole", "JobSatisfaction", "MaritalStatus", "MonthlyIncome", "MonthlyRate",
    "NumCompaniesWorked", "Over18", "OverTime", "PercentSalaryHike", "PerformanceRating",
    "RelationshipSatisfaction", "StandardHours", "StockOptionLevel", "TotalWorkingYears",
    "TrainingTimesLastYear", "WorkLifeBalance", "YearsAtCompany", "YearsInCurrentRole",
    "YearsSinceLastPromotion", "YearsWithCurrManager"]

RANGES = {"Age": (18, 60), "Education": (1, 5), "EnvironmentSatisfaction": (1, 4),
          "JobInvolvement": (1, 4), "JobLevel": (1, 5), "JobSatisfaction": (1, 4),
          "PerformanceRating": (1, 4), "RelationshipSatisfaction": (1, 4),
          "StockOptionLevel": (0, 3), "TrainingTimesLastYear": (0, 6),
          "WorkLifeBalance": (1, 4), "YearsAtCompany": (0, 40), "MonthlyIncome": (1000, 20000)}

CATEGORIES = {"Attrition": {"Yes", "No"}, "OverTime": {"Yes", "No"},
              "Gender": {"Male", "Female"},
              "Department": {"Sales", "Research & Development", "Human Resources"},
              "BusinessTravel": {"Travel_Rarely", "Travel_Frequently", "Non-Travel"}}

results, lines = [], []
def check(name, ok, detail=""):
    results.append(ok)
    lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))

# 1. Folders
for f in FOLDERS:
    check(f"Folder exists: {f}", os.path.isdir(os.path.join(ROOT, f)))

# 2. Raw file
if not os.path.isfile(RAW):
    check("Raw CSV present", False, f"not found at {RAW}")
else:
    check("Raw CSV present", True, f"{os.path.getsize(RAW):,} bytes")
    with open(RAW, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    cols = list(rows[0].keys()) if rows else []
    check("Row count = 1,470", len(rows) == 1470, f"found {len(rows)}")
    check("Column count = 35", len(cols) == 35, f"found {len(cols)}")
    missing = [c for c in EXPECTED_COLS if c not in cols]
    extra = [c for c in cols if c not in EXPECTED_COLS]
    check("All expected columns present", not missing and not extra,
          f"missing={missing} extra={extra}" if (missing or extra) else "")
    blanks = {c: sum(1 for r in rows if (r.get(c) or "").strip() == "") for c in cols}
    blanks = {c: n for c, n in blanks.items() if n}
    check("No missing values", not blanks, str(blanks) if blanks else "")
    ids = [r["EmployeeNumber"] for r in rows]
    check("EmployeeNumber is unique", len(set(ids)) == len(ids),
          f"{len(ids) - len(set(ids))} duplicates" if len(set(ids)) != len(ids) else "")
    for col, exp in [("EmployeeCount", "1"), ("Over18", "Y"), ("StandardHours", "80")]:
        vals = set(r[col] for r in rows)
        check(f"{col} is constant ({exp}) -> drop in Power Query", vals == {exp}, f"values={vals}")
    for col, allowed in CATEGORIES.items():
        vals = set(r[col] for r in rows)
        check(f"{col} values valid", vals <= allowed, f"values={sorted(vals)}")
    for col, (lo, hi) in RANGES.items():
        try:
            nums = [int(r[col]) for r in rows]
            check(f"{col} in range {lo}-{hi}", min(nums) >= lo and max(nums) <= hi,
                  f"min={min(nums)} max={max(nums)}")
        except ValueError as e:
            check(f"{col} is numeric", False, str(e))
    # Logic checks
    bad = sum(1 for r in rows if int(r["YearsAtCompany"]) > int(r["TotalWorkingYears"]))
    check("YearsAtCompany <= TotalWorkingYears", bad == 0, f"{bad} violations")
    bad = sum(1 for r in rows if int(r["YearsInCurrentRole"]) > int(r["YearsAtCompany"]))
    check("YearsInCurrentRole <= YearsAtCompany", bad == 0, f"{bad} violations")

    # Summary profile (for reference, not pass/fail)
    att = Counter(r["Attrition"] for r in rows)
    n = len(rows)
    lines.append("")
    lines.append("---- Quick profile ----")
    lines.append(f"Headcount: {n}")
    lines.append(f"Leavers: {att['Yes']}  | Attrition rate: {att['Yes']/n:.1%}")
    for dim in ["Department", "OverTime"]:
        lines.append(f"Attrition by {dim}:")
        for k, v in sorted(Counter(r[dim] for r in rows).items()):
            lv = sum(1 for r in rows if r[dim] == k and r["Attrition"] == "Yes")
            lines.append(f"   {k:<25} headcount={v:<5} attrition={lv/v:.1%}")
    tr = [int(r["TrainingTimesLastYear"]) for r in rows]
    lines.append(f"Avg training times/employee: {sum(tr)/n:.2f} | zero training: {tr.count(0)/n:.1%}")

passed, total = sum(results), len(results)
lines.insert(0, f"STEP 1 VALIDATION: {passed}/{total} checks passed\n")
out = "\n".join(lines)
print(out)
with open(REPORT, "w", encoding="utf-8") as fh:
    fh.write(out + "\n")
sys.exit(0 if passed == total else 1)
