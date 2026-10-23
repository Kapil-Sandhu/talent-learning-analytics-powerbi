"""
Step 4 - Generate the Power BI Project (PBIP, TMDL format) for the Talent & Learning Analytics Dashboard.

Builds, as plain text files that Power BI Desktop opens directly:
  03_PowerBI/Talent_Learning_Dashboard.pbip
  03_PowerBI/Talent_Learning_Dashboard.SemanticModel/   (model: queries, tables, relationships, metadata)
  03_PowerBI/Talent_Learning_Dashboard.Report/          (report shell; pages are built in Step 6)

Inputs: the validated Step 3 Power Query files (03_PowerBI/PowerQuery/*.pq) and the Step 3 mirror (column lists).
Run from the project root:  python 03_PowerBI/model/build_pbip.py
"""
import json, os, re, sys, uuid, shutil

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
THEME_SRC = sys.argv[2] if len(sys.argv) > 2 else None        # base theme json (CY24SU10)
PQ = os.path.join(ROOT, "03_PowerBI", "PowerQuery")
OUT = os.path.join(ROOT, "03_PowerBI")
NAME = "Talent_Learning_Dashboard"
SM = os.path.join(OUT, f"{NAME}.SemanticModel")
RP = os.path.join(OUT, f"{NAME}.Report")
NS = uuid.UUID("6f1c2a52-5d1e-4a8e-9a43-7d2b8f0c9e11")          # deterministic lineage tags
tag = lambda *parts: str(uuid.uuid5(NS, "/".join(parts)))
T1, T2, T4 = "\t", "\t\t", "\t\t\t\t"

sys.path.insert(0, os.path.join(ROOT, "03_PowerBI", "validation"))
import mirror_step3 as mirror
mirror.CSV = os.path.join(ROOT, "01_Data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv")
mirror.LKP = os.path.join(ROOT, "01_Data/lookups/HR_Lookups.xlsx")
_, _, MT = mirror.build()

# ----------------------------------------------------------------------------- read Step 3 queries
def read_pq(name):
    f = [x for x in os.listdir(PQ) if re.sub(r"^\d+_", "", x[:-3]) == name and x.endswith(".pq")][0]
    lines = open(os.path.join(PQ, f), encoding="utf-8").read().rstrip().splitlines()
    header = []
    while lines and lines[0].startswith("//"):
        header.append(lines.pop(0)[2:].strip())
    return "\n".join(lines), header

def m_block(m, indent):
    return "\n".join((indent + l) if l.strip() else "" for l in m.splitlines())

def desc(text, indent=""):
    return "".join(f"{indent}/// {l}\n" for l in text.splitlines())

# ----------------------------------------------------------------------------- Step 4 model design
KEYS = {"DepartmentKey", "JobRoleKey", "EducationKey", "JobSatisfactionKey", "AgeBandKey", "TenureBandKey",
        "IncomeBandKey", "TrainingBandKey"}
DIM_SPEC = {
    "DimDepartment": ("One row per department (3).", "DepartmentKey", {}),
    "DimJobRole": ("One row per job role (9).", "JobRoleKey", {}),
    "DimEducation": ("Education level 1-5 (Below College ... Doctor).", "EducationKey", {"EducationLevel": "EducationKey"}),
    "DimJobSatisfaction": ("Job satisfaction scale 1-4 (Low ... Very High) - a key attrition driver.", "JobSatisfactionKey",
                           {"JobSatisfaction": "JobSatisfactionKey"}),
    "DimAgeBand": ("Age bands (inclusive Min/Max from HR_Lookups.xlsx).", "AgeBandKey", {"AgeBand": "AgeBandKey"}),
    "DimTenureBand": ("Tenure bands on YearsAtCompany (inclusive Min/Max).", "TenureBandKey", {"TenureBand": "TenureBandKey"}),
    "DimIncomeBand": ("Monthly income bands (currency not stated in the source data).", "IncomeBandKey", {"IncomeBand": "IncomeBandKey"}),
    "DimTrainingBand": ("Training bands on TrainingTimesLastYear (0-6).", "TrainingBandKey", {"TrainingBand": "TrainingBandKey"}),
    "DimEmployee": ("One row per employee: descriptive attributes for slicers and the drill-through page.", "EmployeeID",
                    {c: c + "Sort" for c in ["BusinessTravel", "EnvironmentSatisfaction", "RelationshipSatisfaction",
                                              "JobInvolvement", "WorkLifeBalance", "PerformanceRating"]}),
}
FACT_DESC = "Fact table. Grain: one row per employee (point-in-time snapshot). Foreign keys + numeric columns for DAX measures."
COL_DESC = {
    "EmployeeID": "Unique employee identifier (EmployeeNumber in the source).",
    "AttritionFlag": "1 = employee left, 0 = still employed.",
    "OverTimeFlag": "1 = works overtime, 0 = no overtime.",
    "EmployeeStatus": "Left / Active.",
    "TrainingTimesLastYear": "Number of trainings attended last year (0-6) - the learning metric.",
    "YearsAtCompany": "Tenure at the company in years.",
    "MonthlyIncome": "Monthly income (currency not stated in the source data).",
    "JobSatisfactionScore": "Job satisfaction 1-4, for averages.",
}
SUM_COLS = {"AttritionFlag", "OverTimeFlag", "TrainingTimesLastYear", "MonthlyIncome"}
NONE_COLS = KEYS | {"EmployeeID", "JobLevel", "StockOptionLevel", "MinAge", "MaxAge", "MinYears", "MaxYears",
                    "MinIncome", "MaxIncome", "MinTrainings", "MaxTrainings"} | {c for c in MT["DimEmployee"].columns if c.endswith("Sort")}

def column_meta(table, col, dtype):
    """Returns dict of TMDL column properties for Step 4."""
    p = {"dataType": "int64" if dtype == "Int64" else ("double" if dtype == "double" else "string")}
    is_dim = table in DIM_SPEC
    sort_map = DIM_SPEC[table][2] if is_dim else {}
    hidden = (col in KEYS) or col.endswith("Sort") or (table == "FactEmployee" and col == "EmployeeID") \
        or (is_dim and col == DIM_SPEC[table][1] and table != "DimEmployee") \
        or col.startswith(("Min", "Max")) and table.endswith("Band")
    p["isHidden"] = hidden
    p["isKey"] = is_dim and col == DIM_SPEC[table][1]
    if p["dataType"] == "int64":
        p["formatString"] = "#,##0" if col == "MonthlyIncome" else "0"
    if p["dataType"] == "string":
        p["summarizeBy"] = "none"
    elif col in NONE_COLS:
        p["summarizeBy"] = "none"
    elif col in SUM_COLS:
        p["summarizeBy"] = "sum"
    else:
        p["summarizeBy"] = "average"
    if col in sort_map:
        p["sortByColumn"] = sort_map[col]
    p["description"] = COL_DESC.get(col)
    return p

def column_tmdl(table, col, p):
    s = desc(p["description"], T1) if p.get("description") else ""
    s += f"{T1}column {col}\n{T2}dataType: {p['dataType']}\n"
    if p["isHidden"]:
        s += f"{T2}isHidden\n"
    if p["isKey"]:
        s += f"{T2}isKey\n"
    if "formatString" in p:
        s += f"{T2}formatString: {p['formatString']}\n"
    s += f"{T2}lineageTag: {tag(table, col)}\n{T2}summarizeBy: {p['summarizeBy']}\n{T2}sourceColumn: {col}\n"
    if "sortByColumn" in p:
        s += f"{T2}sortByColumn: {p['sortByColumn']}\n"
    s += f"\n{T2}annotation SummarizationSetBy = User\n\n"
    return s

def table_tmdl(table, description, columns, m_source, hidden=False):
    s = desc(description) + f"table {table}\n"
    if hidden:
        s += f"{T1}isHidden\n"
    s += f"{T1}lineageTag: {tag(table)}\n\n"
    for col, p in columns:
        s += column_tmdl(table, col, p)
    s += f"{T1}partition {table} = m\n{T2}mode: import\n{T2}source =\n{m_block(m_source, T4)}\n\n"
    s += f"{T1}annotation PBI_ResultType = Table\n"
    return s

SPEC = {}            # machine-readable model spec (used by the validator)
os.makedirs(os.path.join(SM, "definition", "tables"), exist_ok=True)
tables_dir = os.path.join(SM, "definition", "tables")
for f in os.listdir(tables_dir):
    os.remove(os.path.join(tables_dir, f))

load_order = list(DIM_SPEC) + ["FactEmployee", "QA_Checks", "_Measures"]
for t in list(DIM_SPEC) + ["FactEmployee"]:
    m, _ = read_pq(t)
    dtypes = {c: ("Int64" if str(MT[t][c].dtype).startswith("int") else "text") for c in MT[t].columns}
    cols = [(c, column_meta(t, c, dtypes[c])) for c in MT[t].columns]
    d = DIM_SPEC[t][0] if t in DIM_SPEC else FACT_DESC
    open(os.path.join(tables_dir, f"{t}.tmdl"), "w", encoding="utf-8").write(table_tmdl(t, d, cols, m))
    SPEC[t] = {"hidden": False, "columns": {c: {k: v for k, v in p.items() if k != "description"} for c, p in cols}}

m, _ = read_pq("QA_Checks")
qa_cols = [("CheckNo", {"dataType": "int64", "isHidden": False, "isKey": False, "formatString": "0", "summarizeBy": "none"}),
           ("Check", {"dataType": "string", "isHidden": False, "isKey": False, "summarizeBy": "none"}),
           ("Actual", {"dataType": "double", "isHidden": False, "isKey": False, "summarizeBy": "none"}),
           ("Expected", {"dataType": "double", "isHidden": False, "isKey": False, "summarizeBy": "none"}),
           ("Result", {"dataType": "string", "isHidden": False, "isKey": False, "summarizeBy": "none"})]
open(os.path.join(tables_dir, "QA_Checks.tmdl"), "w", encoding="utf-8").write(
    table_tmdl("QA_Checks", "35 automatic data-quality checks, recalculated on every refresh. All must be PASS. Hidden from report view.",
               qa_cols, m, hidden=True))
SPEC["QA_Checks"] = {"hidden": True, "columns": {c: p for c, p in qa_cols}}

mm = '#table(type table [Placeholder = text], {})'
open(os.path.join(tables_dir, "_Measures.tmdl"), "w", encoding="utf-8").write(
    table_tmdl("_Measures", "Home table for all DAX measures (added in Step 5). The placeholder column is hidden.",
               [("Placeholder", {"dataType": "string", "isHidden": True, "isKey": False, "summarizeBy": "none"})], mm))
SPEC["_Measures"] = {"hidden": False, "columns": {"Placeholder": {"dataType": "string", "isHidden": True, "isKey": False, "summarizeBy": "none"}}}

# ----------------------------------------------------------------------------- expressions (not loaded)
EXPR_ORDER = ["ProjectFolder", "fnGetLookup", "fnBandKey", "src_HR", "lkp_Education", "lkp_Satisfaction",
              "lkp_WorkLifeBalance", "lkp_PerformanceRating", "lkp_BusinessTravel", "lkp_AgeBand", "lkp_TenureBand",
              "lkp_IncomeBand", "lkp_TrainingBand", "stg_HR"]
ex = ""
for e in EXPR_ORDER:
    m, header = read_pq(e)
    d = " ".join(h for h in header[1:] if h)
    rtype = "Text" if e == "ProjectFolder" else ("Function" if e.startswith("fn") else "Table")
    ex += desc(d) if d else ""
    if e == "ProjectFolder":
        ex += f"expression {e} = {m.strip()}\n"
    else:
        ex += f"expression {e} =\n{m_block(m, T2)}\n"
    ex += f"{T1}lineageTag: {tag('expr', e)}\n\n{T1}annotation PBI_ResultType = {rtype}\n\n"
open(os.path.join(SM, "definition", "expressions.tmdl"), "w", encoding="utf-8").write(ex)

# ----------------------------------------------------------------------------- relationships
REL = [("DepartmentKey", "DimDepartment"), ("JobRoleKey", "DimJobRole"), ("EducationKey", "DimEducation"),
       ("JobSatisfactionKey", "DimJobSatisfaction"), ("AgeBandKey", "DimAgeBand"), ("TenureBandKey", "DimTenureBand"),
       ("IncomeBandKey", "DimIncomeBand"), ("TrainingBandKey", "DimTrainingBand"), ("EmployeeID", "DimEmployee")]
rel = ""
for k, dim in REL:
    rel += f"relationship {tag('rel', k)}\n{T1}fromColumn: FactEmployee.{k}\n{T1}toColumn: {dim}.{k}\n\n"
open(os.path.join(SM, "definition", "relationships.tmdl"), "w", encoding="utf-8").write(rel)
SPEC["_relationships"] = [{"from": f"FactEmployee.{k}", "to": f"{d}.{k}", "fromCardinality": "many", "toCardinality": "one",
                           "crossFilter": "oneDirection", "active": True} for k, d in REL]

# ----------------------------------------------------------------------------- model / database / culture
query_order = EXPR_ORDER + load_order
model = (f"model Model\n{T1}culture: en-US\n{T1}defaultPowerBIDataSourceVersion: powerBI_V3\n{T1}sourceQueryCulture: en-US\n"
         f"{T1}dataAccessOptions\n{T2}legacyRedirects\n{T2}returnErrorValuesAsNull\n\n"
         f"annotation __PBI_TimeIntelligenceEnabled = 0\n\n"
         f"annotation PBI_QueryOrder = {json.dumps(query_order, separators=(',', ':'))}\n\n"
         + "".join(f"ref table {t}\n" for t in load_order) + "\nref cultureInfo en-US\n")
open(os.path.join(SM, "definition", "model.tmdl"), "w", encoding="utf-8").write(model)
open(os.path.join(SM, "definition", "database.tmdl"), "w", encoding="utf-8").write("database\n\tcompatibilityLevel: 1601\n")
os.makedirs(os.path.join(SM, "definition", "cultures"), exist_ok=True)
open(os.path.join(SM, "definition", "cultures", "en-US.tmdl"), "w", encoding="utf-8").write("cultureInfo en-US\n")

def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(json.dumps(obj, indent=2) + "\n")

wjson(os.path.join(SM, "definition.pbism"), {"version": "4.0", "settings": {}})
wjson(os.path.join(SM, ".platform"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": NAME}, "config": {"version": "2.0", "logicalId": tag("sm")}})
wjson(os.path.join(SM, ".pbi", "editorSettings.json"), {
    "version": "1.0", "showHiddenFields": True, "parallelQueryLoading": True,
    "relationshipImportEnabled": False, "shouldNotifyUserOfNameConflictResolution": True})

# ----------------------------------------------------------------------------- report shell (PBIR)
page_id = tag("page", "overview").replace("-", "")[:20]
wjson(os.path.join(RP, "definition.pbir"), {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
wjson(os.path.join(RP, ".platform"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": NAME}, "config": {"version": "2.0", "logicalId": tag("report")}})
wjson(os.path.join(RP, "definition", "version.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0"})
wjson(os.path.join(RP, "definition", "report.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.3.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.61", "type": "SharedResources"}},
    "layoutOptimization": "None",          # REQUIRED by the report schema (None = no mobile layout)
    "resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                          "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                 "defaultFilterActionIsDataFilter": True, "defaultDrillFilterOtherVisuals": True,
                 "allowChangeFilterTypes": True, "useEnhancedTooltips": True}})
wjson(os.path.join(RP, "definition", "pages", "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [page_id], "activePageName": page_id})
wjson(os.path.join(RP, "definition", "pages", page_id, "page.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.4.0/schema.json",
    "name": page_id, "displayName": "Overview", "displayOption": "FitToPage", "height": 720, "width": 1280})
if THEME_SRC:
    dst = os.path.join(RP, "StaticResources", "SharedResources", "BaseThemes", "CY24SU10.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(THEME_SRC, dst)

wjson(os.path.join(OUT, f"{NAME}.pbip"), {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                           "settings": {"enableAutoRecovery": True}})
open(os.path.join(OUT, ".gitignore"), "w").write("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
wjson(os.path.join(OUT, "model", "model_spec.json"), SPEC)
print("PBIP written:", OUT)
