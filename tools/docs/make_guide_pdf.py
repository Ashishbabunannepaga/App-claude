"""Builds docs/CapitUp-Setup-Guide.pdf from docs/SETUP.md (with its screenshots).

Needs: pip install markdown; Node with Playwright (Chromium).  Run from the repo root:
    python tools/docs/make_guide_pdf.py
"""
import pathlib
import subprocess
import tempfile

import markdown

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Inter','Noto Sans','Noto Sans Devanagari',Arial,sans-serif; font-size: 10.5pt; color:#0F1F1D; line-height:1.45; }
h1 { color:#0B7A75; font-size:22pt; margin:0 0 4pt; }
h2 { color:#0B7A75; font-size:15pt; border-bottom:1px solid #E1E8E6; padding-bottom:3pt; margin-top:18pt; page-break-after: avoid; }
h3 { font-size:12pt; margin-top:12pt; page-break-after: avoid; }
code { background:#EAF5F3; padding:1px 3px; border-radius:3px; font-size:9pt; }
pre { background:#0F1F1D; color:#E6EEEC; padding:8pt; border-radius:6px; font-size:8.5pt; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background:none; color:inherit; padding:0; }
table { border-collapse: collapse; width:100%; margin:6pt 0; font-size:9pt; }
th, td { border:1px solid #E1E8E6; padding:4pt 5pt; vertical-align: top; text-align:left; }
th { background:#EAF5F3; }
tr { page-break-inside: avoid; }
td img { width: 100%; max-width: 190px; border:1px solid #E1E8E6; border-radius:8px; }
a { color:#0B7A75; }
hr { border:none; border-top:1px solid #E1E8E6; }
"""
PDF_JS = """
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + process.argv[2], { waitUntil: 'networkidle' });
  await p.pdf({ path: process.argv[3], format: 'A4', printBackground: true,
    margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' }, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#888">CapitUp setup guide · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>' });
  await b.close(); })();
"""


def main() -> None:
    body = markdown.markdown((DOCS / "SETUP.md").read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>CapitUp setup guide</title><style>{CSS}</style></head><body>{body}</body></html>'
    page = DOCS / "_guide.html"  # next to the .md so the screenshot paths resolve
    page.write_text(html, encoding="utf-8")
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as js:
            js.write(PDF_JS)
        subprocess.run(["node", js.name, str(page), str(DOCS / "CapitUp-Setup-Guide.pdf")], check=True)
    finally:
        page.unlink(missing_ok=True)
    print("wrote", DOCS / "CapitUp-Setup-Guide.pdf")


if __name__ == "__main__":
    main()
