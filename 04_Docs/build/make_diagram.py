"""
Draw the star-schema diagram (screenshots/star_schema.png) from the model's own TMDL files:
tables, key columns, visible columns and the 9 relationships are read by tmdl_info.py, nothing is hard-coded.
Run from the project root:  python 04_Docs/build/make_diagram.py
"""
import math, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmdl_info as T

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.path.join(ROOT, "screenshots", "star_schema.png")
M = T.read_model(ROOT)
NAVY, BLUE, GREY, LIGHT, TEXT = "#1E2A44", "#118DFF", "#8A94A6", "#EEF5FF", "#1E2A44"
plt.rcParams["font.family"] = "DejaVu Sans"

rels = M["relationships"]
fact = rels[0]["from"][0]
assert all(r["from"][0] == fact for r in rels), "expected a single fact table"
dims = [r["to"][0] for r in rels]
keyof = {r["to"][0]: r["to"][1] for r in rels}

fig, ax = plt.subplots(figsize=(16, 10), dpi=110)
ax.set_xlim(0, 16); ax.set_ylim(0, 10); ax.axis("off")
fig.patch.set_facecolor("white")

def box(cx, cy, w, title, lines, head_color, body_color="white", title_color="white", fs=10.5):
    lh = 0.26
    h = 0.42 + lh * len(lines) + 0.12
    x0, y0 = cx - w / 2, cy - h / 2
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=body_color, ec=head_color, lw=1.6, zorder=3))
    ax.add_patch(FancyBboxPatch((x0, y0 + h - 0.42), w, 0.42, boxstyle="round,pad=0.02,rounding_size=0.08", fc=head_color, ec=head_color, lw=1.6, zorder=4))
    ax.text(cx, y0 + h - 0.21, title, ha="center", va="center", color=title_color, fontsize=fs + 1, fontweight="bold", zorder=5)
    for i, (txt, style) in enumerate(lines):
        ax.text(x0 + 0.14, y0 + h - 0.42 - 0.18 - i * lh, txt, ha="left", va="center", fontsize=fs - 1.5, zorder=5,
                color=GREY if style == "muted" else TEXT, fontweight="bold" if style == "key" else "normal")
    return (x0, y0, w, h)

def dim_lines(t):
    cols = M["tables"][t]["columns"]
    key = keyof[t]
    vis = [c["name"] for c in cols if not c["hidden"] and c["name"] != key]
    out = [(f"PK  {key}", "key")]
    out += [(f"      {c}", "") for c in vis[:4]]
    if len(vis) > 4: out.append((f"      + {len(vis) - 4} more attributes", "muted"))
    return out

# fact table in the middle
fcols = M["tables"][fact]["columns"]
fks = [r["from"][1] for r in rels]
facts_vis = [c["name"] for c in fcols if c["name"] not in fks and not c["hidden"]]
flines = [("1 row per employee", "muted")] + [(f"FK  {k}", "key") for k in fks] + [("", "")] + [(f"      {c}", "") for c in facts_vis[:5]] + [(f"      + {len(facts_vis) - 5} more numeric columns", "muted")]
fb = box(8, 5.0, 3.5, fact, flines, NAVY, LIGHT, fs=10.5)

# dimensions on an ellipse around the fact
pos = {}
n = len(dims)
for i, t in enumerate(dims):
    a = math.pi / 2 + 2 * math.pi * i / n
    pos[t] = (8 + 6.1 * math.cos(a), 5.0 + 3.85 * math.sin(a))
boxes = {t: box(*pos[t], 2.75, t, dim_lines(t), BLUE) for t in dims}

def edge_point(b, tx, ty):
    x0, y0, w, h = b; cx, cy = x0 + w / 2, y0 + h / 2
    dx, dy = tx - cx, ty - cy
    s = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return cx + dx * s, cy + dy * s

fcx, fcy = fb[0] + fb[2] / 2, fb[1] + fb[3] / 2
for r in rels:
    t = r["to"][0]; b = boxes[t]; bcx, bcy = b[0] + b[2] / 2, b[1] + b[3] / 2
    p1 = edge_point(fb, bcx, bcy); p2 = edge_point(b, fcx, fcy)
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=GREY, lw=1.4, zorder=1)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    ax.add_patch(FancyArrowPatch((mx + (p2[0] - p1[0]) * 0.06, my + (p2[1] - p1[1]) * 0.06), (mx - (p2[0] - p1[0]) * 0.06, my - (p2[1] - p1[1]) * 0.06),
                                 arrowstyle="-|>", mutation_scale=16, color=BLUE, lw=0, zorder=2))
    def lab(p, q, s):
        ax.text(p[0] + (q[0] - p[0]) * 0.12, p[1] + (q[1] - p[1]) * 0.12, s, ha="center", va="center", fontsize=11, fontweight="bold",
                color=NAVY, zorder=6, bbox=dict(boxstyle="circle,pad=0.12", fc="white", ec="none"))
    lab(p1, p2, "*" if r["fromCardinality"] == "many" else "1"); lab(p2, p1, "1" if r["toCardinality"] == "one" else "*")

nm = len(T.measures(M)); folders = sorted({m["folder"] for m in T.measures(M)})
qa_hidden = M["tables"]["QA_Checks"]["hidden"]
ax.text(0.25, 0.35, f"_Measures: {nm} DAX measures in {len(folders)} display folders      QA_Checks: self-test table ({'hidden' if qa_hidden else 'visible'})",
        fontsize=10, color=GREY, ha="left")
ax.text(15.75, 0.35, "Arrows = filter direction (dimension -> fact, single direction)   1 / * = one-to-many", fontsize=10, color=GREY, ha="right")
ax.text(0.25, 9.72, f"Star schema - {len(dims)} dimensions, 1 fact table, {len(rels)} relationships (read from the model's TMDL)",
        fontsize=14, fontweight="bold", color=NAVY, ha="left")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
