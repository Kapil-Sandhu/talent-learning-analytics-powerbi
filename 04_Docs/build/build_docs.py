"""
Step 8 - write README.md, 04_Docs/User_Guide.md and 05_Presentation/deck_content.json (input of build_deck.js).
Every number comes from docnums.py (facts file / measures from the raw CSV / project files / validation reports)
and is logged in 04_Docs/analysis/number_manifest_step8.json for validate_step8.py.
The DAX reference is read from the model's TMDL, so it is always the code that is really in the model.
Run from the project root:  python 04_Docs/build/build_docs.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docnums as N

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
N.init(ROOT)
pct, pts, num, ratio, orr, mval, pc = N.pct, N.pts, N.num, N.ratio, N.orr, N.mval, N.pc
D, L = "drivers", "logit.terms"
REPO_URL = "https://github.com/Kapil-Sandhu"
PAGES = N.page_names()
SHOTS = ["01_overview.png", "02_insights_actions.png", "03_attrition_drivers.png", "04_training_learning.png",
         "05_satisfaction_performance.png", "06_job_role_summary.png", "07_employee_details.png", "08_data_quality.png"]
PAGE_Q = {
    "Overview": "How big is attrition and where is it concentrated?",
    "Insights & Actions": "What should HR do about it?",
    "Attrition Drivers": "Which groups leave most?",
    "Training & Learning": "Who gets trained, and does it relate to attrition?",
    "Satisfaction & Performance": "Do satisfaction and performance ratings relate to attrition?",
    "Job Role Summary": "Which roles need attention first?",
    "Employee Details": "Who exactly is in this group? (drill-through)",
    "Data Quality": "Can I trust the numbers? (self-tests, recalculated on every refresh)",
}
assert list(PAGE_Q) == PAGES, f"page list changed: {PAGES}"
M = N.MODEL
MEASURES = [m for t in M["tables"].values() for m in t["measures"]]
FOLDERS = sorted({m["folder"] for m in MEASURES})

def ot_holds():
    v = sum(x["rate_ot"] > x["rate_no_ot"] for x in N.F["overtime_by_role"].values())
    return N.put(str(v), "facts:overtime_by_role[count rate_ot > rate_no_ot]", v)
def ot_roles():
    v = len(N.F["overtime_by_role"]); return N.put(str(v), "facts:overtime_by_role[count]", v)

# =====================================================================================================  README
def readme():
    o = []
    w = o.append
    w("# Talent & Learning Analytics Dashboard (Power BI)\n")
    w(f"An HR analytics dashboard that tracks **headcount, attrition, training, satisfaction and performance** by department, "
      f"job role and tenure, finds the main **attrition drivers**, and turns them into recommendations for HR and Learning & Development.\n")
    w(f"Built with **Power BI, Power Query (M), DAX and Excel** on the public IBM HR Analytics sample "
      f"({pc('csv_rows')} employees, fictional data). Every step - from the raw CSV to the numbers in the slides - "
      f"is checked by automated validation against the raw data ({N.validation_total()} checks, all passing).\n")
    w("![Overview page](screenshots/01_overview.png)\n")
    # ---- findings
    w("## Key findings\n")
    w(f"- **{pct('company.attrition_rate')} of employees left** ({num('company.leavers')} of {num('company.headcount')}).")
    w(f"- **Overtime is the strongest driver:** {pct('overtime_rates.ot')} attrition with overtime vs {pct('overtime_rates.no_ot')} without "
      f"({ratio('overtime_rates.ratio')}). It holds within job roles (odds ratio {orr('overtime_mh_or_by_role.or')}) and after controlling for "
      f"tenure, satisfaction, job level, stock options and other factors in a logistic regression (odds ratio {orr(L + '.Overtime.odds_ratio')}).")
    w(f"- **The first year is the riskiest:** {pct(D + '.early_tenure.rate')} of employees in their first 0-1 years left - "
      f"{pct('segment_ot_early.rate')} when they also work overtime.")
    w(f"- **Sales Representatives are the hotspot:** {pct(D + '.sales_rep.rate')} attrition ({pts(D + '.sales_rep.vs_company_pts')} vs the company).")
    w(f"- **Engagement matters:** low job satisfaction {pct(D + '.low_job_sat.rate')}, bad work-life balance {pct(D + '.bad_wlb.rate')}.")
    w(f"- **Performance rating does not predict attrition** ({pct(D + '.outstanding_perf.rate')} for Outstanding vs "
      f"{pct(D + '.outstanding_perf.rest_rate')} for everyone else).\n")
    w("Full analysis with confidence intervals, significance tests and a logistic regression: "
      "[`04_Docs/Insights_and_Recommendations.md`](04_Docs/Insights_and_Recommendations.md). "
      "Five-slide summary: [`05_Presentation/Talent_Learning_Deck.pdf`](05_Presentation/Talent_Learning_Deck.pdf).\n")
    w("> The data is a fictional point-in-time snapshot, so these are associations, not proven causes. "
      "The recommendations are framed as pilots to test.\n")
    # ---- pages
    w(f"## Dashboard ({pc('pages')} pages, {pc('visuals')} visuals)\n")
    w("| Page | Question it answers |\n|---|---|")
    for p in PAGES: w(f"| **{p}** | {PAGE_Q[p]} |")
    w("")
    w("Every analysis page has **Department** and **Job role** slicers. Right-click any job role and choose "
      "**Drill through -> Employee Details** to see the people behind a number. See the [User Guide](04_Docs/User_Guide.md).\n")
    w("<table>")
    for i in range(0, len(PAGES), 2):
        w("<tr>")
        for p, s in zip(PAGES[i:i + 2], SHOTS[i:i + 2]):
            w(f'<td width="50%"><img src="screenshots/{s}" alt="{p} page"><br><b>{p}</b></td>')
        w("</tr>")
    w("</table>\n")
    # ---- architecture
    w("## How it is built\n")
    w("```mermaid\nflowchart LR")
    w(f'    A["Raw CSV<br/>{pc("csv_rows")} rows x {pc("csv_cols")} columns"] --> B["Excel<br/>profiling + lookup tables"]')
    w(f'    B --> C["Power Query (M)<br/>{pc("queries")} queries: clean, map codes, build bands"]')
    w(f'    C --> D["Star schema<br/>{pc("dimensions")} dimensions + 1 fact"]')
    w(f'    D --> E["DAX<br/>{pc("measures")} measures"]')
    w(f'    E --> F["Report<br/>{pc("pages")} pages"]')
    w('    F --> G["Insights +<br/>recommendations"]')
    w("```\n")
    w("| Stage | What happens | Where |\n|---|---|---|")
    w("| Excel | Data profiling (pivot tables, KPI summary) and a lookup workbook that maps codes to labels and defines the bands | `02_Excel_Profiling/`, `01_Data/lookups/` |")
    w(f"| Power Query | {pc('queries')} M queries: typed import, cleaning, code-to-label mapping, age / tenure / income / training bands, split into dimensions and fact, plus a self-testing QA table | `03_PowerBI/PowerQuery/` |")
    w(f"| Model | Star schema with {pc('relationships')} single-direction one-to-many relationships, surrogate keys, sort-by columns, hidden helper columns | `03_PowerBI/Talent_Learning_Dashboard.SemanticModel/` |")
    w(f"| DAX | {pc('measures')} measures in {pc('folders')} display folders (headcount and attrition, tenure, training, overtime, satisfaction, demographics) | `03_PowerBI/model/DAX_Measures.md` |")
    w(f"| Report | {pc('pages')} pages incl. a drill-through page and a data-quality page | `03_PowerBI/Talent_Learning_Dashboard.Report/` |")
    w("")
    w("The project is saved in **Power BI Project (PBIP) format**: the model is plain-text TMDL and the report is PBIR JSON, so every change "
      "can be reviewed line by line in Git. The model and report definitions are generated by scripts "
      "(`03_PowerBI/model/build_pbip.py`, `03_PowerBI/report/build_report.py`), so the whole project can be rebuilt from source.\n")
    # ---- model
    w("## Data model\n")
    w("![Star schema](screenshots/star_schema.png)\n")
    w("- **Why a star schema for one flat file?** Clean slicers, simple DAX, and room to add real HR tables later (courses, hires, exits) as new facts that share these dimensions.")
    w("- **Single-direction filters** (dimension -> fact) keep filter paths unambiguous. `DimEmployee` is related many-to-one instead of one-to-one so it does not force two-way filtering.")
    w("- **Sort-by columns** put bands and ratings in logical order (Low -> Very High, 0-1 yrs -> 11+ yrs) instead of alphabetical.")
    w(f"- **Self-testing model:** the hidden `QA_Checks` table recalculates {pc('qa_checks')} checks (row counts, duplicates, nulls, orphan keys, control totals) on every refresh and is shown on the Data Quality page.\n")
    w("Details: [`03_PowerBI/model/Model_Design.md`](03_PowerBI/model/Model_Design.md).\n")
    # ---- DAX
    w("## DAX measures\n")
    w(f"All {pc('measures')} measures live in the `_Measures` table. Ratios use `DIVIDE()` (no divide-by-zero errors), segment measures use "
      "`KEEPFILTERS()` so they respect filters already on the visual, and only the company baseline uses `REMOVEFILTERS()`.\n")
    w("| Measure | Value (whole company) | Meaning |\n|---|---|---|")
    for m in MEASURES:
        w(f"| `{m['name']}` | {mval(m['name'])} | {m['description']} |")
    w("")
    for f in FOLDERS:
        ms = [m for m in MEASURES if m["folder"] == f]
        w(f"<details><summary><b>DAX - {f[2:]}</b> ({len(ms)} measures)</summary>\n")
        for m in ms:
            w(f"**{m['name']}**  (format `{m['format']}`)\n```dax\n{m['expression']}\n```")
        w("</details>\n")
    w("Design notes and likely interview questions: [`03_PowerBI/model/DAX_Measures.md`](03_PowerBI/model/DAX_Measures.md).\n")
    # ---- open
    w("## How to open it\n")
    w("**You need:** Windows and [Power BI Desktop](https://www.microsoft.com/power-platform/products/power-bi/desktop) (free).\n")
    w("1. Download the repository (**Code -> Download ZIP**, then unzip) or `git clone` it.")
    w("2. Open `03_PowerBI/Talent_Learning_Dashboard.pbip` in Power BI Desktop. It opens without data, because the data cache is not stored in Git.")
    w("3. Point the project at your copy: **Home -> Transform data (drop-down arrow) -> Edit parameters -> `ProjectFolder`** = the folder you unzipped, "
      "ending with a backslash (for example `C:\\Users\\you\\Downloads\\Talent-Learning-Dashboard\\`). Click OK.")
    w("4. Click **Home -> Refresh**. It loads all employees and recalculates the QA checks (see the Data Quality page - every row should say PASS).")
    w("5. Optional: **File -> Save as -> Power BI file (.pbix)** for a single file you can share.\n")
    w("No Power BI? Look at the screenshots above, the [dashboard preview PDF](04_Docs/Dashboard_Preview.pdf), or the [deck](05_Presentation/Talent_Learning_Deck.pdf).\n")
    # ---- validation
    w("## Validation\n")
    w("Every step was validated against the raw CSV with independent Python checks, and the Power BI checks were run "
      "inside Power BI Desktop (refresh, DAX queries, opening every page).\n")
    w("| Step | What is checked | Result |\n|---|---|---|")
    rows = [
        (1, "Data: row and column counts, unique employee IDs, no missing values, valid categories and value ranges, logical consistency"),
        (2, "Excel workbooks: lookups, KPI summary, profiles, data dictionary and key findings recalculated and compared with pandas"),
        (3, "Power Query: all queries run in the real Power Query engine; every output table compared cell by cell with an independent Python mirror"),
        (4, "Star schema: relationships, keys, cardinality, filter direction; refresh and DAX tests in Power BI Desktop"),
        (5, "DAX measures: parsed by Microsoft's TMDL serializer, all Ready in Power BI, Excel KPIs reproduced, values vs pandas incl. edge cases"),
        (6, "Report: Microsoft's official JSON schemas, field references, layout, every displayed value vs the raw CSV, every page opened in Power BI"),
        (7, "Insights: statistics recomputed independently, every number reconciled with Power BI, no hand-typed numbers"),
    ]
    for s, what in rows:
        w(f"| {s} | {what} | [{N.validation(s)} passed]({N.validation_file(s)}) |")
    w("")
    w(f"The Step 7 validator was also tested with deliberately planted errors ({N.negative_controls_step7()} caught). "
      "This documentation is checked by `04_Docs/build/validate_step8.py` (every number traced to its source, every link and file reference exists, the DAX above equals the model).\n")
    w("To re-run the offline checks: `pip install pandas openpyxl jsonschema statsmodels scikit-learn matplotlib`, then run the "
      "`validate_*.py` scripts from the project root (each script's header shows its arguments). The PowerShell checks need Power BI Desktop open with the project.\n")
    # ---- structure
    w("## Repository structure\n")
    w("```")
    w(".")
    w("├── README.md")
    w("├── System Design.md                     architecture and step-by-step plan")
    w("├── 01_Data/                             raw CSV, lookup workbook, Step 1 validation")
    w("├── 02_Excel_Profiling/                  Excel data profiling + Step 2 validation")
    w("├── 03_PowerBI/")
    w("│   ├── Talent_Learning_Dashboard.pbip   <- open this in Power BI Desktop")
    w("│   ├── Talent_Learning_Dashboard.SemanticModel/   model (TMDL)")
    w("│   ├── Talent_Learning_Dashboard.Report/          report (PBIR)")
    w(f"│   ├── PowerQuery/                      the {pc('queries')} M queries + setup guide")
    w("│   ├── model/                           model + measure generators, Model_Design.md, DAX_Measures.md")
    w("│   ├── report/                          report generator + Report_Guide.md")
    w("│   └── validation/                      validators and reports for Steps 3-6")
    w("├── 04_Docs/                             insights, user guide, dashboard preview PDF, doc generators")
    w("├── 05_Presentation/                     5-slide deck (PPTX + PDF)")
    w("└── screenshots/                         page screenshots + star schema")
    w("```\n")
    # ---- data
    w("## Data source and licence\n")
    w("- **Dataset:** IBM HR Analytics Employee Attrition & Performance - a fictional dataset created by IBM data scientists, "
      "published on [Kaggle](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset). "
      "IBM lists it under the Open Database License (ODbL) for the database and the Database Contents License (DbCL) for its contents "
      "([source](https://github.com/IBM/employee-attrition-aif360)). The CSV is included unchanged in `01_Data/raw/`.")
    w("- **Code and documentation** in this repository: MIT License (see `LICENSE`).\n")
    w("## Limitations\n")
    w("- Fictional sample data: re-run the pipeline on real HR data before drawing real conclusions.")
    w("- One snapshot with no dates: no trends, and no before/after measurement of any action.")
    w("- Training is only recorded as a count of trainings last year (no course type, hours or completion).\n")
    w("---\n")
    w(f"Author: **Kapil Sandhu** - [GitHub]({REPO_URL})\n")
    return "\n".join(o)

# =====================================================================================================  USER GUIDE
def user_guide():
    o = []
    w = o.append
    w("# User Guide - Talent & Learning Analytics Dashboard\n")
    w(f"For HR, Talent and Learning & Development users. The dashboard covers {pc('csv_rows')} employees (IBM HR sample data, fictional) "
      "at one point in time.\n")
    w("## 1. Open the dashboard")
    w("- Open `03_PowerBI/Talent_Learning_Dashboard.pbip` in Power BI Desktop (or a `.pbix` copy if you were sent one).")
    w("- If the visuals are empty, click **Home -> Refresh**. If the refresh cannot find the files, set "
      "**Home -> Transform data (drop-down arrow) -> Edit parameters -> ProjectFolder** to the project folder and refresh again.\n")
    w("## 2. The pages")
    w("| Page | Use it to |\n|---|---|")
    for p in PAGES: w(f"| **{p}** | {PAGE_Q[p]} |")
    w("")
    w("## 3. Filter, highlight and drill through")
    w("- **Slicers:** use the **Department** and **Job role** drop-downs at the top right of each analysis page. Hold **Ctrl** to select several values. "
      "To clear a slicer, hover over it and click the eraser icon (**Clear selections**).")
    w("- **Cross-filter:** click a bar to filter the other visuals on the same page; click it again to undo.")
    w("- **Drill through:** right-click a job role (a bar or a row in the Job Role Summary matrix) -> **Drill through -> Employee Details**. "
      "The page shows the employees of that role with their status, tenure, training and income.")
    w("- **Back button:** the arrow at the top right of Employee Details returns to the page you came from. In Power BI Desktop, **Ctrl+click** it; "
      "in the Power BI service a normal click works.")
    w("- **Tooltips:** hover over any bar to see its exact value.\n")
    w("## 4. KPI definitions")
    w("| KPI | Definition | Company value |\n|---|---|---|")
    kpis = [
        ("Headcount", "Employees in the current selection (leavers included)"),
        ("Leavers", "Employees who left"),
        ("Attrition Rate", "Leavers / Headcount"),
        ("Attrition vs Company (pts)", "Selected attrition rate minus the company rate; positive = worse than the company"),
        ("Avg Tenure (Years)", "Average years at the company"),
        ("Early Tenure Attrition Rate (0-1 yrs)", "Attrition rate of employees in their first 0-1 years"),
        ("Training per Employee", "Trainings attended last year / Headcount"),
        ("% No Training", "Share of employees with no training last year"),
        ("Overtime %", "Share of employees who work overtime"),
        ("Overtime Attrition Ratio", "Attrition with overtime / attrition without overtime"),
        ("% Low Job Satisfaction", "Share of employees rating job satisfaction Low (1 on a 1-4 scale)"),
        ("Avg Work-Life Balance", "Average rating from 1 (Bad) to 4 (Best)"),
    ]
    for k, d in kpis:
        assert any(m["name"] == k for m in MEASURES), k
        val = mval(k)
        if k == "Attrition vs Company (pts)":   # 0.0% for the whole company by definition - add a meaningful example
            v = N.get(D + ".sales_rep.vs_company_pts")
            val += " (company); " + N.put(N.fmt(v / 100, N.measure_fs(k)), "facts:" + D + ".sales_rep.vs_company_pts", v) + " for Sales Representatives"
        w(f"| **{k}** | {d} | {val} |")
    w("")
    w("All values change with the slicers, except the company baseline used by *Attrition vs Company (pts)*. "
      "Full list of measures and their DAX: `03_PowerBI/model/DAX_Measures.md`.\n")
    w("## 5. Read the numbers carefully")
    w("- **Associations, not causes.** The data is a snapshot; use the findings to choose pilots, not as proof.")
    w(f"- **Small groups move a lot.** For example, only {num(D + '.no_training.n')} employees had no training and "
      f"{num(D + '.sales_rep.n')} are Sales Representatives - one person more or less changes their rate noticeably.")
    w("- **No dates.** There are no trends over time; every page shows the same moment.")
    w(f"- **Data Quality page:** if any of the {pc('qa_checks')} checks shows FAIL after a refresh, do not use the numbers until the data is fixed.\n")
    w("## 6. Page layout at a glance")
    w("Every analysis page follows the same layout: title and slicers at the top, KPI cards below them, charts underneath - read left to right.\n")
    w("![Overview page](../screenshots/01_overview.png)\n")
    return "\n".join(o)

# =====================================================================================================  DECK CONTENT
def deck():
    groups = [("Sales Representatives", "sales_rep"), ("0-1 years at the company", "early_tenure"), ("Bad work-life balance", "bad_wlb"),
              ("Works overtime", "overtime"), ("Low job satisfaction", "low_job_sat")]
    # chart bars carry raw values (PowerPoint renders the labels); validate_step8 checks them against the facts file
    chart = [{"label": lab, "value": N.get(f"{D}.{k}.rate"), "path": f"{D}.{k}.rate"} for lab, k in groups]
    chart.append({"label": "Company", "value": N.get("company.attrition_rate"), "path": "company.attrition_rate"})
    c = {
        "title": {
            "kicker": "Talent & Learning Analytics Dashboard",
            "headline": f"{pct('company.attrition_rate')} of employees left - where, why, and what HR can do",
            "stats": [[num("company.headcount"), "employees"], [num("company.leavers"), "leavers"], [pct("company.attrition_rate"), "attrition rate"]],
            "sub": "Power BI | Power Query | DAX | Excel - IBM HR sample data (fictional), one point-in-time snapshot",
            "notes": "The question: why do people leave, and what can HR and L&D do about it? The answer comes from a Power BI dashboard built on the IBM HR sample."},
        "data": {
            "title": "From a raw CSV to a self-testing Power BI model",
            "steps": [
                ["Raw data", f"{pc('csv_rows')} employees x {pc('csv_cols')} columns"],
                ["Excel", "Profiling + lookup tables"],
                ["Power Query", f"{pc('queries')} queries: clean, map, band"],
                ["Model + DAX", f"Star schema, {pc('measures')} measures"],
                ["Report", f"{pc('pages')} pages, drill-through"]],
            "callout": [N.validation_total(), "automated checks passed, Steps 1-7"],
            "callout_sub": "Every displayed number was compared with an independent calculation from the raw CSV",
            "notes": "Each stage is validated before the next one starts. The model also tests itself on every refresh (Data Quality page)."},
        "model": {
            "title": "A star schema built for slicing",
            "image": "screenshots/star_schema.png",
            "points": [
                ["Single-direction filters", f"{pc('relationships')} one-to-many relationships, dimension to fact - no ambiguous paths"],
                ["Measures, not columns", f"{pc('measures')} DAX measures with DIVIDE, KEEPFILTERS and a REMOVEFILTERS company baseline"],
                ["Self-testing", f"{pc('qa_checks')} QA checks recalculated on every refresh"],
                ["Code, not clicks", "PBIP / TMDL text format: reviewable in Git and rebuildable from scripts"]],
            "notes": "Why a star schema on one flat file: clean slicers, simple DAX, and room to add real HR tables later."},
        "findings": {
            "title": "Overtime and the first year stand out",
            "chart_title": "Attrition rate by group",
            "chart": chart,
            "points": [
                [ratio("overtime_rates.ratio"), f"higher attrition with overtime ({pct('overtime_rates.ot')} vs {pct('overtime_rates.no_ot')}); odds ratio {orr(L + '.Overtime.odds_ratio')} after controls"],
                [pct("segment_ot_early.rate"), "attrition in the first 0-1 years when combined with overtime"],
                [pts(D + ".sales_rep.vs_company_pts"), "Sales Representatives vs the company rate"]],
            "foot": f"Performance rating does not predict attrition ({pct(D + '.outstanding_perf.rate')} Outstanding vs {pct(D + '.outstanding_perf.rest_rate')} others). Associations in a snapshot, not proven causes.",
            "notes": f"Overtime goes with higher attrition in {ot_holds()} of {ot_roles()} job roles, within roles (odds ratio {orr('overtime_mh_or_by_role.or')}) and in a logistic regression with tenure, satisfaction, job level, stock options and other factors (odds ratio {orr(L + '.Overtime.odds_ratio')})."},
        "recs": {
            "title": "Four actions to pilot, one data fix",
            "cards": [
                ["Reduce sustained overtime", "Monthly overtime reviews and workload rebalancing, starting with the highest-risk roles",
                 "Track: Overtime %, Attrition Rate - Overtime"],
                ["Make the first year stick", "90-day onboarding, a mentor for every new hire, front-loaded learning",
                 "Track: Early Tenure Attrition Rate (0-1 yrs)"],
                ["Retain Sales Representatives", f"Pay and incentive benchmark, career path to Sales Executive ({pct(D + '.sales_rep.rate')} attrition today)",
                 "Track: Attrition vs Company (pts)"],
                ["Act on engagement signals", "Quarterly pulse survey, manager follow-up within 30 days",
                 "Track: % Low Job Satisfaction"]],
            "data_fix": "Data fix: record course type, hours and completion, calibrate performance ratings, and add dates to measure whether the actions work.",
            "notes": "Each action has a measure in the dashboard to track it. Run them as pilots with a comparison group, because the data shows associations, not causes."},
    }
    return c

if __name__ == "__main__":
    md = readme()
    open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n").write(md)
    n_readme = len(N.MANIFEST)
    ug = user_guide()
    open(os.path.join(ROOT, "04_Docs", "User_Guide.md"), "w", encoding="utf-8", newline="\n").write(ug)
    n_ug = len(N.MANIFEST)
    dk = deck()
    os.makedirs(os.path.join(ROOT, "05_Presentation"), exist_ok=True)
    json.dump(dk, open(os.path.join(ROOT, "05_Presentation", "deck_content.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for i, m in enumerate(N.MANIFEST):
        m["doc"] = "README.md" if i < n_readme else ("04_Docs/User_Guide.md" if i < n_ug else "05_Presentation/deck_content.json")
    N.save_manifest(os.path.join(ROOT, "04_Docs", "analysis", "number_manifest_step8.json"))
    print(f"README.md {len(md):,} chars, User_Guide.md {len(ug):,} chars, deck_content.json; {len(N.MANIFEST)} numbers logged")
