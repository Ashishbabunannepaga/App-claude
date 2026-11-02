"""SQLite database: one row per email, one per unique file, one per attachment link.

The database is what makes the tool resumable: an email already in `messages`
is never read from Outlook again, and a file already in `files` (same SHA-256)
is never stored twice.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    entry_id     TEXT PRIMARY KEY,
    store        TEXT,
    folder       TEXT,
    subject      TEXT,
    sender_name  TEXT,
    sender_email TEXT,
    recipients   TEXT,      -- semicolon separated SMTP addresses
    received     TEXT,      -- ISO date-time
    body         TEXT,      -- first part of the body
    status       TEXT DEFAULT 'ok',   -- ok | error
    error        TEXT
);

CREATE TABLE IF NOT EXISTS files (
    sha256         TEXT PRIMARY KEY,
    ext            TEXT,
    size           INTEGER,
    store_path     TEXT,     -- where the extractor saved it
    organized_path TEXT,     -- where it now lives in output_dir (relative)
    text           TEXT,     -- first part of the document text (NULL = not read yet)
    category       TEXT,
    confidence     TEXT,     -- high | medium | low
    method         TEXT,     -- rules | ai | manual
    client         TEXT,
    insurer        TEXT,
    policy_no      TEXT,
    reason         TEXT
);

CREATE TABLE IF NOT EXISTS attachments (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id  TEXT NOT NULL REFERENCES messages(entry_id),
    sha256    TEXT NOT NULL REFERENCES files(sha256),
    filename  TEXT NOT NULL,
    UNIQUE(entry_id, sha256, filename)
);

CREATE INDEX IF NOT EXISTS ix_att_sha ON attachments(sha256);
CREATE INDEX IF NOT EXISTS ix_att_entry ON attachments(entry_id);
CREATE INDEX IF NOT EXISTS ix_files_cat ON files(category);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def first_message_for_files(conn: sqlite3.Connection, where: str = "", params: tuple = ()):
    """Each unique file joined with the earliest email it arrived in.

    Yields sqlite rows with file columns plus: filename, subject, sender_name,
    sender_email, recipients, received, body, folder, n_emails.
    """
    sql = f"""
    WITH first AS (
        SELECT a.sha256, a.filename, m.*,
               ROW_NUMBER() OVER (PARTITION BY a.sha256 ORDER BY m.received) AS rn,
               COUNT(*) OVER (PARTITION BY a.sha256) AS n_emails
        FROM attachments a JOIN messages m ON m.entry_id = a.entry_id
    )
    SELECT f.*, first.filename, first.subject, first.sender_name, first.sender_email,
           first.recipients, first.received, first.body, first.folder, first.n_emails
    FROM files f JOIN first ON first.sha256 = f.sha256 AND first.rn = 1
    {where}
    ORDER BY first.received
    """
    return conn.execute(sql, params)
