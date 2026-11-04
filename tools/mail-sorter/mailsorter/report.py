"""Step 4 - the Excel index and the HTML dashboard, saved in output_dir.

  Attachments Index.xlsx  - one row per file, filter/sort in Excel, click to open.
                            Fix a wrong category in the 'Category' column, save,
                            then run  import-review  and  organize .
  Dashboard.html          - double-click to open in any browser. Works offline,
                            straight from the shared drive.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from importlib import resources
from pathlib import Path, PurePosixPath

from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from . import db
from .config import Config
from .organize import fiscal_year

EXCEL_NAME = "Attachments Index.xlsx"
DASHBOARD_NAME = "Dashboard.html"

COLUMNS = [
    ("Date", 11), ("Category", 22), ("Client", 26), ("Insurer", 18), ("Policy No", 20),
    ("File name", 42), ("Type", 7), ("Size (KB)", 10), ("Email subject", 50), ("From", 30),
    ("To", 30), ("CC", 30), ("Forwarded from", 28), ("Email summary (AI)", 45),
    ("Outlook folder", 28), ("Times received", 9), ("Sorted by", 9), ("Confidence", 10),
    ("Reason", 40), ("Open", 8), ("File ID", 12),
]
CAT_COL = 2          # 1-based column of 'Category'
ID_COL = len(COLUMNS)


def _rows(conn):
    return db.first_message_for_files(conn, "WHERE f.category IS NOT NULL").fetchall()


def _date(row) -> datetime | None:
    try:
        return datetime.fromisoformat(row["received"])
    except (TypeError, ValueError):
        return None


def write_excel(cfg: Config, rows, path: Path) -> None:
    wb = Workbook(write_only=True)
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1F4E78")
    link_font = Font(color="0563C1", underline="single")
    n_cats = len(cfg.category_names)

    def header(ws):
        ws.freeze_panes = "A2"
        for i, (_, width) in enumerate(COLUMNS, 1):
            ws.column_dimensions[_col(i)].width = width
        ws.column_dimensions[_col(ID_COL)].hidden = True
        cells = []
        for name, _ in COLUMNS:
            c = WriteOnlyCell(ws, value=name)
            c.font, c.fill = head_font, head_fill
            c.alignment = Alignment(vertical="center")
            cells.append(c)
        ws.append(cells)

    def dropdown(ws, n):
        dv = DataValidation(type="list", formula1=f"=Lists!$A$1:$A${n_cats}", allow_blank=False)
        dv.add(f"{_col(CAT_COL)}2:{_col(CAT_COL)}{max(2, n + 1)}")
        ws.data_validations.append(dv)
        ws.auto_filter.ref = f"A1:{_col(len(COLUMNS) - 1)}{max(2, n + 1)}"

    def line(ws, r):
        d = _date(r)
        target = str(cfg.output_dir / Path(*PurePosixPath(r["organized_path"]).parts)) \
            if r["organized_path"] else r["store_path"]
        link = WriteOnlyCell(ws, value=f'=HYPERLINK("{target}","Open")')
        link.font = link_font
        date_cell = WriteOnlyCell(ws, value=d)
        date_cell.number_format = "dd-mmm-yyyy"
        return [
            date_cell, r["category"], r["client"] or "", r["insurer"] or "",
            r["policy_no"] or "", r["filename"], (r["ext"] or "").lstrip(".").upper(),
            round((r["size"] or 0) / 1024), r["subject"], r["sender_email"] or r["sender_name"],
            _addrs(r["to_addrs"] or r["recipients"]), _addrs(r["cc_addrs"]), r["fwd_from"] or "",
            r["summary"] or "", r["folder"], r["n_emails"], r["method"], r["confidence"], r["reason"] or "",
            link, r["sha256"],
        ]

    review = [r for r in rows if r["confidence"] == "low" or r["category"] == cfg.fallback_category]

    ws = wb.create_sheet("Index")
    header(ws)
    dropdown(ws, len(rows))
    for r in rows:
        ws.append(line(ws, r))

    rv = wb.create_sheet("Needs Review")
    header(rv)
    dropdown(rv, len(review))
    for r in review:
        rv.append(line(rv, r))

    # Summary: category x financial year, then top clients and insurers
    sm = wb.create_sheet("Summary")
    by_fy: dict[str, Counter] = defaultdict(Counter)
    fys = set()
    for r in rows:
        d = _date(r)
        fy = fiscal_year(d) if d else "Unknown"
        fys.add(fy)
        by_fy[r["category"]][fy] += 1
    fys = sorted(fys)
    sm.column_dimensions["A"].width = 30
    title = WriteOnlyCell(sm, value="Files by category and financial year")
    title.font = Font(bold=True, size=13)
    sm.append([title])
    hdr = []
    for v in ["Category", *fys, "Total"]:
        c = WriteOnlyCell(sm, value=v)
        c.font, c.fill = head_font, head_fill
        hdr.append(c)
    sm.append(hdr)
    for cat in cfg.category_names:
        if by_fy.get(cat):
            sm.append([cat, *[by_fy[cat][fy] for fy in fys], sum(by_fy[cat].values())])
    sm.append(["Total", *[sum(by_fy[c][fy] for c in by_fy) for fy in fys], len(rows)])
    for label, key in (("Top clients", "client"), ("Top insurers", "insurer")):
        sm.append([])
        t = WriteOnlyCell(sm, value=label)
        t.font = Font(bold=True, size=13)
        sm.append([t])
        for name, n in Counter((r[key] or "Unknown") for r in rows).most_common(30):
            sm.append([name, n])

    lists = wb.create_sheet("Lists")
    for name in cfg.category_names:
        lists.append([name])
    lists.sheet_state = "hidden"

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.xlsx")
    wb.save(tmp)
    tmp.replace(path)


def _addrs(v) -> str:
    return (v or "").replace(";", "; ")


def _col(n: int) -> str:
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def write_dashboard(cfg: Config, rows, path: Path) -> None:
    cats = list(cfg.category_names)
    lookups: dict[str, dict[str, int]] = {"client": {}, "insurer": {}}

    def idx(kind, value):
        table = lookups[kind]
        if value not in table:
            table[value] = len(table)
        return table[value]

    data = []
    for r in rows:
        d = _date(r)
        data.append([
            d.strftime("%Y-%m-%d") if d else "",
            cats.index(r["category"]) if r["category"] in cats else len(cats) - 1,
            idx("client", r["client"] or "Unknown Client"),
            idx("insurer", r["insurer"] or "Unknown"),
            r["policy_no"] or "",
            r["filename"],
            (r["ext"] or "").lstrip(".").upper(),
            round((r["size"] or 0) / 1024),
            r["subject"] or "",
            r["sender_email"] or r["sender_name"] or "",
            r["organized_path"] or "",
            r["confidence"] or "",
            r["n_emails"],
            _addrs(r["to_addrs"] or r["recipients"]),
            _addrs(r["cc_addrs"]),
            r["fwd_from"] or "",
            r["summary"] or "",
        ])
    payload = {
        "generated": datetime.now().strftime("%d %b %Y, %H:%M"),
        "categories": cats,
        "review": cfg.fallback_category,
        "clients": list(lookups["client"]),
        "insurers": list(lookups["insurer"]),
        "rows": data,
    }
    template = resources.files("mailsorter").joinpath("dashboard.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/null", blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def report(cfg: Config) -> None:
    conn = db.connect(cfg.db_path)
    rows = _rows(conn)
    if not rows:
        print("Nothing to report yet - run extract and classify first.")
        return
    xl = cfg.output_dir / EXCEL_NAME
    try:
        write_excel(cfg, rows, xl)
        print(f"Excel index:  {xl}")
    except PermissionError:
        print(f"Could not write {xl} - is it open in Excel? Close it and run report again.")
    dash = cfg.output_dir / DASHBOARD_NAME
    write_dashboard(cfg, rows, dash)
    print(f"Dashboard:    {dash}")


def import_review(cfg: Config, xlsx: Path | None = None) -> None:
    """Reads category corrections typed into the Excel file back into the database."""
    xlsx = xlsx or cfg.output_dir / EXCEL_NAME
    conn = db.connect(cfg.db_path)
    valid = {n.lower(): n for n in cfg.category_names}
    current = {r[0]: r[1] for r in conn.execute("SELECT sha256, category FROM files")}
    wb = load_workbook(xlsx, read_only=True)
    changes: dict[str, str] = {}
    bad = 0
    for sheet in ("Needs Review", "Index"):     # Needs Review wins if both edited
        if sheet not in wb.sheetnames:
            continue
        for row in wb[sheet].iter_rows(min_row=2, values_only=True):
            if not row or len(row) < ID_COL:
                continue
            sha, cat = row[ID_COL - 1], row[CAT_COL - 1]
            if not sha or sha not in current or not cat:
                continue
            new = valid.get(str(cat).strip().lower())
            if new is None:
                bad += 1
                continue
            if new != current[sha] and sha not in changes:
                changes[sha] = new
    wb.close()
    for sha, cat in changes.items():
        conn.execute(
            "UPDATE files SET category=?, method='manual', confidence='high', reason='Corrected by hand' "
            "WHERE sha256=?", (cat, sha))
    conn.commit()
    print(f"Imported {len(changes):,} corrections from {xlsx.name}"
          + (f" ({bad} rows had a category name that is not in config.yaml - ignored)" if bad else ""))
    if changes:
        print("Now run  organize  then  report  to move the files and refresh the index.")
