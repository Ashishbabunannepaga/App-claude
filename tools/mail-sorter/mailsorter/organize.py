"""Step 3 - put every file into the shared-drive folder tree.

Running it again is safe: files already in the right place are left alone,
and files whose category was corrected are moved to their new folder.
"""
from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from pathlib import Path, PurePosixPath

from . import db
from .config import Config

BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
            *(f"lpt{i}" for i in range(1, 10))}
MAX_FULL_PATH = 250


def safe(part: str, limit: int = 80) -> str:
    part = BAD_CHARS.sub(" ", part or "")
    part = " ".join(part.split()).strip(" .")[:limit].strip(" .")
    if part.lower() in RESERVED:
        part = f"_{part}"
    return part


def fiscal_year(d: datetime) -> str:
    start = d.year if d.month >= 4 else d.year - 1
    return f"FY{start}-{(start + 1) % 100:02d}"


def tokens(row, cfg: Config) -> dict[str, str]:
    try:
        d = datetime.fromisoformat(row["received"])
    except (TypeError, ValueError):
        d = datetime(1900, 1, 1)
    return {
        "category": row["category"] or cfg.fallback_category,
        "fy": fiscal_year(d),
        "year": str(d.year),
        "month": d.strftime("%Y-%m"),
        "date": d.strftime("%Y-%m-%d"),
        "client": row["client"] or "Unknown Client",
        "insurer": row["insurer"] or "",
        "policy": row["policy_no"] or "",
        "name": row["filename"] or f"file{row['ext'] or ''}",
    }


def target_relpath(row, cfg: Config) -> PurePosixPath:
    t = tokens(row, cfg)
    folders = [safe(p.format(**t)) or "_" for p in cfg.layout.split("/")]

    stem, ext = os.path.splitext(t["name"])
    ext = (row["ext"] or ext.lower())[:10]
    name = cfg.filename.format(**{**t, "name": stem})
    name = re.sub(r"_+", "_", name).strip("_ ")
    name = safe(name, 150) or "file"

    room = MAX_FULL_PATH - len(str(cfg.output_dir)) - sum(len(f) + 1 for f in folders) - len(ext) - 6
    name = name[: max(20, room)].rstrip(" .")
    return PurePosixPath(*folders, name + ext)


def _unique(rel: PurePosixPath, taken: set[str]) -> PurePosixPath:
    if str(rel).lower() not in taken:
        return rel
    n = 2
    while True:
        cand = rel.with_name(f"{rel.stem} ({n}){rel.suffix}")
        if str(cand).lower() not in taken:
            return cand
        n += 1


def organize(cfg: Config) -> None:
    conn = db.connect(cfg.db_path)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    rows = db.first_message_for_files(conn, "WHERE f.category IS NOT NULL").fetchall()
    taken = {str(r[0]).lower() for r in conn.execute(
        "SELECT organized_path FROM files WHERE organized_path IS NOT NULL")}

    placed = moved = missing = 0
    for i, r in enumerate(rows, 1):
        want = target_relpath(r, cfg)
        current = r["organized_path"]
        if current and PurePosixPath(current).parent == want.parent and \
                PurePosixPath(current).suffix == want.suffix:
            continue  # already in the right folder
        if current:
            taken.discard(current.lower())
        rel = _unique(want, taken)
        dest = cfg.output_dir / Path(*rel.parts)

        src = cfg.output_dir / Path(*PurePosixPath(current).parts) if current else Path(r["store_path"])
        if not src.exists():
            missing += 1
            if current:
                taken.add(current.lower())
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if current or cfg.organize_mode == "move":
            shutil.move(str(src), str(dest))
        else:
            shutil.copy2(str(src), str(dest))
        conn.execute("UPDATE files SET organized_path=? WHERE sha256=?", (str(rel), r["sha256"]))
        taken.add(str(rel).lower())
        if current:
            moved += 1
        else:
            placed += 1
        if i % 200 == 0:
            conn.commit()
            print(f"   {i:,}/{len(rows):,}", flush=True)
    conn.commit()
    _remove_empty_dirs(cfg.output_dir)
    print(f"Organised into {cfg.output_dir}: {placed:,} placed, {moved:,} re-filed"
          + (f", {missing:,} missing (moved or deleted by hand?)" if missing else ""))


def _remove_empty_dirs(root: Path) -> None:
    for dirpath, _dirnames, _filenames in os.walk(root, topdown=False):
        p = Path(dirpath)
        if p != root and not any(p.iterdir()):
            try:
                p.rmdir()
            except OSError:
                pass
