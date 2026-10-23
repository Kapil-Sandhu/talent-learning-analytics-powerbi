"""
Render 04_Docs/User_Guide.md to 04_Docs/User_Guide.pdf (A4, headless Chromium) and assemble the 8 page
screenshots into 04_Docs/Dashboard_Preview.pdf.
Run from the project root:  python 04_Docs/build/render_pdfs.py
"""
import glob, os, sys
import markdown
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
CSS = """
@page { size: A4; margin: 14mm 15mm 14mm 15mm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; color: #1E2A44; line-height: 1.38; }
h1 { font-size: 16pt; margin: 0 0 4px 0; color: #1E2A44; }
h2 { font-size: 11.5pt; margin: 12px 0 4px 0; color: #0B5CAD; }
p { margin: 3px 0 6px 0; }
ul { margin: 2px 0 6px 0; padding-left: 18px; } li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 8px 0; font-size: 9pt; }
th { background: #1E2A44; color: white; text-align: left; padding: 3px 6px; }
td { border-bottom: 1px solid #D9DEE7; padding: 3px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #F4F7FB; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 8.6pt; background: #EEF2F7; padding: 0 3px; border-radius: 3px; }
"""

def md_to_pdf(md_path, pdf_path, page):
    html = markdown.markdown(open(md_path, encoding="utf-8").read(), extensions=["tables"])
    tmp = os.path.join(os.path.dirname(os.path.abspath(md_path)), "_render_tmp.html")   # same folder, so relative image paths resolve
    open(tmp, "w", encoding="utf-8").write(f"<html><head><meta charset='utf-8'><style>{CSS} img {{ width: 100%; border: 1px solid #D9DEE7; }}</style></head><body>{html}</body></html>")
    page.goto("file://" + tmp); page.wait_for_load_state("networkidle")
    os.remove(tmp)
    page.pdf(path=pdf_path, format="A4", print_background=True, prefer_css_page_size=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    md_to_pdf(os.path.join(ROOT, "04_Docs", "User_Guide.md"), os.path.join(ROOT, "04_Docs", "User_Guide.pdf"), pg)
    b.close()

shots = sorted(glob.glob(os.path.join(ROOT, "screenshots", "0[1-8]_*.png")))
assert len(shots) == 8, shots
ims = [Image.open(s).convert("RGB") for s in shots]
ims[0].save(os.path.join(ROOT, "04_Docs", "Dashboard_Preview.pdf"), save_all=True, append_images=ims[1:], resolution=110)
print("wrote User_Guide.pdf and Dashboard_Preview.pdf")
