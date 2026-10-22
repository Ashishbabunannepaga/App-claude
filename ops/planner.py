#!/usr/bin/env python3
"""Daily planner: ranks the backlog, writes today's plan, closes the day and rolls unfinished work forward.

    python3 ops/planner.py plan   [--date YYYY-MM-DD] [--capacity 5]
    python3 ops/planner.py close  [--date YYYY-MM-DD]
    python3 ops/planner.py add "title" --project app --priority P1 [--due YYYY-MM-DD] [--note "..."]
    python3 ops/planner.py list

Standard library only. Files: ops/backlog.md (source of truth), ops/daily/<date>.md (plan + day report).
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

OPS = Path(__file__).resolve().parent
BACKLOG = OPS / "backlog.md"
DAILY = OPS / "daily"
LINE = re.compile(r"^- \[(?P<box>[ x!])\] (?P<rest>.+)$")
BASE = {"P0": 100, "P1": 60, "P2": 30, "P3": 10}


class Task:
    def __init__(self, box, id, pri, project, title, due, carried, note):
        self.box, self.id, self.pri, self.project = box, id, pri, project
        self.title, self.due, self.carried, self.note = title, due, carried, note

    @classmethod
    def parse(cls, line):
        m = LINE.match(line)
        if not m:
            return None
        parts = [p.strip() for p in m["rest"].split("|")]
        if len(parts) < 4:
            return None
        due, carried, note = None, 0, ""
        for p in parts[4:]:
            if p.startswith("due="):
                due = dt.date.fromisoformat(p[4:]) if p[4:] else None
            elif p.startswith("carried="):
                carried = int(p[8:] or 0)
            else:
                note = p
        return cls(m["box"], parts[0], parts[1], parts[2], parts[3], due, carried, note)

    def render(self):
        bits = [self.id, self.pri, self.project, self.title]
        if self.due:
            bits.append(f"due={self.due.isoformat()}")
        bits.append(f"carried={self.carried}")
        bits.append(self.note)
        return f"- [{self.box}] " + " | ".join(bits)

    def score(self, today):
        s = BASE.get(self.pri, 30) + min(self.carried, 6) * 6
        if self.due:
            days = (self.due - today).days
            if days < 0:
                s += 60 + min(-days, 10) * 2
            elif days <= 2:
                s += 40
            elif days <= 7:
                s += 20
            elif days <= 14:
                s += 8
            elif days > 30:
                s -= 40  # far-off deadline: don't crowd out near-term work
        return s

    def why(self, today):
        r = [self.pri]
        if self.due:
            d = (self.due - today).days
            r.append(f"OVERDUE {-d}d" if d < 0 else "due today" if d == 0 else f"due in {d}d")
        if self.carried:
            r.append(f"carried {self.carried}x")
        return ", ".join(r)


def load():
    lines = BACKLOG.read_text().splitlines()
    return lines, [(i, Task.parse(l)) for i, l in enumerate(lines)]


def save(lines, parsed):
    for i, t in parsed:
        if t:
            lines[i] = t.render()
    BACKLOG.write_text("\n".join(lines) + "\n")


def day(args):
    return dt.date.fromisoformat(args.date) if args.date else dt.date.today()


def cmd_plan(args):
    today = day(args)
    _, parsed = load()
    open_ = sorted((t for _, t in parsed if t and t.box == " "), key=lambda t: -t.score(today))
    pick = open_[: args.capacity]
    must, should = pick[:3], pick[3:]
    blocked = [t for _, t in parsed if t and t.box == "!"]
    later = open_[args.capacity :]
    out = [f"# Plan for {today:%A %d %b %Y}", "", "## Must do (top 3)"]
    out += [f"- [ ] {t.id} · {t.title}  _({t.why(today)})_" for t in must] or ["- nothing open"]
    out += ["", "## Should do if time allows"]
    out += [f"- [ ] {t.id} · {t.title}  _({t.why(today)})_" for t in should] or ["- nothing"]
    out += ["", "## Watch list (next in line)"]
    out += [f"- {t.id} · {t.title} ({t.why(today)})" for t in later[:5]] or ["- nothing"]
    if blocked:
        out += ["", "## Blocked (needs you to unblock)"]
        out += [f"- {t.id} · {t.title}" for t in blocked]
    out += ["", "## Also did today (free text, filled at close)", "- ", ""]
    DAILY.mkdir(exist_ok=True)
    path = DAILY / f"{today.isoformat()}.md"
    if path.exists() and not args.force:
        sys.exit(f"{path} exists; use --force to regenerate")
    path.write_text("\n".join(out))
    print(path)
    print("NOTIFY:", notify_line(today, must))


def notify_line(today, must):
    if not must:
        return f"{today:%a %d %b}: backlog is clear."
    return f"Today's top {len(must)}: " + "; ".join(f"{t.id} {t.title}" for t in must)[:170]


def cmd_close(args):
    today = day(args)
    path = DAILY / f"{today.isoformat()}.md"
    if not path.exists():
        sys.exit(f"no plan at {path}; run plan first")
    text = path.read_text()
    planned = re.findall(r"^- \[(?P<b>[ x])\] (?P<id>CAP-\d+)", text, re.M)
    done_ids = [i for b, i in planned if b == "x"]
    miss_ids = [i for b, i in planned if b == " "]
    lines, parsed = load()
    by_id = {t.id: t for _, t in parsed if t}
    for i in done_ids:
        if i in by_id:
            by_id[i].box = "x"
    for i in miss_ids:
        if i in by_id and by_id[i].box == " ":
            by_id[i].carried += 1
    save(lines, parsed)
    also = re.search(r"## Also did today.*?\n(.*)", text, re.S)
    extra = [l for l in (also.group(1).splitlines() if also else []) if l.strip("- ").strip()]
    tomorrow = day(args) + dt.timedelta(days=1)
    nxt = sorted((t for t in by_id.values() if t.box == " "), key=lambda t: -t.score(tomorrow))[:5]
    rep = ["", f"# Day report {today.isoformat()}", "", f"Planned {len(planned)} · done {len(done_ids)} · carried {len(miss_ids)}", "", "## Done"]
    rep += [f"- {i} · {by_id[i].title}" for i in done_ids if i in by_id] + extra or ["- nothing"]
    rep += ["", "## Carried to tomorrow (carried count +1)"]
    rep += [f"- {i} · {by_id[i].title}" for i in miss_ids if i in by_id] or ["- nothing"]
    rep += ["", f"## Tomorrow's likely top 5 ({tomorrow:%a %d %b})"]
    rep += [f"- {t.id} · {t.title} ({t.why(tomorrow)})" for t in nxt]
    marker = "\n# Day report"
    path.write_text(text.split(marker)[0].rstrip() + "\n" + "\n".join(rep) + "\n")
    print(path)
    print(f"NOTIFY: Day done: {len(done_ids)}/{len(planned)} finished. Tomorrow starts with: "
          + "; ".join(t.id for t in nxt[:3]))


def cmd_add(args):
    lines, parsed = load()
    n = max([int(t.id.split("-")[1]) for _, t in parsed if t] + [0]) + 1
    t = Task(" ", f"CAP-{n:03d}", args.priority, args.project, args.title,
             dt.date.fromisoformat(args.due) if args.due else None, 0, args.note or "")
    lines.append(t.render())
    save(lines, parsed)
    print(t.render())


def cmd_list(args):
    today = dt.date.today()
    _, parsed = load()
    for t in sorted((t for _, t in parsed if t and t.box == " "), key=lambda t: -t.score(today)):
        print(f"{t.score(today):4d}  {t.id}  {t.title}  ({t.why(today)})")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "close"):
        p = sub.add_parser(name)
        p.add_argument("--date")
        if name == "plan":
            p.add_argument("--capacity", type=int, default=5)
            p.add_argument("--force", action="store_true")
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--project", default="app")
    a.add_argument("--priority", default="P2", choices=list(BASE))
    a.add_argument("--due")
    a.add_argument("--note")
    sub.add_parser("list")
    args = ap.parse_args()
    {"plan": cmd_plan, "close": cmd_close, "add": cmd_add, "list": cmd_list}[args.cmd](args)


if __name__ == "__main__":
    main()
