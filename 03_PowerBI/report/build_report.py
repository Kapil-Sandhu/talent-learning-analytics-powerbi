"""
Step 6 - generate the report pages (PBIR format) for the Talent & Learning Analytics Dashboard.

Writes 03_PowerBI/Talent_Learning_Dashboard.Report/definition/pages/** (6 pages, ~50 visuals).
Run with Power BI Desktop CLOSED:  python 03_PowerBI/report/build_report.py [project_root]

Only visual types and JSON structures that Power BI Desktop itself writes are used
(card, clusteredBarChart, columnChart, slicer, pivotTable, tableEx, textbox); every file is
validated against Microsoft's official JSON schemas by validate_step6.py.
Also writes 03_PowerBI/report/report_spec.json (what every visual shows) for the validator.
"""
import json, os, sys, uuid

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
RP = os.path.join(ROOT, "03_PowerBI", "Talent_Learning_Dashboard.Report", "definition")
NS = uuid.UUID("6f1c2a52-5d1e-4a8e-9a43-7d2b8f0c9e11")
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json"
PG = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.4.0/schema.json"
PM = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
W, H, M, GAP = 1280, 720, 16, 12
MT = "_Measures"
OVERVIEW_ID = "752e97a8ae9256f78cc6"          # existing page folder (kept, so nothing has to be deleted)

def vid(*parts):
    return uuid.uuid5(NS, "/".join(parts)).hex[:20]

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}
def s(text):
    return lit("'" + text.replace("'", "''") + "'")

def col(e, p):
    return {"Column": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}
def mea(p, e=MT):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": e}}, "Property": p}}

AGG = {"Sum": 0, "Avg": 1}          # Power BI QueryAggregateFunction codes (Sum = 0, Avg = 1, Min = 3 as in Desktop files)
def agg(e, p, func):
    return {"Aggregation": {"Expression": col(e, p), "Function": AGG[func]}}

# friendly names shown on axes / slicer headers / table headers instead of the technical column names
DISPLAY = {"Department": "Department", "TenureBand": "Tenure", "JobRole": "Job role", "OverTime": "Overtime",
           "AgeBand": "Age band", "JobLevel": "Job level", "StockOptionLevel": "Stock option level",
           "MaritalStatus": "Marital status", "BusinessTravel": "Business travel", "IncomeBand": "Monthly income",
           "TrainingBand": "Training band", "JobSatisfaction": "Job satisfaction", "WorkLifeBalance": "Work-life balance",
           "EnvironmentSatisfaction": "Environment satisfaction", "PerformanceRating": "Performance rating"}

def proj(field, display=None, active=None):
    if "Aggregation" in field:
        inner = field["Aggregation"]["Expression"]["Column"]
        e = inner["Expression"]["SourceRef"]["Entity"]; p = inner["Property"]
        fn = {v: k for k, v in AGG.items()}[field["Aggregation"]["Function"]]
        d = {"field": field, "queryRef": f"{fn}({e}.{p})"}
    else:
        kind = "Measure" if "Measure" in field else "Column"
        e = field[kind]["Expression"]["SourceRef"]["Entity"]; p = field[kind]["Property"]
        d = {"field": field, "queryRef": f"{e}.{p}", "nativeQueryRef": p}
        if display is None and kind == "Column":
            display = DISPLAY.get(p)
    if display: d["displayName"] = display
    if active is not None: d["active"] = active
    return d

SPEC = {"pages": []}

class Page:
    def __init__(self, pid, name, title, subtitle):
        self.pid, self.name, self.visuals, self.z = pid, name, [], 1000
        self.textbox("title", M, 6, 900, 68, [(title, "18pt", True, "#1F3864"), (subtitle, "9pt", False, "#595959")])

    def _container(self, key, x, y, w, h, visual, name=None):
        self.z += 1000
        v = {"$schema": VC, "name": name or vid(self.pid, key),
             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
             "visual": visual}
        self.visuals.append(v)
        return v

    def textbox(self, key, x, y, w, h, lines):
        paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": size, "color": color,
                                                            **({"fontWeight": "bold"} if bold else {})}}]}
                 for t, size, bold, color in lines]
        self._container(key, x, y, w, h, {"visualType": "textbox",
                                            "objects": {"general": [{"properties": {"paragraphs": paras}}]},
                                            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, "textbox", x, y, w, h, text=[l[0] for l in lines])

    def back_button(self, key, x, y, w, h, name):
        self._container(key, x, y, w, h, {
            "visualType": "actionButton",
            "objects": {"icon": [{"properties": {"shapeType": s("back")}, "selector": {"id": "default"}}]},
            "visualContainerObjects": {"visualLink": [{"properties": {"show": lit("true"), "type": s("Back")}}]},
            "drillFilterOtherVisuals": True}, name=name)
        SPEC_V(self, key, "actionButton", x, y, w, h, name_override=name)

    def card(self, key, x, y, w, h, measure):
        self._container(key, x, y, w, h, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proj(mea(measure))]}}},
            "objects": {"labels": [{"properties": {"fontSize": lit("22D"), "labelDisplayUnits": lit("1D")}}],
                        "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("10D")}}]},
            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, "card", x, y, w, h, measures=[measure])

    def slicer(self, key, x, y, w, h, entity, prop):
        self._container(key, x, y, w, h, {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [proj(col(entity, prop), active=True)]}}},
            "objects": {"data": [{"properties": {"mode": s("Dropdown")}}]},
            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, "slicer", x, y, w, h, columns=[f"{entity}.{prop}"])

    def chart(self, key, x, y, w, h, vtype, entity, prop, measure, title, sort="category"):
        cat, m = col(entity, prop), mea(measure)
        sort_def = ({"sort": [{"field": m, "direction": "Descending"}]} if sort == "measure"
                    else {"sort": [{"field": cat, "direction": "Ascending"}]})
        self._container(key, x, y, w, h, {
            "visualType": vtype,
            "query": {"queryState": {"Category": {"projections": [proj(cat, active=True)]},
                                     "Y": {"projections": [proj(m)]}},
                      "sortDefinition": sort_def},
            "objects": {"labels": [{"properties": {"show": lit("true")}}],
                        # chart titles already say what is shown, so the axis titles are hidden; bar charts get
                        # more room for long category names (job roles) so they are not cut off
                        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"),
                                                         **({"maxMarginFactor": lit("45L")} if vtype == "clusteredBarChart" else {})}}],
                        "valueAxis": [{"properties": {"showAxisTitle": lit("false")}}]},
            "visualContainerObjects": {"title": [{"properties": {"show": lit("true"), "text": s(title)}}]},
            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, vtype, x, y, w, h, columns=[f"{entity}.{prop}"], measures=[measure], title=title, sort=sort)

    def matrix(self, key, x, y, w, h, entity, prop, measures, title, sort_by):
        assert sort_by in measures
        font = lambda n: [{"properties": {"fontSize": lit(n)}}]
        self._container(key, x, y, w, h, {
            "visualType": "pivotTable",
            "query": {"queryState": {"Rows": {"projections": [proj(col(entity, prop), active=True)]},
                                     "Values": {"projections": [proj(mea(m)) for m in measures]}},
                      "sortDefinition": {"sort": [{"field": mea(sort_by), "direction": "Descending"}]}},
            "objects": {"values": font("11D"), "columnHeaders": font("11D"), "rowHeaders": font("11D")},
            "visualContainerObjects": {"title": [{"properties": {"show": lit("true"), "text": s(title)}}]},
            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, "pivotTable", x, y, w, h, columns=[f"{entity}.{prop}"], measures=measures, title=title, sort_by=sort_by)

    def table(self, key, x, y, w, h, fields, title, totals=True):
        """fields: (kind, entity, prop, display[, func]) with kind col | mea | agg (column with Sum/Avg aggregation)."""
        def field(f):
            kind, e, p = f[0], f[1], f[2]
            return col(e, p) if kind == "col" else (mea(p) if kind == "mea" else agg(e, p, f[4]))
        projs = [proj(field(f), display=f[3]) for f in fields]
        objects = {} if totals else {"total": [{"properties": {"totals": lit("false")}}]}
        self._container(key, x, y, w, h, {
            "visualType": "tableEx",
            "query": {"queryState": {"Values": {"projections": projs}}},
            **({"objects": objects} if objects else {}),
            "visualContainerObjects": {"title": [{"properties": {"show": lit("true"), "text": s(title)}}]},
            "drillFilterOtherVisuals": True})
        SPEC_V(self, key, "tableEx", x, y, w, h, columns=[f"{f[1]}.{f[2]}" for f in fields if f[0] == "col"],
               measures=[f[2] for f in fields if f[0] == "mea"],
               aggs=[{"col": f"{f[1]}.{f[2]}", "func": f[4], "alias": f"{f[4]}({f[1]}.{f[2]})"} for f in fields if f[0] == "agg"],
               title=title)

def SPEC_V(page, key, vtype, x, y, w, h, **kw):
    page_spec = next(p for p in SPEC["pages"] if p["id"] == page.pid) if any(p["id"] == page.pid for p in SPEC["pages"]) else None
    if page_spec is None:
        page_spec = {"id": page.pid, "name": page.name, "visuals": []}; SPEC["pages"].append(page_spec)
    name = kw.pop("name_override", None) or vid(page.pid, key)
    page_spec["visuals"].append({"key": key, "name": name, "type": vtype, "x": x, "y": y, "w": w, "h": h, **kw})

# ----------------------------------------------------------------------------- layout helpers
def row(n, y, h):
    w = (W - 2 * M - (n - 1) * GAP) / n
    return [(round(M + i * (w + GAP), 2), y, round(w, 2), h) for i in range(n)]
CARD_Y, CARD_H = 80, 92
R1_Y, R2_Y, CH_H = 184, 452, 256            # chart rows: 184-440 and 452-708
def slicers(page):
    page.slicer("slicer_dept", 948, 12, 150, 56, "DimDepartment", "Department")
    page.slicer("slicer_role", 1110, 12, 154, 56, "DimJobRole", "JobRole")

pages = []
# ----------------------------------------------------------------------------- 1 Overview
p = Page(OVERVIEW_ID, "Overview", "Talent & Learning Analytics - Overview",
         "1,470 employees (IBM HR sample data, fictional) - point-in-time snapshot. Use the slicers to filter; right-click a job role to drill through.")
slicers(p)
for (x, y, w, h), m in zip(row(6, CARD_Y, CARD_H), ["Headcount", "Leavers", "Attrition Rate", "Avg Tenure (Years)",
                                                   "Training per Employee", "Overtime %"]):
    p.card("card_" + m, x, y, w, h, m)
(l, m1, r1) = row(3, R1_Y, CH_H); (_, m2, r2) = row(3, R2_Y, CH_H)
TALL = R2_Y + CH_H - R1_Y                    # full chart-area height (184-708)
p.chart("role", l[0], R1_Y, l[2], TALL, "clusteredBarChart", "DimJobRole", "JobRole", "Attrition Rate", "Attrition rate by job role", sort="measure")
p.chart("dept", *m1, "clusteredBarChart", "DimDepartment", "Department", "Attrition Rate", "Attrition rate by department", sort="measure")
p.chart("overtime", *m2, "columnChart", "DimEmployee", "OverTime", "Attrition Rate", "Attrition rate: overtime vs no overtime")
p.chart("tenure", *r1, "columnChart", "DimTenureBand", "TenureBand", "Attrition Rate", "Attrition rate by tenure (years at company)")
p.chart("trainingband", *r2, "columnChart", "DimTrainingBand", "TrainingBand", "Attrition Rate", "Attrition rate by trainings last year")
pages.append(p)

# ----------------------------------------------------------------------------- 2 Insights & Actions (Step 7; text from 04_Docs/insights_page.json)
INS = os.path.join(ROOT, "04_Docs", "insights_page.json")
if os.path.isfile(INS):
    ins = json.load(open(INS, encoding="utf-8"))
    p = Page(vid("page", "insights"), "Insights & Actions", "Insights & Actions",
             "Four evidence-based actions for HR and L&D. Cards are live; details in 04_Docs/Insights_and_Recommendations.md.")
    for (x, y, w, h), m in zip(row(4, CARD_Y, CARD_H), ins["cards"]):
        p.card("card_" + m, x, y, w, h, m)
    boxes = row(2, R1_Y, 236) + row(2, 432, 236)
    for i, ((x, y, w, h), panel) in enumerate(zip(boxes, ins["panels"])):
        lines = [(panel["title"], "13pt", True, "#1F3864")] + [(t, "11pt", False, "#262626") for t in panel["lines"]]
        p.textbox(f"panel{i + 1}", x, y, w, h, lines)
        p_spec = next(x2 for x2 in SPEC["pages"] if x2["id"] == p.pid)
        p_spec["visuals"][-1]["title"] = panel["title"]
    p.textbox("footnote", M, 680, W - 2 * M, 34, [(ins["footnote"], "9pt", False, "#595959")])
    pages.append(p)

# ----------------------------------------------------------------------------- 3 Attrition Drivers
p = Page(vid("page", "drivers"), "Attrition Drivers", "Attrition Drivers",
         "Which groups leave most? Compare each bar with the company rate of 16.1%.")
slicers(p)
for (x, y, w, h), m in zip(row(5, CARD_Y, CARD_H), ["Attrition Rate - Overtime", "Attrition Rate - No Overtime",
                                                   "Overtime Attrition Ratio", "Early Tenure Attrition Rate (0-1 yrs)",
                                                   "Attrition Rate - Low Job Satisfaction"]):
    p.card("card_" + m, x, y, w, h, m)
t1, t2, t3 = row(3, R1_Y, CH_H); b1, b2, b3 = row(3, R2_Y, CH_H)
p.chart("age", *t1, "columnChart", "DimAgeBand", "AgeBand", "Attrition Rate", "Attrition rate by age band")
p.chart("joblevel", *t2, "columnChart", "DimEmployee", "JobLevel", "Attrition Rate", "Attrition rate by job level (1 = junior)")
p.chart("stock", *t3, "columnChart", "DimEmployee", "StockOptionLevel", "Attrition Rate", "Attrition rate by stock option level")
p.chart("marital", *b1, "clusteredBarChart", "DimEmployee", "MaritalStatus", "Attrition Rate", "Attrition rate by marital status", sort="measure")
p.chart("travel", *b2, "columnChart", "DimEmployee", "BusinessTravel", "Attrition Rate", "Attrition rate by business travel")
p.chart("income", *b3, "clusteredBarChart", "DimIncomeBand", "IncomeBand", "Attrition Rate", "Attrition rate by monthly income band")
pages.append(p)

# ----------------------------------------------------------------------------- 3 Training & Learning
p = Page(vid("page", "training"), "Training & Learning", "Training & Learning",
         "Trainings attended last year (0-6). Note: only 54 employees had no training - treat that group as indicative.")
slicers(p)
for (x, y, w, h), m in zip(row(5, CARD_Y, CARD_H), ["Total Trainings", "Training per Employee", "Employees with No Training",
                                                   "% No Training", "% High Training (5-6)"]):
    p.card("card_" + m, x, y, w, h, m)
(l, m1, r1) = row(3, R1_Y, CH_H); (_, m2, r2) = row(3, R2_Y, CH_H)
p.chart("role_tpe", l[0], R1_Y, l[2], TALL, "clusteredBarChart", "DimJobRole", "JobRole", "Training per Employee", "Trainings per employee by job role", sort="measure")
p.chart("band_hc", *m1, "columnChart", "DimTrainingBand", "TrainingBand", "Headcount", "Employees by training band")
p.chart("band_rate", *m2, "columnChart", "DimTrainingBand", "TrainingBand", "Attrition Rate", "Attrition rate by training band")
p.chart("dept_tpe", *r1, "clusteredBarChart", "DimDepartment", "Department", "Training per Employee", "Trainings per employee by department", sort="measure")
p.chart("tenure_tpe", *r2, "columnChart", "DimTenureBand", "TenureBand", "Training per Employee", "Trainings per employee by tenure")
pages.append(p)

# ----------------------------------------------------------------------------- 4 Satisfaction & Performance
p = Page(vid("page", "satisfaction"), "Satisfaction & Performance", "Satisfaction & Performance",
         "Ratings 1-4. Low job satisfaction and bad work-life balance go with higher attrition; performance rating does not.")
slicers(p)
for (x, y, w, h), m in zip(row(5, CARD_Y, CARD_H), ["Avg Job Satisfaction", "% Low Job Satisfaction",
                                                   "Attrition Rate - Low Job Satisfaction", "Avg Work-Life Balance",
                                                   "Avg Performance Rating"]):
    p.card("card_" + m, x, y, w, h, m)
(a, b) = row(2, R1_Y, CH_H); (c, d) = row(2, R2_Y, CH_H)
p.chart("jobsat", *a, "columnChart", "DimJobSatisfaction", "JobSatisfaction", "Attrition Rate", "Attrition rate by job satisfaction")
p.chart("wlb", *b, "columnChart", "DimEmployee", "WorkLifeBalance", "Attrition Rate", "Attrition rate by work-life balance")
p.chart("env", *c, "columnChart", "DimEmployee", "EnvironmentSatisfaction", "Attrition Rate", "Attrition rate by environment satisfaction")
p.chart("perf", *d, "columnChart", "DimEmployee", "PerformanceRating", "Attrition Rate", "Attrition rate by performance rating")
pages.append(p)

# ----------------------------------------------------------------------------- 5 Job Role Summary (matrix) + 6 Employee Details (drill-through)
p = Page(vid("page", "roles"), "Job Role Summary", "Job Role Summary",
         "All key measures per job role. Right-click a job role and choose Drill through > Employee Details to see its employees.")
slicers(p)
p.matrix("matrix_roles", M, 80, W - 2 * M, 316, "DimJobRole", "JobRole",
         ["Headcount", "Leavers", "Attrition Rate", "Attrition vs Company (pts)", "Avg Tenure (Years)",
          "Training per Employee", "% No Training", "Overtime %", "Avg Job Satisfaction"],
         "Key measures by job role (sorted by attrition gap vs company)", sort_by="Attrition vs Company (pts)")
p.chart("gap", M, 408, W - 2 * M, 300, "clusteredBarChart", "DimJobRole", "JobRole", "Attrition vs Company (pts)",
        "Attrition gap vs company rate, in percentage points (positive = more leavers than average)", sort="measure")
pages.append(p)

DT_FILTER = "Filter" + vid("filter", "drill_jobrole")
BACK_BUTTON_ID = "ee71184a4e862a767556"     # folder name Power BI Desktop gave its back button on this page
p = Page(vid("page", "employees"), "Employee Details", "Employee Details",
         "Drill-through page: right-click a job role on any page > Drill through > Employee Details. Opened directly it shows all employees.")
for (x, y, w, h), m in zip(row(4, CARD_Y, CARD_H), ["Headcount", "Leavers", "Attrition Rate", "Training per Employee"]):
    p.card("card_" + m, x, y, w, h, m)
p.table("employees", M, R1_Y, W - 2 * M, 524, [
    ("col", "DimEmployee", "EmployeeID", "Employee ID"), ("col", "DimEmployee", "EmployeeStatus", "Status"),
    ("col", "DimDepartment", "Department", "Department"), ("col", "DimJobRole", "JobRole", "Job role"),
    ("col", "DimEmployee", "Gender", "Gender"), ("col", "DimEmployee", "OverTime", "Overtime"),
    # one row per employee, so Sum = the employee's own value (shown as a whole number); totals row is off
    ("agg", "FactEmployee", "Age", "Age", "Sum"), ("agg", "FactEmployee", "YearsAtCompany", "Tenure (years)", "Sum"),
    ("agg", "FactEmployee", "TrainingTimesLastYear", "Trainings last year", "Sum"),
    ("agg", "FactEmployee", "JobSatisfactionScore", "Job satisfaction (1-4)", "Sum"),
    ("agg", "FactEmployee", "MonthlyIncome", "Monthly income", "Sum")], "Employees in the current selection", totals=False)
p.back_button("back", 1164, 16, 100, 40, BACK_BUTTON_ID)
p.drill = {"filter": DT_FILTER, "entity": "DimJobRole", "prop": "JobRole"}
pages.append(p)

# ----------------------------------------------------------------------------- 7 Data Quality
p = Page(vid("page", "quality"), "Data Quality", "Data Quality (self-testing model)",
         "35 automatic checks recalculated on every refresh: row counts, duplicates, nulls, orphan keys and control totals. All must be PASS.")
p.table("qa", M, 80, W - 2 * M, 628, [("col", "QA_Checks", c, d) for c, d in [("CheckNo", "#"), ("Check", "Check"), ("Actual", "Actual"),
                                                                              ("Expected", "Expected"), ("Result", "Result")]],
        "QA_Checks - recalculated on every refresh", totals=False)
pages.append(p)

# ----------------------------------------------------------------------------- write files
def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(json.dumps(obj, indent=2) + "\n")

for pg in pages:
    base = os.path.join(RP, "pages", pg.pid)
    page = {"$schema": PG, "name": pg.pid, "displayName": pg.name, "displayOption": "FitToPage", "height": H, "width": W}
    if getattr(pg, "drill", None):
        d = pg.drill
        # structure copied from a drill-through field added in Power BI Desktop (howCreated = "Drillthrough")
        page["filterConfig"] = {"filters": [{"name": d["filter"], "field": col(d["entity"], d["prop"]),
                                             "type": "Categorical", "howCreated": "Drillthrough"}]}
        page["pageBinding"] = {"name": vid("binding", pg.pid), "type": "Drillthrough",
                               "parameters": [{"name": "Param_" + d["filter"], "boundFilter": d["filter"],
                                               "asAggregation": False, "qnaSingleSelectRequired": False,
                                               "fieldExpr": col(d["entity"], d["prop"])}]}
        next(x for x in SPEC["pages"] if x["id"] == pg.pid)["drillthrough"] = f"{d['entity']}.{d['prop']}"
    wjson(os.path.join(base, "page.json"), page)
    vdir = os.path.join(base, "visuals")
    os.makedirs(vdir, exist_ok=True)
    for v in pg.visuals:
        wjson(os.path.join(vdir, v["name"], "visual.json"), v)

wjson(os.path.join(RP, "pages", "pages.json"), {"$schema": PM, "pageOrder": [p.pid for p in pages], "activePageName": OVERVIEW_ID})
os.makedirs(os.path.join(ROOT, "03_PowerBI", "report"), exist_ok=True)
wjson(os.path.join(ROOT, "03_PowerBI", "report", "report_spec.json"), SPEC)
print(f"{len(pages)} pages, {sum(len(p.visuals) for p in pages)} visuals written to {RP}")
