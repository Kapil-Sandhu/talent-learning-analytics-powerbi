"""
Step 4 - validate every report / project JSON file against Microsoft's OFFICIAL JSON schemas
(github.com/microsoft/json-schemas). This is the check that catches errors like
"Required property 'layoutOptimization' was not included in report.json" BEFORE Power BI opens the file.
Run from the project root:  python 03_PowerBI/validation/check_report_schemas.py
Writes 03_PowerBI/validation/step4_schema_results.json
"""
import glob, json, os, sys, urllib.request
from jsonschema import Draft7Validator

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PB = os.path.join(ROOT, "03_PowerBI")
CACHE = os.path.join(PB, "validation", "schemas")
BASE = "https://raw.githubusercontent.com/microsoft/json-schemas/main/fabric/"
os.makedirs(CACHE, exist_ok=True)

def schema(rel):
    f = os.path.join(CACHE, rel.replace("/", "_") + ".json")
    if not os.path.isfile(f):
        urllib.request.urlretrieve(BASE + rel + "/schema.json", f)
    return json.load(open(f, encoding="utf-8"))

R = "Talent_Learning_Dashboard.Report"
M = "Talent_Learning_Dashboard.SemanticModel"
pairs = [(f"{R}/definition/report.json", "item/report/definition/report/1.3.0", False),
         (f"{R}/definition/pages/pages.json", "item/report/definition/pagesMetadata/1.0.0", False),
         (f"{R}/definition/version.json", "item/report/definition/versionMetadata/1.0.0", False),
         (f"{R}/.platform", "gitIntegration/platformProperties/2.0.0", False),
         (f"{M}/.platform", "gitIntegration/platformProperties/2.0.0", False),
         (f"{R}/definition.pbir", "item/report/definitionProperties/2.0.0", True),
         (f"{M}/definition.pbism", "item/semanticModel/definitionProperties/1.0.0", True)]
pairs += [(os.path.relpath(p, PB).replace("\\", "/"), "item/report/definition/page/1.4.0", False)
          for p in sorted(glob.glob(os.path.join(PB, R, "definition", "pages", "*", "page.json")))]
results = []
for f, rel, schema_optional in pairs:
    sch = schema(rel)
    if schema_optional:      # Power BI Desktop itself writes .pbir/.pbism without a "$schema" property
        sch = dict(sch, required=[r for r in sch.get("required", []) if r != "$schema"])
    doc = json.load(open(os.path.join(PB, f), encoding="utf-8-sig"))
    errs = [e.message for e in Draft7Validator(sch).iter_errors(doc)]
    results.append({"file": f, "schema": rel, "ok": not errs, "errors": errs})
    print(("OK   " if not errs else "FAIL ") + f + ("" if not errs else "  -> " + " | ".join(errs)))
json.dump(results, open(os.path.join(PB, "validation", "step4_schema_results.json"), "w"), indent=2)
print("files:", len(results), "schema errors:", sum(len(r["errors"]) for r in results))
