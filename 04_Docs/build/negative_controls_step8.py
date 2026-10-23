"""
Negative controls for validate_step8.py: plant one deliberate fault at a time in a throw-away copy of the project and
confirm the validator FAILS on the expected check. Proves the Step 8 validation can actually catch errors.
Usage: python 04_Docs/build/negative_controls_step8.py <project_root>
"""
import os, re, shutil, subprocess, sys, json, zipfile, tempfile
SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."); V = os.path.join(SRC, "04_Docs/build/validate_step8.py")
WORK = tempfile.mkdtemp()
results = []
def run(name, mutate, expect):
    d = os.path.join(WORK, re.sub(r"[^A-Za-z0-9]+", "_", name)[:40]); shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(SRC, d, ignore=lambda dirpath, names: [n for n in names if n == "__pycache__" or (n == "raw" and dirpath.endswith("screenshots"))])
    mutate(d)
    p = subprocess.run([sys.executable, "-W", "ignore", V, d, d + "/rep.txt"], capture_output=True, text=True)
    fails = [l for l in p.stdout.splitlines() if l.startswith("[FAIL]")]
    ok = bool(fails) and all(any(e in f for f in fails) for e in expect)
    results.append((ok, name)); shutil.rmtree(d, ignore_errors=True)
    print(("CAUGHT " if ok else "MISSED ") + name, "->", [f[7:80] for f in fails] or p.stderr[-400:])
def edit(rel, a, b):
    def f(d):
        p = os.path.join(d, rel); s = open(p, encoding="utf-8").read(); assert s.count(a) >= 1, (rel, a); open(p, "w", encoding="utf-8").write(s.replace(a, b, 1))
    return f
def jedit(rel, fn):
    def f(d):
        p = os.path.join(d, rel); j = json.load(open(p, encoding="utf-8-sig")); fn(j); json.dump(j, open(p, "w", encoding="utf-8"))
    return f
def zedit(rel, member, a, b):
    def f(d):
        p = os.path.join(d, rel); zin = zipfile.ZipFile(p); items = [(i, zin.read(i.filename)) for i in zin.infolist()]; zin.close()
        hit = False
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
            for i, data in items:
                if i.filename == member and a.encode() in data: data = data.replace(a.encode(), b.encode(), 1); hit = True
                z.writestr(i, data)
        assert hit, (member, a)
    return f
R, UG, SD = "README.md", "04_Docs/User_Guide.md", "System Design.md"
run("README: one rate mistyped (30.5% -> 30.6%)", edit(R, "30.5% attrition with overtime", "30.6% attrition with overtime"), ["C. Number audit: README.md"])
run("README: hand-typed unsupported number", edit(R, "## Limitations", "Replacing a leaver costs 45% of salary.\n\n## Limitations"), ["C. Number audit: README.md: every one"])
run("README: wrong page count in heading", edit(R, "## Dashboard (8 pages,", "## Dashboard (9 pages,"), ["F. Consistency", "no manual edits"])
run("README: a rate swapped for another real number (30.5% -> 34.9%)", edit(R, "30.5% attrition with overtime", "34.9% attrition with overtime"), ["no manual edits"])
run("Deck content changed but deck not rebuilt", jedit("05_Presentation/deck_content.json", lambda j: j["recs"].__setitem__("title", "Five actions")), ["no manual edits", "appears verbatim in the PPTX"])
run("README: broken screenshot link", edit(R, "screenshots/08_data_quality.png", "screenshots/08_dataquality.png"), ["B. Links: README.md: every relative"])
run("README: tree lists a folder that does not exist", edit(R, "├── 05_Presentation/", "├── 06_Extras/"), ["B. Links: Every entry"])
run("README: DAX code differs from the model", edit(R, "```dax\nDIVIDE ( [Leavers], [Headcount] )\n```", "```dax\n[Leavers] / [Headcount]\n```"), ["D. DAX reference: README DAX code"])
run("README: one measure row dropped", lambda d: (lambda p: open(p, "w", encoding="utf-8").write(re.sub(r"(?m)^\| `Retention Rate` .*\n", "", open(p, encoding="utf-8").read(), count=1)))(os.path.join(d, R)), ["D. DAX reference: README measure table"])
run("README: measure description changed", edit(R, "| Leavers / Headcount. |", "| Leavers divided by employees. |"), ["D. DAX reference: Every measure description"])
run("README: ProjectFolder instructions removed", edit(R, "Edit parameters", "Edit settings"), ["G. Git readiness: README tells"])
run("README: personal e-mail added", edit(R, "Author: **Kapil Sandhu**", "Author: **Kapil Sandhu** (someone.example" + "@" + "gmail.com)"), ["G. Git readiness: No secrets"])
run("User guide: KPI value mistyped (2.80 -> 2.81)", edit(UG, "| 2.80 |", "| 2.81 |"), ["C. Number audit: 04_Docs/User_Guide.md"])
run("System Design: stale check tally (68/68 -> 66/66)", edit(SD, "validated 68/68", "validated 66/66"), ["F. Consistency: Every check tally"])
run("System Design: Step 7 tick no longer matches its report", edit(SD, "validated 28/28 + 18/18", "validated 27/27 + 18/18"), ["F. Consistency: Every check tally"])
run("System Design: Step 8 tick no longer matches its report", lambda d: edit(SD, "validated 45/45 + 25/25", "validated 44/44 + 25/25")(d) if "validated 45/45" in open(os.path.join(d, SD), encoding="utf-8").read() else None, ["F. Consistency: Every check tally"])
run("Model_Design: stale check tally", edit("03_PowerBI/model/Model_Design.md", "68/68 checks passed", "66/66 checks passed"), ["F. Consistency: Every check tally"])
run("Report_Guide: stale visual count", edit("03_PowerBI/report/Report_Guide.md", "77 visuals", "67 visuals"), ["F. Consistency"])
run("Deck: chart bar value differs from facts", zedit("05_Presentation/Talent_Learning_Deck.pptx", "ppt/charts/chart1.xml", "<c:v>0.3125</c:v>", "<c:v>0.35</c:v>"), ["E. Deck: Chart values"])
run("Deck: slide number mistyped (498 -> 500)", zedit("05_Presentation/Talent_Learning_Deck.pptx", "ppt/slides/slide2.xml", ">498<", ">500<"), ["C. Number audit: Deck"])
run("Facts file: value perturbed", jedit("04_Docs/insights_facts.json", lambda j: j["drivers"]["sales_rep"].__setitem__("rate", 0.4)), ["C. Number audit: All"])
run("Power BI result differs (Headcount 1469)", jedit("03_PowerBI/validation/step5_live_results.json", lambda j: j["queries"]["total"]["rows"][0].__setitem__(0, 1469)), ["C. Number audit: All"])
run("A validation report is no longer all-pass", edit("03_PowerBI/validation/validation_report_step3.txt", "[PASS] A. Syntax", "[FAIL] A. Syntax"), ["C. Number audit: All", "F. Consistency"])
run("Extra M query that is not in the PowerQuery folder", edit("03_PowerBI/Talent_Learning_Dashboard.SemanticModel/definition/expressions.tmdl", "expression ProjectFolder", "expression Extra = 1\n\nexpression ProjectFolder"), ["C. Number audit: Power Query ETL count"])
run("A screenshot is missing", lambda d: os.remove(os.path.join(d, "screenshots/08_data_quality.png")), ["A. Deliverables: 8 page screenshots"])
def drop_ignore_and_plant_cache(d):
    edit(".gitignore", "**/.pbi/cache.abf\n", "")(d)
    open(os.path.join(d, "03_PowerBI/Talent_Learning_Dashboard.SemanticModel/.pbi/cache.abf"), "wb").write(b"\0" * 1000)
    p = os.path.join(d, "03_PowerBI/.gitignore"); open(p, "w").write(open(p).read().replace("**/.pbi/cache.abf", ""))
run(".gitignore no longer excludes the Power BI cache (cache present)", drop_ignore_and_plant_cache, ["G. Git readiness: git would commit", "G. Git readiness: .gitignore"])
run("A token committed in a text file", lambda d: open(os.path.join(d, "04_Docs", "notes.txt"), "w").write("token = ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"), ["G. Git readiness: No secrets"])
print(f"\nNEGATIVE CONTROLS: {sum(ok for ok, _ in results)}/{len(results)} caught")
shutil.rmtree(WORK, ignore_errors=True)
sys.exit(0 if all(ok for ok, _ in results) else 1)
