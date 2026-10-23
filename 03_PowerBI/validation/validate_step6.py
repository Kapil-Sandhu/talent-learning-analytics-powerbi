"""
Step 6 validation - report pages.
  A. Schemas      : every report file (pages, 63 visuals) valid against Microsoft's OFFICIAL JSON schemas, incl. all $ref'd
                    sub-schemas (semanticQuery, filterConfiguration, visualConfiguration, formattingObjectDefinitions)
  B. Fields       : every field used by a visual / filter exists in the model, as the right kind (column vs measure)
  C. Visual roles : each visual type uses the data roles Power BI expects (card: Values; charts: Category + Y; ...)
  D. Layout       : every visual inside the 1280x720 page, no overlapping visuals, readable minimum sizes
  E. Pages        : pages.json <-> page folders, unique ids/names, drill-through wired to an existing filter + field
  F. Numbers      : what every card / chart / matrix / table will show (DAX run in Power BI) == pandas from the RAW CSV
  G. Rendering    : every page opened in Power BI Desktop - no visual error text, every chart title and card value visible
Usage: python validate_step6.py <project_root> <model_offline.json> <live_values.json> <ui_pages.json> <report.txt>
"""
import glob, json, math, os, re, sys, urllib.request
import pandas as pd
from jsonschema import Draft7Validator, RefResolver
from openpyxl import load_workbook

ROOT, MODEL, LIVE, UI, REPORT = sys.argv[1:6]
PB = os.path.join(ROOT, "03_PowerBI")
RD = os.path.join(PB, "Talent_Learning_Dashboard.Report", "definition")
SPEC = json.load(open(os.path.join(PB, "report", "report_spec.json"), encoding="utf-8"))
res, out = [], []
def check(sec, name, ok, detail=""):
    res.append(bool(ok)); out.append(f"[{'PASS' if ok else 'FAIL'}] {sec}: {name}" + (f" - {detail}" if detail else ""))

# ------------------------------------------------------------------ A. official schemas (with $ref resolution + cache)
S = "A. Schemas"
CACHE = os.path.join(PB, "validation", "schemas"); os.makedirs(CACHE, exist_ok=True)
def fetch(uri):
    f = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9.]+", "_", uri.split("json-schemas/")[-1]))
    if not os.path.isfile(f):
        raw = uri.replace("https://developer.microsoft.com/json-schemas/", "https://raw.githubusercontent.com/microsoft/json-schemas/main/")
        # Microsoft's embedded schemas declare $id ".../schema.embedded.json" but the file is named "schema-embedded.json"
        raw = raw.replace("/schema.embedded.json", "/schema-embedded.json")
        urllib.request.urlretrieve(raw, f)
    return json.load(open(f, encoding="utf-8"))
def validate(doc):
    sch = fetch(doc["$schema"])
    resolver = RefResolver(base_uri=doc["$schema"], referrer=sch, handlers={"https": fetch})
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in Draft7Validator(sch, resolver=resolver).iter_errors(doc)]
files = sorted(glob.glob(os.path.join(RD, "**", "*.json"), recursive=True))
bad, n_vis = {}, 0
for f in files:
    doc = json.load(open(f, encoding="utf-8-sig"))
    if "$schema" not in doc: bad[f] = ["no $schema"]; continue
    errs = validate(doc)
    if errs: bad[os.path.relpath(f, RD)] = errs[:3]
    n_vis += f.endswith("visual.json")
check(S, f"All {len(files)} report definition files ({n_vis} visuals) pass Microsoft's official schemas incl. referenced sub-schemas",
      not bad and n_vis == sum(len(p["visuals"]) for p in SPEC["pages"]), json.dumps(bad)[:600])
neg = json.load(open(next(f for f in files if f.endswith("visual.json")), encoding="utf-8-sig"))
neg["position"]["width"] = "wide"; neg["visual"]["bogusProperty"] = 1
check(S, "Negative control: a deliberately broken visual is rejected by the schema check", len(validate(neg)) >= 1)

# ------------------------------------------------------------------ B. fields exist in the model, right kind
S = "B. Fields"
model = json.load(open(MODEL, encoding="utf-8-sig"))
columns = {(t["name"], c["name"]) for t in model["tables"] for c in t["columns"]}
measures = {(m["table"], m["name"]) for m in model["measures"]}
def refs(o, acc):
    if isinstance(o, dict):
        for kind in ("Column", "Measure"):
            if kind in o and isinstance(o[kind], dict) and "Property" in o[kind]:
                ent = o[kind].get("Expression", {}).get("SourceRef", {}).get("Entity")
                if ent: acc.append((kind, ent, o[kind]["Property"]))
        for v in o.values(): refs(v, acc)
    elif isinstance(o, list):
        for v in o: refs(v, acc)
    return acc
all_refs, wrong = [], []
for f in files:
    doc = json.load(open(f, encoding="utf-8-sig"))
    for kind, e, p in refs(doc, []):
        all_refs.append((kind, e, p))
        ok = (e, p) in (columns if kind == "Column" else measures)
        if not ok: wrong.append(f"{os.path.relpath(f, RD)[:40]}: {kind} {e}.{p}")
check(S, f"All {len(all_refs)} field references point to an existing model column / measure of the right kind", not wrong and all_refs, "; ".join(wrong[:5]))
qr_bad = []
for f in glob.glob(os.path.join(RD, "pages", "*", "visuals", "*", "visual.json")):
    v = json.load(open(f, encoding="utf-8-sig"))["visual"]
    for role, st in v.get("query", {}).get("queryState", {}).items():
        for pj in st["projections"]:
            fld = pj["field"]
            if "Aggregation" in fld:
                inner = fld["Aggregation"]["Expression"]["Column"]; fn = {0: "Sum", 1: "Avg"}.get(fld["Aggregation"]["Function"], "?")
                e = inner["Expression"]["SourceRef"]["Entity"]; p = inner["Property"]
                if pj["queryRef"] != f"{fn}({e}.{p})": qr_bad.append(pj["queryRef"])
                continue
            kind = "Measure" if "Measure" in fld else "Column"
            e = fld[kind]["Expression"]["SourceRef"]["Entity"]; p = fld[kind]["Property"]
            if pj["queryRef"] != f"{e}.{p}" or pj.get("nativeQueryRef") != p: qr_bad.append(pj["queryRef"])
check(S, "Every projection's queryRef / nativeQueryRef matches its field", not qr_bad, str(qr_bad[:5]))
hidden_cols = {(t["name"], c["name"]) for t in model["tables"] for c in t["columns"] if c["isHidden"]}
used_hidden = sorted({f"{e}.{p}" for k, e, p in all_refs if k == "Column" and (e, p) in hidden_cols})
check(S, "Visuals use no hidden helper columns (keys, sort columns)", not used_hidden, str(used_hidden))

# ------------------------------------------------------------------ C. roles per visual type
S = "C. Visual roles"
ROLES = {"card": {"Values"}, "clusteredBarChart": {"Category", "Y"}, "columnChart": {"Category", "Y"}, "slicer": {"Values"},
         "pivotTable": {"Rows", "Values"}, "tableEx": {"Values"}, "textbox": set(), "actionButton": set()}
role_bad, types = [], {}
for f in glob.glob(os.path.join(RD, "pages", "*", "visuals", "*", "visual.json")):
    v = json.load(open(f, encoding="utf-8-sig"))["visual"]
    t = v["visualType"]; types[t] = types.get(t, 0) + 1
    got = set(v.get("query", {}).get("queryState", {}).keys())
    if t not in ROLES or got != ROLES[t]: role_bad.append(f"{t}: {got}")
    if t in ("clusteredBarChart", "columnChart"):
        y = v["query"]["queryState"]["Y"]["projections"]
        if not all("Measure" in pj["field"] for pj in y): role_bad.append(f"{t}: Y is not a measure")
    if t == "card" and not all("Measure" in pj["field"] for pj in v["query"]["queryState"]["Values"]["projections"]):
        role_bad.append("card value is not a measure")
check(S, f"Every visual uses the expected data roles ({types})", not role_bad, "; ".join(role_bad[:5]))

pres_bad = []
for f in glob.glob(os.path.join(RD, "pages", "*", "visuals", "*", "visual.json")):
    v = json.load(open(f, encoding="utf-8-sig"))["visual"]; t = v["visualType"]; qs = v.get("query", {}).get("queryState", {})
    for role in ("Category", "Rows") + (("Values",) if t == "slicer" else ()):
        for pj in qs.get(role, {}).get("projections", []):
            if "Column" in pj["field"] and not pj.get("displayName"): pres_bad.append(f"{t}: {pj['queryRef']} has no friendly name")
check(S, "Every axis / row / slicer field shows a friendly name (no technical column names)", not pres_bad, "; ".join(pres_bad[:5]))
sort_bad = []
for pg in SPEC["pages"]:
    for vs in pg["visuals"]:
        if vs["type"] == "pivotTable":
            d = json.load(open(os.path.join(RD, "pages", pg["id"], "visuals", vs["name"], "visual.json"), encoding="utf-8-sig"))
            got = d["visual"]["query"]["sortDefinition"]["sort"][0]["field"]["Measure"]["Property"]
            if got != vs["sort_by"] or ("gap" in vs["title"] and got != "Attrition vs Company (pts)"): sort_bad.append(f"{vs['key']} sorted by {got}")
check(S, "Matrix is sorted by the measure its title promises (attrition gap)", not sort_bad, str(sort_bad))
per_emp = [v for p in SPEC["pages"] for v in p["visuals"] if v["type"] == "tableEx" and "DimEmployee.EmployeeID" in v.get("columns", [])]
check(S, "Employee table shows per-employee values from fact columns (no averaged measures per person)",
      per_emp and not per_emp[0]["measures"] and len(per_emp[0]["aggs"]) == 5)

# ------------------------------------------------------------------ D. layout
S = "D. Layout"
for pg in SPEC["pages"]:
    vs = pg["visuals"]
    outside = [v["key"] for v in vs if v["x"] < 0 or v["y"] < 0 or v["x"] + v["w"] > 1280 + 1e-6 or v["y"] + v["h"] > 720 + 1e-6]
    overlaps = [(a["key"], b["key"]) for i, a in enumerate(vs) for b in vs[i + 1:]
                if a["x"] < b["x"] + b["w"] - 1e-6 and b["x"] < a["x"] + a["w"] - 1e-6 and a["y"] < b["y"] + b["h"] - 1e-6 and b["y"] < a["y"] + a["h"] - 1e-6]
    small = [v["key"] for v in vs if v["type"] not in ("textbox", "actionButton") and (v["w"] < 140 or v["h"] < 56)]
    check(S, f"{pg['name']}: {len(vs)} visuals inside the page, no overlaps, none too small", not outside and not overlaps and not small,
          f"outside={outside} overlaps={overlaps} small={small}")
    files_pos = {}
    for f in glob.glob(os.path.join(RD, "pages", pg["id"], "visuals", "*", "visual.json")):
        d = json.load(open(f, encoding="utf-8-sig")); files_pos[d["name"]] = d["position"]
    mism = [v["key"] for v in vs if v["name"] not in files_pos or abs(files_pos[v["name"]]["x"] - v["x"]) > 1e-6 or abs(files_pos[v["name"]]["width"] - v["w"]) > 1e-6]
    check(S, f"{pg['name']}: visual files on disk == layout spec (no stray or missing visual files)",
          not mism and len(files_pos) == len(vs), f"mismatch={mism} files={len(files_pos)} spec={len(vs)}")

# ------------------------------------------------------------------ E. pages + drill-through
S = "E. Pages"
pm = json.load(open(os.path.join(RD, "pages", "pages.json"), encoding="utf-8-sig"))
folders = sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(RD, "pages", "*", "page.json")))
check(S, f"pages.json lists exactly the {len(folders)} page folders; active page exists", sorted(pm["pageOrder"]) == folders and pm["activePageName"] in folders,
      f"{pm['pageOrder']} vs {folders}")
names = []
for pid in pm["pageOrder"]:
    pgd = json.load(open(os.path.join(RD, "pages", pid, "page.json"), encoding="utf-8-sig"))
    names.append(pgd["displayName"])
    if pgd["name"] != pid: check(S, f"page {pid} name == folder", False)
check(S, "Page names unique and in the planned order", names == [p["name"] for p in SPEC["pages"]] and len(set(names)) == len(names), str(names))
dt = [p for p in SPEC["pages"] if p.get("drillthrough")]
ok = False
if dt:
    pgd = json.load(open(os.path.join(RD, "pages", dt[0]["id"], "page.json"), encoding="utf-8-sig"))
    flt = {f["name"]: f for f in pgd.get("filterConfig", {}).get("filters", [])}
    pb = pgd.get("pageBinding", {})
    par = pb.get("parameters", [{}])[0]
    ok = pb.get("type") == "Drillthrough" and par.get("boundFilter") in flt and par.get("fieldExpr") == flt[par["boundFilter"]]["field"] \
         and flt[par["boundFilter"]].get("howCreated") == "Drillthrough" and len(flt) == 1 and len(pb.get("parameters", [])) == 1 \
         and ("Column", "DimJobRole", "JobRole") in [(k, e, p) for k, e, p in refs(par["fieldExpr"], [])]
    sources = [p["name"] for p in SPEC["pages"] for v in p["visuals"] if "DimJobRole.JobRole" in v.get("columns", []) and v["type"] != "slicer" and not p.get("drillthrough")]
check(S, "Employee Details is a drill-through page: one filter marked howCreated=Drillthrough on DimJobRole[JobRole], bound by the page binding (as Power BI Desktop writes it)", ok and dt[0]["name"] == "Employee Details")
back = [v for v in dt[0]["visuals"] if v["type"] == "actionButton"] if dt else []
bdoc = json.load(open(os.path.join(RD, "pages", dt[0]["id"], "visuals", back[0]["name"], "visual.json"), encoding="utf-8-sig")) if back else {}
check(S, "Drill-through page has a Back button (actionButton with visualLink type Back)",
      bdoc.get("visual", {}).get("visualContainerObjects", {}).get("visualLink", [{}])[0].get("properties", {}).get("type") == {"expr": {"Literal": {"Value": "'Back'"}}})
check(S, "At least one visual on another page shows JobRole, so drill-through can be started", dt and len(sources) >= 2, str(sources))

# ------------------------------------------------------------------ F. numbers each visual will show == pandas
S = "F. Numbers"
sys.path.insert(0, os.path.join(PB, "validation"))
from expected_measures import RAW as r, expected, eq, COLMAP
live = json.load(open(LIVE, encoding="utf-8-sig"))
check(S, "All visual queries ran in Power BI without error", not live["errors"], str(live["errors"])[:400])
cells, problems = 0, []
for pg in SPEC["pages"]:
    for v in pg["visuals"]:
        q = live["queries"].get(f"{pg['id']}|{v['key']}")
        if v["type"] in ("textbox", "actionButton"): continue
        if q is None or "error" in q: problems.append(f"{pg['name']}/{v['key']}: no result"); continue
        rows = [dict(zip(q["columns"], rw)) for rw in q["rows"]]
        if v["type"] == "slicer":
            c = COLMAP[v["columns"][0]]
            got = sorted(str(rw[q["columns"][0]]) for rw in rows); exp = sorted(str(x) for x in r[c].unique())
            cells += len(got)
            if got != exp: problems.append(f"{pg['name']}/{v['key']}: slicer items {got[:4]} vs {exp[:4]}")
            continue
        if v["type"] == "card":
            e = expected(r)[v["measures"][0]]; g = rows[0]["[v]"]; cells += 1
            if not eq(g, e): problems.append(f"{pg['name']}/{v['key']}: {g} vs {e}")
            continue
        if v["columns"] and v["columns"][0].startswith("QA_Checks"):
            continue
        keys = [COLMAP[c] for c in v["columns"]]
        for rw in rows:
            vals = [rw[f"{c.split('.')[0]}[{c.split('.')[1]}]"] for c in v["columns"]]
            g = r
            for k, val in zip(keys, vals): g = g[g[k].astype(str) == str(val)]
            e = expected(g)
            for m in v["measures"]:
                cells += 1
                if not eq(rw[f"[{m}]"], e[m]): problems.append(f"{pg['name']}/{v['key']} {vals} {m}: {rw[f'[{m}]']} vs {e[m]}")
        if v["type"] in ("clusteredBarChart", "columnChart", "pivotTable"):
            members = sorted(str(x) for x in r[keys[0]].unique())
            if sorted(str(rw[f"{v['columns'][0].split('.')[0]}[{v['columns'][0].split('.')[1]}]"]) for rw in rows) != members:
                problems.append(f"{pg['name']}/{v['key']}: categories differ from data")
        AGGCOL = {"FactEmployee.Age": "Age", "FactEmployee.YearsAtCompany": "YearsAtCompany", "FactEmployee.TrainingTimesLastYear": "TrainingTimesLastYear",
                  "FactEmployee.JobSatisfactionScore": "JobSatisfaction", "FactEmployee.MonthlyIncome": "MonthlyIncome"}
        for a in v.get("aggs", []):
            byid = r.set_index("EmployeeNumber")[AGGCOL[a["col"]]]
            akey = "[" + a["alias"] + "]"
            for rw in rows:
                cells += 1
                if not eq(rw[akey], float(byid[rw["DimEmployee[EmployeeID]"]])):
                    problems.append(pg["name"] + "/" + v["key"] + " employee " + str(rw["DimEmployee[EmployeeID]"]) + " " + a["alias"] + ": " + str(rw[akey]))
        if v["type"] == "tableEx" and len(rows) != len(r):
            problems.append(f"{pg['name']}/{v['key']}: {len(rows)} employee rows, expected {len(r)}")
# exact number of values the visuals must return, derived from the raw data (not from Power BI):
expected_cells = 0
for pg in SPEC["pages"]:
    for v in pg["visuals"]:
        if v["type"] in ("textbox", "actionButton") or (v.get("columns") and v["columns"][0].startswith("QA_Checks")): continue
        if v["type"] == "card": expected_cells += 1
        elif v["type"] == "slicer": expected_cells += r[COLMAP[v["columns"][0]]].nunique()
        elif v["type"] == "tableEx": expected_cells += len(r) * (len(v["measures"]) + len(v.get("aggs", [])))
        else: expected_cells += r[COLMAP[v["columns"][0]]].nunique() * len(v["measures"])
check(S, f"Every card, chart, slicer, matrix and table value == pandas from the raw CSV ({cells:,} of {expected_cells:,} expected values)",
      not problems and cells == expected_cells, "; ".join(problems[:5]))
qa = live["queries"].get(next(f"{p['id']}|qa" for p in SPEC["pages"] if p["name"] == "Data Quality"), {})
qrows = [dict(zip(qa.get("columns", []), x)) for x in qa.get("rows", [])]
check(S, "Data Quality page table: 35 checks, all PASS", len(qrows) == 35 and all(x.get("QA_Checks[Result]") == "PASS" for x in qrows))
sl = live["queries"].get("slicer_test_sales", {})
srow = dict(zip(sl.get("columns", []), (sl.get("rows") or [[None]])[0]))
sales = r[r.Department == "Sales"]; es = expected(sales)
check(S, "Slicer simulation (Department = Sales): Overview cards show the Sales values (446 headcount, 20.6%)",
      all(eq(srow.get(f"[{m}]"), es[m]) for m in ["Headcount", "Leavers", "Attrition Rate", "Avg Tenure (Years)", "Training per Employee", "Overtime %"]), str(srow))

# ------------------------------------------------------------------ G. rendering in Power BI Desktop
S = "G. Rendering"
ui = json.load(open(UI, encoding="utf-8-sig"))
check(S, "Power BI opened the project with no dialog (only built-in DAX query / TMDL panes)",
      all(d in ("Run DAX queries on your model", "Edit your model with TMDL") for d in ui["dialogs"]), str(ui["dialogs"]))
fmt = {"#,##0": lambda v: f"{v:,.0f}", "0.0%": lambda v: f"{v * 100:.1f}%", "0.0": lambda v: f"{v:.1f}", "0.00": lambda v: f"{v:.2f}",
       '0.0"x"': lambda v: f"{v:.1f}x", "+0.0%;-0.0%;0.0%": lambda v: f"{v * 100:+.1f}%"}
sys.path.insert(0, os.path.join(PB, "model"))
from measures_spec import MEASURES
mfmt = {m["name"]: m["fmt"] for m in MEASURES}
for pg in SPEC["pages"]:
    u = ui["pages"].get(pg["name"])
    if not u:
        check(S, f"{pg['name']}: page opened in Power BI", False, "page not visited"); continue
    errs = [t for t in u["texts"] if re.search(r"can't display|cannot display|something's wrong|fix this|couldn't load|could not load|see details|exceeded the available|error", t, re.I)]
    titles = [v["title"] for v in pg["visuals"] if v.get("title")]
    missing_titles = [t for t in titles if not any(t in x for x in u["texts"])]
    cards = [v["measures"][0] for v in pg["visuals"] if v["type"] == "card"]
    want = {m: fmt[mfmt[m]](expected(r)[m]) for m in cards} if pg["name"] != "Employee Details" else {m: fmt[mfmt[m]](expected(r)[m]) for m in cards}
    missing_vals = [f"{m}={val}" for m, val in want.items() if not any(val in x for x in u["texts"])]
    check(S, f"{pg['name']}: opened, no visual error text, all {len(titles)} chart titles and {len(cards)} card values visible",
          u["selected"] and not errs and not missing_titles and not missing_vals,
          f"selected={u['selected']} errors={errs[:3]} missing_titles={missing_titles[:3]} missing_values={missing_vals[:4]}")

passed, total = sum(res), len(res)
text = f"STEP 6 VALIDATION: {passed}/{total} checks passed\n\n" + "\n".join(out)
print(text)
open(REPORT, "w", encoding="utf-8").write(text + "\n")
sys.exit(0 if passed == total else 1)
