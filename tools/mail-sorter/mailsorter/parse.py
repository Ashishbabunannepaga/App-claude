"""Splits an email body into the newest message and the forwarded / quoted
messages underneath it, each with its own From, To, CC, Date and Subject.

Handles the common formats:
  Gmail / Google Workspace   ---------- Forwarded message ---------
                             From: Name <a@b.com>  Date: ...  Subject: ...  To: ...
  Outlook                    From: Name <a@b.com>  Sent: ...  To: ...  Cc: ...  Subject: ...
                             -----Original Message-----
  Replies                    On Mon, 3 Jun 2024 at 10:15, Name <a@b.com> wrote:
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

EMAIL_IN_TEXT = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
FWD_SUBJECT = re.compile(r"^\s*((re|aw|sv)\s*:\s*)*(fw|fwd|forward)\s*:", re.IGNORECASE)
FWD_MARKER = re.compile(r"(?im)^[ \t>]*-{2,}\s*(forwarded message|original message)\s*-{2,}[ \t]*$")
HEADER_LINE = re.compile(r"(?i)^[ \t>*]*(from|sent|date|to|cc|subject)[ \t]*:[ \t]*(.*)$")
WROTE_LINE = re.compile(r"(?im)^[ \t>]*on .{4,120}?(?:<([^>\s]+@[^>\s]+)>|([\w.%+'-]+@[\w.-]+\.\w+))?\s*wrote:\s*$")


@dataclass
class Part:
    sender: str = ""          # display text of From:
    sender_email: str = ""
    to: str = ""
    cc: str = ""
    date: str = ""
    subject: str = ""
    kind: str = "quoted"      # forwarded | quoted
    body: str = ""


@dataclass
class Parsed:
    newest: str
    parts: list[Part] = field(default_factory=list)
    is_forward: bool = False

    @property
    def forwarded(self) -> list[Part]:
        return [p for p in self.parts if p.kind == "forwarded"]

    def original_sender(self, ignore_domains: set[str]) -> str:
        """For a forward: the email address of whoever first wrote it
        (skipping our own staff)."""
        for p in self.forwarded or self.parts:
            em = p.sender_email.lower()
            if em and em.rsplit("@", 1)[-1] not in ignore_domains:
                return em
        return ""


def _first_email(text: str) -> str:
    m = EMAIL_IN_TEXT.search(text or "")
    return m.group(0).lower() if m else ""


def _header_block_at(lines: list[str], i: int) -> int:
    """If lines[i] starts an Outlook/Gmail header block (From: ... then Sent/Date
    and To/Subject within the next few lines), return how many lines it spans."""
    m = HEADER_LINE.match(lines[i])
    if not m or m.group(1).lower() != "from":
        return 0
    seen = {"from"}
    j = i + 1
    while j < len(lines) and j <= i + 8:
        h = HEADER_LINE.match(lines[j])
        if not h:
            if lines[j].strip() == "" and len(seen) >= 3:
                break
            if lines[j].strip() and not lines[j].startswith((" ", "\t")):
                break
            j += 1
            continue
        seen.add(h.group(1).lower())
        j += 1
    if ({"sent", "date"} & seen) and ({"to", "subject"} & seen):
        return j - i
    return 0


def parse_body(body: str, subject: str = "") -> Parsed:
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = body.split("\n")
    starts: list[tuple[int, int, str]] = []   # (line index, header lines, kind)
    marker_kind = None
    i = 0
    while i < len(lines):
        line = lines[i]
        mk = FWD_MARKER.match(line)
        if mk:
            marker_kind = "forwarded" if "forward" in mk.group(1).lower() else "quoted"
            span = _header_block_at(lines, i + 1) if i + 1 < len(lines) else 0
            starts.append((i, 1 + span, marker_kind))
            i += 1 + span
            marker_kind = None
            continue
        span = _header_block_at(lines, i)
        if span:
            starts.append((i, span, "quoted"))
            i += span
            continue
        if WROTE_LINE.match(line):
            starts.append((i, 1, "quoted"))
        i += 1

    if not starts:
        return Parsed(newest=body.strip(), is_forward=bool(FWD_SUBJECT.match(subject or "")))

    newest = "\n".join(lines[: starts[0][0]]).strip()
    is_forward = bool(FWD_SUBJECT.match(subject or "")) or any(k == "forwarded" for _, _, k in starts)
    parts: list[Part] = []
    for n, (idx, span, kind) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        header, text = lines[idx: idx + span], lines[idx + span: end]
        p = Part(kind=kind)
        for h in header:
            hm = HEADER_LINE.match(h)
            if hm:
                key, val = hm.group(1).lower(), hm.group(2).strip()
                if key == "from":
                    p.sender, p.sender_email = val, _first_email(val)
                elif key in ("sent", "date"):
                    p.date = val
                elif key in ("to", "cc", "subject"):
                    setattr(p, key, val)
            else:
                wm = WROTE_LINE.match(h)
                if wm:
                    p.sender_email = (wm.group(1) or wm.group(2) or "").lower()
                    p.sender = h.strip()
        # In a forward with an empty newest part, the first quoted block IS the forwarded mail
        if is_forward and n == 0 and kind == "quoted":
            p.kind = "forwarded"
        p.body = "\n".join(text).strip()
        parts.append(p)
    return Parsed(newest=newest, parts=parts, is_forward=is_forward)


def addresses(text: str) -> list[str]:
    return [e.lower() for e in EMAIL_IN_TEXT.findall(text or "")]
