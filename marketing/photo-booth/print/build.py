#!/usr/bin/env python3
"""Builds the print files for the CapitUp photo booth (Concept A, "The Frame").

Every panel is drawn at 1:1 in millimetres. Output:
  out/print/<panel>.svg   artwork with bleed, no guides (send the PDFs, not these, to the printer)
  out/proof/<panel>.svg   same artwork with trim (cyan) and safe-area (magenta) lines, for sign-off
  out/qr-capitupindia.svg the QR code on its own

The CapitUp logo is never redrawn here. Drop the approved vector master into logo/:
  logo/capitup-logo.svg   full-colour logo, tight-cropped (no empty margin)
and re-run. It is placed with its own aspect ratio inside each logo box, so its colours and internal
spacing stay exactly as supplied. Until the file exists, each logo box is a labelled placeholder.

Then run `node render_pdf.js` to turn out/print/*.svg into print-ready PDFs (fonts embedded).

Usage: pip install segno && python3 build.py
"""

import base64
import html
from pathlib import Path

import segno

HERE = Path(__file__).parent
OUT = HERE / "out"
LOGO = HERE / "logo" / "capitup-logo.svg"

# Brand tokens (replica/design/tokens.json, mobile/lib/app/theme/app_colors.dart).
INK = "#0B2B2E"  # matte base
GOLD = "#F5A81C"  # the one accent
TEAL = "#0B7A75"  # logo / URL only
PAPER = "#F6F8F7"  # light plates that carry the full-colour logo
WHITE = "#FFFFFF"
MUTED = "#55635F"

DISPLAY = "'Inter Display', 'Inter', sans-serif"
BODY = "'Inter', sans-serif"

URL = "https://capitupindia.com"  # APPROVAL: add UTM tags if marketing wants event tracking
TAGLINE = ("Check your policy.", "Share your win.")  # APPROVAL
HASHTAG = "#PolicyChecked"  # APPROVAL: check it is free and on-brand before printing


def esc(s):
    return html.escape(s, quote=True)


def text(x, y, s, size, fill, weight=800, family=DISPLAY, anchor="start", spacing=0, extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}" {extra}>{esc(s)}</text>'
    )


def check(x, y, size, color, stroke=None):
    """A tick drawn as a path, so it never depends on a font having the glyph."""
    sw = stroke or size * 0.16
    return (
        f'<path d="M{x} {y + size * 0.55} L{x + size * 0.38} {y + size * 0.9} L{x + size} {y + size * 0.12}" '
        f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def logo(x, y, w, h, label_color=INK):
    """The official logo fitted into a w x h box (aspect kept), or a labelled placeholder."""
    if LOGO.exists():
        data = base64.b64encode(LOGO.read_bytes()).decode()
        return (
            f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" '
            f'href="data:image/svg+xml;base64,{data}"/>'
        )
    fs = min(h * 0.22, w * 0.06)
    return (
        f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{label_color}" '
        f'stroke-width="{max(1, h * 0.012)}" stroke-dasharray="{h * 0.06} {h * 0.04}"/>'
        + text(x + w / 2, y + h / 2 - fs * 0.15, "OFFICIAL CAPITUP LOGO", fs, label_color, 700, BODY, "middle")
        + text(x + w / 2, y + h / 2 + fs * 1.1, f"max box {w:g} x {h:g} mm · do not redraw", fs * 0.7, label_color, 500, BODY, "middle")
        + "</g>"
    )


def qr(x, y, size, dark=INK):
    """QR code for URL, square of side `size` mm including a 4-module quiet zone."""
    code = segno.make(URL, error="q")
    m = code.matrix
    n = len(m)
    mod = size / (n + 8)
    parts = []
    for r, row in enumerate(m):
        for c, v in enumerate(row):
            if v:
                parts.append(f"M{x + (c + 4) * mod:.3f} {y + (r + 4) * mod:.3f}h{mod:.3f}v{mod:.3f}h-{mod:.3f}z")
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{WHITE}"/><path d="{"".join(parts)}" fill="{dark}"/>'


def corners(x, y, w, h, arm, sw, color):
    """Four L-shaped corner brackets: the selfie frame."""
    o = sw / 2
    pts = [
        (f"M{x + o} {y + arm} V{y + o} H{x + arm}"),
        (f"M{x + w - arm} {y + o} H{x + w - o} V{y + arm}"),
        (f"M{x + o} {y + h - arm} V{y + h - o} H{x + arm}"),
        (f"M{x + w - arm} {y + h - o} H{x + w - o} V{y + h - arm}"),
    ]
    return "".join(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="square"/>' for d in pts
    )


# ---------------------------------------------------------------- panels
# Each returns (finished_w, finished_h, bleed, safe, body_svg). Coordinates are in the finished panel's
# space (0,0 = top-left of the trimmed panel); the bleed is filled by drawing the background past the edges.


def backdrop():
    """SEG fabric, 2400 x 1500 finished. Floor is y = 1500."""
    W, H, B = 2400, 1500, 25
    s = [f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" fill="{INK}"/>']
    # Left column: tagline, chest height, beside the people (never behind them).
    lines = [("Check", WHITE), ("your", WHITE), ("policy.", WHITE), ("Share", GOLD), ("your", GOLD), ("win.", GOLD)]
    for i, (w, c) in enumerate(lines):
        s.append(text(70, 290 + i * 146, w, 142, c, 900, DISPLAY, spacing=-3))
    s.append(text(76, 1250, "We read the fine print,", 36, PAPER, 500, BODY))
    s.append(text(76, 1296, "so you don't have to.", 36, PAPER, 500, BODY))
    # Centre: the frame people stand in, 1100 wide (fits 2-3 adults shoulder to shoulder).
    fx, fy, fw, fh = 650, 110, 1100, 1390
    s.append(corners(fx, fy, fw, fh, 260, 44, GOLD))
    s.append(text(fx + fw / 2, fy + 70, HASHTAG, 46, GOLD, 700, BODY, "middle", 4))
    # Right column: light plate with the full-colour logo and the QR code, at scanning height.
    px, py, pw, ph = 1840, 110, 480, 860
    s.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="24" fill="{PAPER}"/>')
    s.append(logo(px + 50, py + 50, pw - 100, 140))
    s.append(f'<rect x="{px + 50}" y="{py + 230}" width="{pw - 100}" height="3" fill="{INK}" opacity=".15"/>')
    s.append(qr(px + 60, py + 270, 360))
    s.append(text(px + pw / 2, py + 702, "Scan to check", 44, INK, 800, DISPLAY, "middle"))
    s.append(text(px + pw / 2, py + 752, "your policy", 44, INK, 800, DISPLAY, "middle"))
    s.append(text(px + pw / 2, py + 812, "capitupindia.com", 32, TEAL, 700, BODY, "middle"))
    s.append(text(2080, 1060, "We don't sell insurance.", 26, PAPER, 500, BODY, "middle", extra='opacity=".75"'))
    return W, H, B, 50, "".join(s)


def header():
    """Top sign front, 2400 x 300 finished, matte white vinyl on ACP box."""
    W, H, B = 2400, 300, 5
    s = [f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" fill="{PAPER}"/>']
    s.append(f'<rect x="{-B}" y="{H - 14}" width="{W + 2 * B}" height="{14 + B}" fill="{GOLD}"/>')
    s.append(logo(W / 2 - 400, 60, 800, 170))
    s.append(text(2340, 175, "capitupindia.com", 34, TEAL, 700, BODY, "end"))
    s.append(text(60, 175, "Policy review, in plain words", 34, INK, 600, BODY))  # APPROVAL
    return W, H, B, 30, "".join(s)


def floor_decal():
    """Anti-slip floor vinyl, 1200 x 600, placed in front of the frame."""
    W, H, B = 1200, 600, 3
    s = [f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" rx="0" fill="{INK}"/>']
    s.append(corners(40, 40, W - 80, H - 80, 120, 24, GOLD))
    s.append(text(W / 2, 270, "Stand here.", 110, WHITE, 900, DISPLAY, "middle", -1))
    s.append(text(W / 2, 390, "Strike your best", 64, GOLD, 800, DISPLAY, "middle"))
    s.append(text(W / 2, 460, "policy-checked pose.", 64, GOLD, 800, DISPLAY, "middle"))
    return W, H, B, 40, "".join(s)


def phone_spot():
    """Round floor sticker, 300 diameter, 1.8 m in front of the frame, under the phone stand."""
    W, H, B = 300, 300, 3
    s = [f'<circle cx="150" cy="150" r="{150 + B}" fill="{GOLD}"/>']
    s.append(text(150, 140, "Phone", 52, INK, 900, DISPLAY, "middle"))
    s.append(text(150, 196, "goes here", 34, INK, 700, BODY, "middle"))
    return W, H, B, 20, "".join(s)


def sticker_wall():
    """Free-standing panel, 600 x 1800, matte laminated ACP. Visitors stick their stickers here."""
    W, H, B = 600, 1800, 5
    s = [f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" fill="{INK}"/>']
    s.append(f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{230 + B}" fill="{PAPER}"/>')
    s.append(logo(60, 50, 480, 130))
    s.append(text(50, 340, "Stick", 96, WHITE, 900, DISPLAY, spacing=-1))
    s.append(text(50, 440, "your win.", 96, GOLD, 900, DISPLAY, spacing=-1))
    s.append(text(52, 510, "What did your policy surprise you with?", 24, PAPER, 500, BODY))
    # A faint dot grid so the first stickers have somewhere to go.
    for r in range(11):
        for c in range(5):
            s.append(f'<circle cx="{90 + c * 105}" cy="{620 + r * 105}" r="5" fill="{GOLD}" opacity=".35"/>')
    s.append(text(W / 2, 1760, "capitupindia.com", 28, GOLD, 700, BODY, "middle"))
    return W, H, B, 30, "".join(s)


STICKERS = [
    ("Policy", "checked"),
    ("I read the", "fine print"),
    ("Sub-limits?", "Spotted."),
    ("Claim-", "ready"),
    ("Renewal", "sorted"),
    ("Adulting:", "insured"),
]


def sticker_sheet():
    """Six 80 mm round stickers on an A4 sheet. Kiss-cut on the dashed circles (cut path in `cut` group)."""
    W, H, B = 210, 297, 3
    s = [f'<rect x="{-B}" y="{-B}" width="{W + 2 * B}" height="{H + 2 * B}" fill="{WHITE}"/>']
    cuts = []
    for i, (a, b) in enumerate(STICKERS):
        cx, cy = 57 + (i % 2) * 96, 58 + (i // 2) * 92
        dark = i % 2 == 0
        bg, fg, acc = (INK, WHITE, GOLD) if dark else (GOLD, INK, INK)
        s.append(f'<circle cx="{cx}" cy="{cy}" r="41.5" fill="{bg}"/>')  # 1.5 mm bleed past the cut
        s.append(check(cx - 9, cy - 30, 18, acc))
        s.append(text(cx, cy + 4, a, 10.5, fg, 800, DISPLAY, "middle"))
        s.append(text(cx, cy + 17, b, 10.5, acc, 800, DISPLAY, "middle"))
        s.append(text(cx, cy + 30, "CapitUp", 5, fg, 700, BODY, "middle", 0.6, 'opacity=".8"'))  # APPROVAL: wordmark text, not the logo
        cuts.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="none" stroke="#FF00FF" stroke-width=".25"/>')
    s.append(f'<g id="cut" data-note="CutContour: spot colour, do not print">{"".join(cuts)}</g>')
    return W, H, B, 8, "".join(s)


def report_card():
    """Hand-held prop, 600 x 420 card plus a 120 x 160 handle, 5 mm sunboard, router cut to shape."""
    W, H, B = 600, 580, 3
    rows = [
        ("Hospital room rent", "Checked"),
        ("Waiting periods", "Checked"),
        ("Co-pay & sub-limits", "Checked"),
        ("Renewal date", "Reminder set"),
    ]
    shape = "M24 0 H576 Q600 0 600 24 V396 Q600 420 576 420 H360 V580 H240 V420 H24 Q0 420 0 396 V24 Q0 0 24 0 Z"
    s = [f'<path d="{shape}" fill="{WHITE}" stroke="{WHITE}" stroke-width="{2 * B}"/>']
    s.append(f'<path d="M0 24 Q0 0 24 0 H576 Q600 0 600 24 V96 H0 Z" fill="{INK}"/>')
    s.append(text(32, 64, "MY POLICY REPORT", 30, WHITE, 900, DISPLAY, spacing=2))
    s.append(f'<rect x="388" y="20" width="192" height="56" rx="8" fill="{PAPER}"/>')
    s.append(logo(398, 26, 172, 44))
    for i, (k, v) in enumerate(rows):
        y = 150 + i * 62
        s.append(text(32, y, k, 26, INK, 600, BODY))
        s.append(check(366, y - 22, 26, TEAL, 5))
        s.append(text(404, y, v, 24, TEAL, 700, BODY))
        s.append(f'<rect x="32" y="{y + 20}" width="536" height="1.5" fill="{INK}" opacity=".12"/>')
    s.append(
        f'<g transform="rotate(-6 465 388)"><rect x="380" y="362" width="170" height="52" rx="8" fill="none" '
        f'stroke="{GOLD}" stroke-width="6"/>' + text(465, 400, "CHECKED", 28, GOLD, 900, DISPLAY, "middle", 3) + "</g>"
    )
    s.append(text(32, 404, "Sample prop. Not a real policy.", 16, MUTED, 500, BODY))
    s.append(f'<rect x="240" y="420" width="120" height="160" fill="{GOLD}"/>')
    s.append(f'<path id="cut" d="{shape}" fill="none" stroke="#FF00FF" stroke-width=".5"/>')
    return W, H, B, 15, "".join(s)


PANELS = {
    "01-backdrop-2400x1500": backdrop,
    "02-header-sign-2400x300": header,
    "03-floor-decal-1200x600": floor_decal,
    "04-phone-spot-300": phone_spot,
    "05-sticker-wall-600x1800": sticker_wall,
    "06-sticker-sheet-a4": sticker_sheet,
    "07-report-card-prop-600x420": report_card,
}


def wrap(W, H, B, safe, body, guides):
    g = ""
    if guides:
        g = (
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#00B7EB" stroke-width="{max(.5, W / 1200)}"/>'
            f'<rect x="{safe}" y="{safe}" width="{W - 2 * safe}" height="{H - 2 * safe}" fill="none" stroke="#FF00FF" '
            f'stroke-width="{max(.5, W / 1200)}" stroke-dasharray="{W / 120} {W / 200}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2 * B}mm" height="{H + 2 * B}mm" '
        f'viewBox="{-B} {-B} {W + 2 * B} {H + 2 * B}">{body}{g}</svg>\n'
    )


def main():
    for d in ("print", "proof"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for name, fn in PANELS.items():
        W, H, B, safe, body = fn()
        (OUT / "print" / f"{name}.svg").write_text(wrap(W, H, B, safe, body, False))
        (OUT / "proof" / f"{name}.svg").write_text(wrap(W, H, B, safe, body, True))
        print(f"{name}: {W} x {H} mm finished, {B} mm bleed, {safe} mm safe area")
    (OUT / "qr-capitupindia.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="360mm" height="360mm" viewBox="0 0 360 360">{qr(0, 0, 360)}</svg>\n'
    )
    print("logo:", "embedded from " + str(LOGO.relative_to(HERE)) if LOGO.exists() else "PLACEHOLDER (logo/capitup-logo.svg missing)")


if __name__ == "__main__":
    main()
