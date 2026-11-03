"""Mail Sorter command line.

    python -m mailsorter extract  [--days 30 | --since 2026-10-01] [--until ...] [--limit N]
    python -m mailsorter classify [--ai] [--redo]
    python -m mailsorter organize
    python -m mailsorter report
    python -m mailsorter all      [same options as extract] [--ai]
    python -m mailsorter import-review [--file "Attachments Index.xlsx"]
    python -m mailsorter status
    python -m mailsorter estimate (what the AI step would cost)
    python -m mailsorter ai       (run / resume only the AI step)
    python -m mailsorter demo     (fake mailbox - no Outlook needed)
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .config import load_config

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def _date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError("use the format YYYY-MM-DD, e.g. 2026-10-01")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mailsorter", description="Sort Outlook attachments for an insurance broker.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to config.yaml")
    p.add_argument("--demo", action="store_true",
                   help="use the separate demo folder instead of the real paths in config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    def extract_opts(sp):
        sp.add_argument("--since", type=_date, help="only emails on/after this date (YYYY-MM-DD)")
        sp.add_argument("--until", type=_date, help="only emails before this date (YYYY-MM-DD)")
        sp.add_argument("--days", type=int, help="only emails from the last N days")
        sp.add_argument("--limit", type=int, help="stop after this many new emails (for a quick test)")

    extract_opts(sub.add_parser("extract", help="step 1: save attachments from Outlook"))
    c = sub.add_parser("classify", help="step 2: decide categories")
    c.add_argument("--ai", action="store_true", help="also run the AI step (see config.yaml ai:)")
    c.add_argument("--redo", action="store_true", help="re-sort everything (keeps manual corrections)")
    sub.add_parser("organize", help="step 3: file into the shared-drive folders")
    sub.add_parser("report", help="step 4: Excel index + dashboard")
    a = sub.add_parser("all", help="steps 1-4 in one go")
    extract_opts(a)
    a.add_argument("--ai", action="store_true")
    r = sub.add_parser("import-review", help="read category corrections from the Excel file")
    r.add_argument("--file", type=Path)
    sub.add_parser("status", help="show what has been done so far")
    sub.add_parser("estimate", help="show what the AI step would cost for the emails read so far")
    sub.add_parser("ai", help="run (or resume) only the AI step")
    d = sub.add_parser("demo", help="build a fake mailbox to try the tool without Outlook")
    d.add_argument("--emails", type=int, default=400)

    args = p.parse_args(argv)
    if getattr(args, "days", None):
        args.since = datetime.now() - timedelta(days=args.days)
    cfg = load_config(args.config)
    if args.demo or args.cmd == "demo":
        base = Path(args.config).resolve().parent / "demo"
        cfg.work_dir, cfg.store_dir, cfg.output_dir = base / "work", base / "work" / "store", base / "output"
        print(f"[demo mode - using {base}]")
    if args.cmd in ("classify", "all") and getattr(args, "ai", False):
        cfg.ai_enabled = True
    use_ai = cfg.ai_enabled

    if args.cmd == "extract":
        from .outlook import extract
        extract(cfg, args.since, args.until, args.limit)
    elif args.cmd == "classify":
        from .classify import classify_all
        classify_all(cfg, use_ai=use_ai, redo=args.redo)
    elif args.cmd == "organize":
        from .organize import organize
        organize(cfg)
    elif args.cmd == "report":
        from .report import report
        report(cfg)
    elif args.cmd == "all":
        from .classify import classify_all
        from .organize import organize
        from .outlook import extract
        from .report import report
        print("STEP 1/4  Reading Outlook"); extract(cfg, args.since, args.until, args.limit)
        print("\nSTEP 2/4  Sorting"); classify_all(cfg, use_ai=use_ai)
        print("\nSTEP 3/4  Filing into folders"); organize(cfg)
        print("\nSTEP 4/4  Excel + dashboard"); report(cfg)
    elif args.cmd == "import-review":
        from .report import import_review
        import_review(cfg, args.file)
    elif args.cmd == "status":
        from . import db
        conn = db.connect(cfg.db_path)
        q = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
        print(f"Emails read:        {q('SELECT COUNT(*) FROM messages'):,}")
        print(f"Unique files:       {q('SELECT COUNT(*) FROM files'):,}  "
              f"({(q('SELECT COALESCE(SUM(size),0) FROM files') / 1e9):.2f} GB)")
        print(f"Attachments total:  {q('SELECT COUNT(*) FROM attachments'):,} (incl. duplicates)")
        print(f"Sorted:             {q('SELECT COUNT(*) FROM files WHERE category IS NOT NULL'):,}")
        print(f"Filed in folders:   {q('SELECT COUNT(*) FROM files WHERE organized_path IS NOT NULL'):,}")
        ai_done = q("SELECT COUNT(*) FROM messages WHERE ai_status='done'")
        ai_queued = q("SELECT COUNT(*) FROM messages WHERE ai_status='queued'")
        print(f"Read by AI:         {ai_done:,} emails  (waiting in a batch: {ai_queued:,})")
        for row in conn.execute("SELECT category, COUNT(*) FROM files WHERE category IS NOT NULL "
                                "GROUP BY category ORDER BY 2 DESC"):
            print(f"   {row[0]:<28} {row[1]:>8,}")
    elif args.cmd == "estimate":
        from . import db
        from .ai import print_estimate
        conn = db.connect(cfg.db_path)
        if not conn.execute("SELECT COUNT(*) FROM files WHERE category IS NOT NULL").fetchone()[0]:
            print("Nothing read yet - run the trial or full run first (with AI switched off it is free).")
            return 0
        for scope in ("all", "unsure"):
            print_estimate(cfg, conn, scope)
            print()
        done = conn.execute("SELECT COUNT(*) FROM messages WHERE ai_status='done'").fetchone()[0]
        if done:
            print(f"({done:,} emails were already read by the AI - they are not counted or charged again.)")
    elif args.cmd == "ai":
        from . import db
        from .ai import ai_pass
        ai_pass(cfg, db.connect(cfg.db_path))
    elif args.cmd == "demo":
        from .demo import make_demo
        make_demo(cfg, args.emails)
        print("Now run with --demo:  classify, organize, report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
