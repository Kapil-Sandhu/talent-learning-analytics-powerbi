"""
Step 5 - write all DAX measures (from measures_spec.py) into the Power BI-saved _Measures.tmdl.
* Keeps everything Power BI wrote (placeholder column, partition, annotations) and its CRLF line endings.
* Idempotent: existing measure blocks are removed first, so running it twice gives the same file.
Run with Power BI Desktop CLOSED (Desktop does not notice external file changes and would overwrite them on save):
    python 03_PowerBI/model/add_measures.py [project_root]
"""
import os, re, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from measures_spec import MEASURES

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
TMDL = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    ROOT, "03_PowerBI", "Talent_Learning_Dashboard.SemanticModel", "definition", "tables", "_Measures.tmdl")
NS = uuid.UUID("6f1c2a52-5d1e-4a8e-9a43-7d2b8f0c9e11")


def quote(name):
    return name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) else "'" + name.replace("'", "''") + "'"


def measure_block(m):
    out = [f"\t/// {line}" for line in m["desc"].splitlines()]
    if len(m["expr"]) == 1:
        out.append(f"\tmeasure {quote(m['name'])} = {m['expr'][0]}")
    else:
        out.append(f"\tmeasure {quote(m['name'])} =")
        out += [f"\t\t\t{line}" for line in m["expr"]]
    out += [f"\t\tformatString: {m['fmt']}",
            f"\t\tdisplayFolder: {m['folder']}",
            f"\t\tlineageTag: {uuid.uuid5(NS, 'measure/' + m['name'])}",
            ""]
    return out


def split_level1(lines):
    """Split table body into level-1 chunks (an object plus its /// description lines)."""
    chunks, cur, pending_desc = [], [], []
    for ln in lines:
        is_desc = ln.startswith("\t///")
        is_obj = re.match(r"\t[^\t/]", ln) is not None
        if is_desc:
            pending_desc.append(ln)
            continue
        if is_obj:
            if cur:
                chunks.append(cur)
            cur = pending_desc + [ln]
            pending_desc = []
        else:
            cur += pending_desc + [ln]
            pending_desc = []
    if cur or pending_desc:
        chunks.append(cur + pending_desc)
    return chunks


def main():
    raw = open(TMDL, "rb").read().decode("utf-8-sig")
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    # header = description + "table _Measures" + table-level properties (2-tab lines are not expected here)
    t = next(i for i, l in enumerate(lines) if l.startswith("table _Measures"))
    j = t + 1
    while j < len(lines) and (lines[j].startswith("\t") and not lines[j].startswith("\t\t")) and re.match(r"\t(lineageTag|isHidden|description)", lines[j]):
        j += 1
    header, body = lines[:j], lines[j:]
    chunks = split_level1(body)
    kept = [c for c in chunks if not any(re.match(r"\tmeasure ", l) for l in c)]
    removed = len(chunks) - len(kept)
    new = header + [""]
    for m in MEASURES:
        new += measure_block(m)
    rest = [l for c in kept for l in c]
    while rest and rest[0] == "":
        rest.pop(0)
    new += rest
    text = "\n".join(new)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text.endswith("\n"):
        text += "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    open(TMDL, "wb").write(text.encode("utf-8"))
    print(f"wrote {len(MEASURES)} measures to {TMDL} (removed {removed} old measure blocks, CRLF={crlf})")


if __name__ == "__main__":
    main()
