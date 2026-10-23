"""
Number helpers for the Step 8 documents (README, user guide, deck).
Every number that goes into a document is produced here from a SOURCE and logged in a manifest, so
validate_step8.py can prove that no number was typed by hand and re-check each one against Power BI.

Sources:
  facts:<path>     04_Docs/insights_facts.json (Step 7 analysis of the raw CSV)
  measure:<name>   company-level value of a DAX measure, computed with pandas from the raw CSV (expected_measures.py),
                   formatted with the measure's own format string from the model (as Power BI displays it)
  project:<what>   counted from the project files (pages, visuals, measures, queries, ...)
  validation:<n>   "passed/total" read from validation_report_step<n>.txt
"""
import csv, glob, json, os, re, sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = None
F = None
MANIFEST = []
_EXPECTED = None
MODEL = None

def init(root):
    global ROOT, F, _EXPECTED, MODEL
    ROOT = root
    F = json.load(open(os.path.join(root, "04_Docs", "insights_facts.json"), encoding="utf-8"))
    sys.path.insert(0, os.path.join(root, "03_PowerBI", "validation"))
    from expected_measures import RAW, expected
    _EXPECTED = expected(RAW)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tmdl_info
    MODEL = tmdl_info.read_model(root)

def r(x, dp):
    """Round half away from zero, like Power BI's display formatting."""
    q = Decimal(1).scaleb(-dp)
    d = Decimal(repr(float(x)))
    return d.quantize(q, rounding=ROUND_HALF_UP) if d >= 0 else -(-d).quantize(q, rounding=ROUND_HALF_UP)

def put(text, source, value):
    MANIFEST.append({"text": text, "source": source, "value": value}); return text

def get(path):
    v = F
    for k in path.split("."): v = v[k]
    return v

# ---- facts
def pct(path, dp=1):   v = get(path); return put(f"{r(v * 100, dp)}%", "facts:" + path, v)
def pts(path, dp=1):   v = get(path); return put(("+" if v >= 0 else "") + f"{r(v, dp)} pts", "facts:" + path, v)
def num(path, dp=0):   v = get(path); return put(f"{r(v, dp):,}", "facts:" + path, v)
def ratio(path, dp=1): v = get(path); return put(f"{r(v, dp)}x", "facts:" + path, v)
def orr(path, dp=1):   v = get(path); return put(f"{r(v, dp)}", "facts:" + path, v)

# ---- measures, formatted with the model's format string
def fmt(value, fs):
    if fs == "#,##0": return f"{r(value, 0):,}"
    if fs == "0.0%": return f"{r(value * 100, 1)}%"
    if fs == "0.0": return f"{r(value, 1)}"
    if fs == "0.00": return f"{r(value, 2)}"
    if fs == '0.0"x"': return f"{r(value, 1)}x"
    if fs == "+0.0%;-0.0%;0.0%":
        t = r(value * 100, 1); return "0.0%" if t == 0 else (f"+{t}%" if t > 0 else f"{t}%")
    raise ValueError(fs)
def measure_fs(name):
    for t in MODEL["tables"].values():
        for m in t["measures"]:
            if m["name"] == name: return m["format"]
    raise KeyError(name)
def mval(name):
    v = _EXPECTED[name]; return put(fmt(v, measure_fs(name)), "measure:" + name, v)

# ---- project facts (counted from the files)
def project_counts():
    rd = os.path.join(ROOT, "03_PowerBI", "Talent_Learning_Dashboard.Report", "definition")
    pages = json.load(open(os.path.join(rd, "pages", "pages.json"), encoding="utf-8-sig"))["pageOrder"]
    names = [json.load(open(os.path.join(rd, "pages", p, "page.json"), encoding="utf-8-sig"))["displayName"] for p in pages]
    visuals = len(glob.glob(os.path.join(rd, "pages", "*", "visuals", "*", "visual.json")))
    ms = [m for t in MODEL["tables"].values() for m in t["measures"]]
    pq = len(glob.glob(os.path.join(ROOT, "03_PowerBI", "PowerQuery", "*.pq")))
    with open(os.path.join(ROOT, "01_Data", "raw", "WA_Fn-UseC_-HR-Employee-Attrition.csv"), encoding="utf-8-sig") as f:
        rd_ = csv.reader(f); header = next(rd_); rows = sum(1 for _ in rd_)
    live = json.load(open(os.path.join(ROOT, "03_PowerBI", "validation", "step6_live_values.json"), encoding="utf-8-sig"))
    qa = len(next(v for k, v in live["queries"].items() if k.endswith("|qa"))["rows"])   # rows Power BI returned for QA_Checks
    rels = MODEL["relationships"]
    dims = sorted({x["to"][0] for x in rels})
    return {"pages": len(pages), "page_names": names, "visuals": visuals, "measures": len(ms),
            "folders": len({m["folder"] for m in ms}), "queries": pq, "csv_rows": rows, "csv_cols": len(header),
            "relationships": len(rels), "dimensions": len(dims), "qa_checks": qa}
_PC = None
def pc(key):
    global _PC
    _PC = _PC or project_counts()
    v = _PC[key]
    return put(f"{v:,}", "project:" + key, v)
def page_names():
    global _PC
    _PC = _PC or project_counts()
    return _PC["page_names"]

# ---- validation tallies
def validation(step):
    files = {1: "01_Data/validation_report_step1.txt", 2: "02_Excel_Profiling/validation_report_step2.txt",
             3: "03_PowerBI/validation/validation_report_step3.txt", 4: "03_PowerBI/validation/validation_report_step4.txt",
             5: "03_PowerBI/validation/validation_report_step5.txt", 6: "03_PowerBI/validation/validation_report_step6.txt",
             7: "04_Docs/analysis/validation_report_step7.txt"}
    head = open(os.path.join(ROOT, files[step]), encoding="utf-8-sig").readline()
    m = re.search(r"(\d+)/(\d+) checks passed", head)
    a, b = int(m.group(1)), int(m.group(2))
    assert a == b, f"step {step} report is not all-pass: {head}"
    return put(f"{a}/{b}", f"validation:{step}", a)
def validation_file(step):
    return {1: "01_Data/validation_report_step1.txt", 2: "02_Excel_Profiling/validation_report_step2.txt",
            3: "03_PowerBI/validation/validation_report_step3.txt", 4: "03_PowerBI/validation/validation_report_step4.txt",
            5: "03_PowerBI/validation/validation_report_step5.txt", 6: "03_PowerBI/validation/validation_report_step6.txt",
            7: "04_Docs/analysis/validation_report_step7.txt"}[step]
def negative_controls_step7():
    t = open(os.path.join(ROOT, validation_file(7)), encoding="utf-8-sig").read()
    m = re.search(r"NEGATIVE CONTROLS: (\d+)/(\d+)", t)
    return put(f"{m.group(1)}/{m.group(2)}", "validation:7-negative", int(m.group(1)))

def save_manifest(path):
    json.dump(MANIFEST, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

def validation_total():
    """Sum of all checks passed across Steps 1-7 (each report must be all-pass)."""
    tot = 0
    for s in range(1, 8):
        head = open(os.path.join(ROOT, validation_file(s)), encoding="utf-8-sig").readline()
        a, b = map(int, re.search(r"(\d+)/(\d+) checks passed", head).groups()); assert a == b; tot += a
    return put(f"{tot:,}", "validation:total", tot)
