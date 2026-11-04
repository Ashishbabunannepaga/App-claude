"""Step 1 - read desktop Outlook (Windows only) and pull out every attachment.

Talks to the Outlook program that is already installed and signed in, through
Windows COM (the same interface Outlook's own VBA macros use). It only READS:
no email is moved, deleted, changed or marked as read.

Every mailbox and every .pst file that is open in Outlook is included, so
open old archive PSTs first (File > Open & Export > Open Outlook Data File).
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from . import db
from .config import Config
from .store import add_file, add_message, clean_ext

OL_MAIL = 43                      # olMail item class
OL_MAIL_FOLDER = 0                # olMailItem default item type
ATT_BY_VALUE, ATT_EMBEDDED = 1, 5  # olByValue, olEmbeddeditem (attached .msg)
PR_ATTACH_CONTENT_ID = "http://schemas.microsoft.com/mapi/proptag/0x3712001F"
PR_ATTACHMENT_HIDDEN = "http://schemas.microsoft.com/mapi/proptag/0x7FFE000B"
HAS_ATTACHMENT_FILTER = '@SQL="urn:schemas:httpmail:hasattachment" = 1'
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emz", ".wmz", ".tif", ".tiff", ".webp"}


def _com_dt(value) -> datetime:
    # pywin32 returns a timezone-aware pywintypes datetime; keep local wall time.
    return datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)


def _smtp(address_entry, fallback: str) -> str:
    if fallback and "@" in fallback:
        return fallback
    try:
        user = address_entry.GetExchangeUser()
        if user is not None and user.PrimarySmtpAddress:
            return user.PrimarySmtpAddress
    except Exception:
        pass
    return fallback or ""


def _sender(item) -> str:
    try:
        if item.SenderEmailType == "EX":
            return _smtp(item.Sender, "")
    except Exception:
        pass
    try:
        return item.SenderEmailAddress or ""
    except Exception:
        return ""


OL_TO, OL_CC = 1, 2


def _recipients(item) -> tuple[list[str], list[str], list[str]]:
    """(everyone, To, CC) as SMTP addresses."""
    every, to, cc = [], [], []
    try:
        for i in range(1, item.Recipients.Count + 1):
            r = item.Recipients.Item(i)
            addr = _smtp(r.AddressEntry, r.Address or "")
            every.append(addr)
            if r.Type == OL_TO:
                to.append(addr)
            elif r.Type == OL_CC:
                cc.append(addr)
    except Exception:
        pass
    return every, to, cc


def _skip_attachment(att, cfg: Config) -> bool:
    try:
        if att.Type not in (ATT_BY_VALUE, ATT_EMBEDDED):
            return True
        name = att.FileName or ""
    except Exception:
        return True
    ext = clean_ext(name)
    if ext in cfg.skip_extensions:
        return True
    if att.Type == ATT_EMBEDDED:
        return False
    pa = att.PropertyAccessor
    try:
        if pa.GetProperty(PR_ATTACHMENT_HIDDEN):
            return True
    except Exception:
        pass
    if ext in IMAGE_EXTS:
        try:
            size_kb = att.Size / 1024
        except Exception:
            size_kb = 0
        if size_kb < cfg.min_image_kb:
            return True
        try:  # inline picture in the body (signature, banner)
            if pa.GetProperty(PR_ATTACH_CONTENT_ID):
                return True
        except Exception:
            pass
    return False


def _walk(folder, cfg: Config, path: str = ""):
    name = folder.Name
    if name.lower() in cfg.skip_folders:
        return
    here = f"{path}/{name}" if path else name
    try:
        is_mail = folder.DefaultItemType == OL_MAIL_FOLDER
    except Exception:
        is_mail = False
    if is_mail:
        yield folder, here
    try:
        subs = folder.Folders
        for i in range(1, subs.Count + 1):
            yield from _walk(subs.Item(i), cfg, here)
    except Exception:
        return


def extract(cfg: Config, since: datetime | None = None, until: datetime | None = None,
            limit: int | None = None) -> None:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise SystemExit(
            "This step needs Windows with Outlook and the 'pywin32' package.\n"
            "Run setup.bat first. (To try the tool without Outlook, run: demo)"
        )

    pythoncom.CoInitialize()
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")

    conn = db.connect(cfg.db_path)
    tmp_dir = cfg.work_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cfg.store_dir.mkdir(parents=True, exist_ok=True)
    log_path = cfg.work_dir / "extract-errors.log"

    done = {r[0] for r in conn.execute("SELECT entry_id FROM messages")}
    stats = dict(emails=0, skipped=0, files=0, new_files=0, dupes=0, errors=0, bytes=0)
    started = time.time()
    include = {s.lower() for s in cfg.include_stores}

    def report(final=False):
        mins = (time.time() - started) / 60
        print(f"{'DONE' if final else '...'} emails {stats['emails']:,} | "
              f"attachments {stats['files']:,} (new {stats['new_files']:,}, "
              f"duplicates {stats['dupes']:,}) | {stats['bytes'] / 1e9:.2f} GB new | "
              f"already done {stats['skipped']:,} | errors {stats['errors']} | {mins:.1f} min",
              flush=True)

    with open(log_path, "a", encoding="utf-8") as log:
        for s in range(1, ns.Stores.Count + 1):
            store = ns.Stores.Item(s)
            store_name = store.DisplayName
            if include and store_name.lower() not in include:
                continue
            print(f"\n=== Mailbox / data file: {store_name}")
            try:
                root = store.GetRootFolder()
            except Exception as exc:
                print(f"   cannot open: {exc}")
                continue

            for folder, fpath in _walk(root, cfg):
                try:
                    items = folder.Items
                    try:
                        items = items.Restrict(HAS_ATTACHMENT_FILTER)
                    except Exception:
                        pass
                    items.Sort("[ReceivedTime]", True)   # newest first
                    count = items.Count
                except Exception as exc:
                    log.write(f"{fpath}\tfolder error\t{exc}\n")
                    continue
                if count == 0:
                    continue
                print(f"   {fpath}: {count:,} emails with attachments")

                item = items.GetFirst()
                while item is not None:
                    if limit and stats["emails"] >= limit:
                        report(final=True)
                        return
                    try:
                        if item.Class != OL_MAIL:
                            raise StopIteration
                        received = _com_dt(item.ReceivedTime)
                        if until and received > until:
                            raise StopIteration
                        if since and received < since:
                            break                      # sorted newest first
                        entry_id = item.EntryID
                        if entry_id in done:
                            stats["skipped"] += 1
                            raise StopIteration
                        _process_item(conn, cfg, item, entry_id, store_name, fpath,
                                      received, tmp_dir, stats)
                        done.add(entry_id)
                        stats["emails"] += 1
                        if stats["emails"] % 50 == 0:
                            conn.commit()
                        if stats["emails"] % 500 == 0:
                            report()
                    except StopIteration:
                        pass
                    except Exception as exc:
                        stats["errors"] += 1
                        try:
                            subj = item.Subject
                        except Exception:
                            subj = "?"
                        log.write(f"{fpath}\t{subj}\t{exc}\n")
                    item = items.GetNext()
                conn.commit()
    conn.commit()
    report(final=True)
    if stats["errors"]:
        print(f"Some emails could not be read - see {log_path}")


def _process_item(conn, cfg, item, entry_id, store_name, fpath, received, tmp_dir, stats):
    saved = []
    atts = item.Attachments
    for i in range(1, atts.Count + 1):
        att = atts.Item(i)
        if _skip_attachment(att, cfg):
            continue
        name = att.FileName or f"attachment{i}"
        if att.Type == ATT_EMBEDDED and not name.lower().endswith(".msg"):
            name += ".msg"
        tmp = tmp_dir / f"att{i}{clean_ext(name)}"
        att.SaveAsFile(str(tmp))
        saved.append((tmp, name))

    try:
        body = item.Body or ""
    except Exception:
        body = ""
    every, to, cc = _recipients(item)
    add_message(
        conn, entry_id=entry_id, store=store_name, folder=fpath,
        subject=item.Subject or "", sender_name=item.SenderName or "",
        sender_email=_sender(item), recipients=every, to=to, cc=cc,
        received=received.isoformat(), body=body,
    )
    for tmp, name in saved:
        size = tmp.stat().st_size
        _sha, is_new = add_file(conn, cfg, tmp, name, entry_id)
        stats["files"] += 1
        if is_new:
            stats["new_files"] += 1
            stats["bytes"] += size
        else:
            stats["dupes"] += 1
