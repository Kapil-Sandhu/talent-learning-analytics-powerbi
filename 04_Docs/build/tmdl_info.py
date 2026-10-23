"""
Read the Power BI model straight from its TMDL files (the saved project), so the README, user guide, deck and
star-schema diagram describe the model as it actually is - not as someone remembers it.
Used by make_diagram.py, build_docs.py and validate_step8.py.
"""
import glob, os, re

def _lines(path):
    return open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")

def _unquote(name):
    name = name.strip()
    return name[1:-1].replace("''", "'") if name.startswith("'") and name.endswith("'") else name

def read_model(root):
    d = os.path.join(root, "03_PowerBI", "Talent_Learning_Dashboard.SemanticModel", "definition")
    tables = {}
    for f in sorted(glob.glob(os.path.join(d, "tables", "*.tmdl"))):
        L = _lines(f)
        t = {"description": "", "hidden": False, "columns": [], "measures": []}
        name, doc, cur = None, [], None
        i = 0
        while i < len(L):
            line = L[i]
            s = line.strip()
            depth = len(line) - len(line.lstrip("\t"))
            if s.startswith("///"):
                doc.append(s[3:].strip()); i += 1; continue
            if depth == 0 and s.startswith("table "):
                name = _unquote(s[6:]); t["description"] = " ".join(doc); doc = []
            elif depth == 1 and s == "isHidden":
                t["hidden"] = True
            elif depth == 1 and s.startswith("column "):
                cur = {"name": _unquote(s[7:].split("=")[0]), "hidden": False, "key": False, "description": " ".join(doc)}
                t["columns"].append(cur); doc = []
            elif depth == 1 and s.startswith("measure "):
                head, _, expr = s[8:].partition("=")
                body = [expr.strip()] if expr.strip() else []
                j = i + 1
                while j < len(L) and (L[j].startswith("\t\t\t") or (L[j].strip() == "" and j + 1 < len(L) and L[j + 1].startswith("\t\t\t"))):
                    body.append(L[j][3:].rstrip()); j += 1
                cur = {"name": _unquote(head), "expression": "\n".join(body).strip(), "format": None, "folder": None,
                       "description": " ".join(doc)}
                t["measures"].append(cur); doc = []; i = j; continue
            elif depth == 2 and cur is not None:
                if s == "isHidden": cur["hidden"] = True
                elif s == "isKey": cur["key"] = True
                elif s.startswith("formatString:"): cur["format"] = s.split(":", 1)[1].strip()
                elif s.startswith("displayFolder:"): cur["folder"] = s.split(":", 1)[1].strip()
            elif depth == 1:
                cur = None if not s.startswith(("column", "measure")) and s and not s.startswith("lineageTag") else cur
                doc = []
            i += 1
        tables[name] = t
    rels = []
    L = _lines(os.path.join(d, "relationships.tmdl"))
    for k, line in enumerate(L):
        if line.startswith("relationship "):
            r = {"fromCardinality": "many", "toCardinality": "one", "crossFilter": "oneDirection", "active": True}
            for x in L[k + 1:]:
                if not x.startswith("\t"): break
                key, _, val = x.strip().partition(":")
                val = val.strip()
                if key == "fromColumn": r["from"] = tuple(_unquote(p) for p in val.split(".", 1))
                elif key == "toColumn": r["to"] = tuple(_unquote(p) for p in val.split(".", 1))
                elif key == "toCardinality": r["toCardinality"] = val
                elif key == "fromCardinality": r["fromCardinality"] = val
                elif key == "crossFilteringBehavior": r["crossFilter"] = val
                elif key == "isActive": r["active"] = val != "false"
            rels.append(r)
    expr = open(os.path.join(d, "expressions.tmdl"), encoding="utf-8-sig").read()
    queries = re.findall(r"^expression\s+('[^']+'|\S+)\s*=", expr, re.M)
    return {"tables": tables, "relationships": rels, "expressions": [_unquote(q) for q in queries]}

def measures(model):
    return [dict(m, table=t) for t, v in model["tables"].items() for m in v["measures"]]

if __name__ == "__main__":
    import json, sys
    m = read_model(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps({"tables": {k: {"columns": len(v["columns"]), "measures": len(v["measures"]), "hidden": v["hidden"]}
                                 for k, v in m["tables"].items()},
                      "relationships": [f"{r['from']} -> {r['to']} {r['crossFilter']}" for r in m["relationships"]],
                      "expressions": m["expressions"]}, indent=1))
