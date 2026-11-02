"""Saving attachments into the de-duplicated store and recording emails."""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
from pathlib import Path

from .config import Config


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if not ext or len(ext) > 10 or not ext[1:].isalnum():
        return ""
    return ext


def add_file(conn: sqlite3.Connection, cfg: Config, tmp_path: Path, filename: str,
             entry_id: str) -> tuple[str, bool]:
    """Move a freshly saved attachment into the store (unless it is a duplicate)
    and link it to its email. Returns (sha256, is_new)."""
    sha = sha256_of(tmp_path)
    ext = clean_ext(filename)
    row = conn.execute("SELECT sha256 FROM files WHERE sha256=?", (sha,)).fetchone()
    is_new = row is None
    if is_new:
        dest = cfg.store_dir / sha[:2] / f"{sha}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_path), str(dest))
        conn.execute(
            "INSERT INTO files(sha256, ext, size, store_path) VALUES (?,?,?,?)",
            (sha, ext, dest.stat().st_size, str(dest)),
        )
    else:
        tmp_path.unlink(missing_ok=True)
    conn.execute(
        "INSERT OR IGNORE INTO attachments(entry_id, sha256, filename) VALUES (?,?,?)",
        (entry_id, sha, filename),
    )
    return sha, is_new


def add_message(conn: sqlite3.Connection, *, entry_id: str, store: str, folder: str,
                subject: str, sender_name: str, sender_email: str, recipients: list[str],
                received: str, body: str, status: str = "ok", error: str | None = None) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO messages
           (entry_id, store, folder, subject, sender_name, sender_email, recipients,
            received, body, status, error)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (entry_id, store, folder, subject or "", sender_name or "", (sender_email or "").lower(),
         ";".join(r.lower() for r in recipients if r), received, (body or "")[:3000],
         status, error),
    )
