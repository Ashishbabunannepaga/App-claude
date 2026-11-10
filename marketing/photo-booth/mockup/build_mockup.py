#!/usr/bin/env python3
"""Builds mockup/index.html (the concept pack) from template.html and the print artwork in ../print.

Run ../print/build.py first; the Concept A elevation and the file thumbnails reuse its real artwork.
Usage: python3 build_mockup.py
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PRINT = HERE.parent / "print"
sys.path.insert(0, str(PRINT))
import build as art  # noqa: E402

WARM = "#FFC46B"  # 2700 K LED glow, drawing only

BOM = [
    ("SEG backdrop frame", "2400 × 1500, 80 mm aluminium profile, 2 stabiliser feet, tool-free corners", "1", 11000, 15000),
    ("Backdrop fabric", "Dye-sub on matte 230 gsm stretch polyester, silicone edge, fire-retardant, 3.6 m²", "1", 5500, 8000),
    ("Header sign", "2400 × 300 × 80 box, 3 mm ACP, matte white vinyl + matte laminate, splits in 2 for transport", "1", 6000, 9000),
    ("Warm LED edge lighting", "2700 K COB 12 V strip ~13 m in aluminium channel with opal diffuser (header halo + backdrop sides)", "1 set", 4500, 7000),
    ("Driver and dimmer", "12 V 10 A SMPS in enclosure, inline dimmer, 5 m extension, cable covers", "1", 2000, 3000),
    ("Floor decal", "1200 × 600 printed vinyl, anti-slip matte laminate", "2", 1200, 2000),
    ("Phone-spot sticker", "300 mm round, anti-slip", "2", 300, 500),
    ("Sticker wall", "600 × 1800, 3 mm ACP, matte laminate, A-frame stand", "1", 4000, 6000),
    ("Stickers", "80 mm round, matte vinyl, kiss-cut, 6 designs", "600", 2400, 4200),
    ("Policy report card prop", "600 × 420 + handle, 5 mm sunboard, printed, matte laminate, router-cut", "3", 1500, 2400),
    ("Phone stand", "1.8 m tripod, universal phone clamp, 25 cm warm ring light, Bluetooth shutter", "1", 2000, 3500),
    ("Transport bags", "Padded bags for frame and fabric, flat case for ACP panels", "1 set", 3000, 5000),
    ("Pre-press and proof", "Colour proof on the real fabric and ACP, test assembly", "1", 2000, 4000),
]


def inr(n):
    """Indian digit grouping: 131000 -> 1,31,000."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
    return f"{head},{tail}"


def inner(svg):
    """Body of an exported print SVG, without its root tag or cut-line ids."""
    body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", svg.strip())
    return body.replace(' id="cut"', "")


def panel(name):
    return inner((PRINT / "out" / "print" / f"{name}.svg").read_text())


def person(cx, h=1700, floor=1800, cls="person"):
    r = h * 0.068
    top = floor - h
    sh = h * 0.13  # half shoulder width
    return (
        f'<g class="{cls}"><circle cx="{cx}" cy="{top + r}" r="{r}"/>'
        f'<path d="M{cx - sh} {top + 2.3 * r + 40} Q{cx - sh} {top + 2.3 * r} {cx - sh + 50} {top + 2.3 * r} '
        f'H{cx + sh - 50} Q{cx + sh} {top + 2.3 * r} {cx + sh} {top + 2.3 * r + 40} V{floor - h * 0.47} '
        f'H{cx + sh * 0.7} V{floor} H{cx + 20} V{floor - h * 0.4} H{cx - 20} V{floor} H{cx - sh * 0.7} '
        f'V{floor - h * 0.47} H{cx - sh} Z"/></g>'
    )


def dim_h(x1, x2, y, label):
    t = 30
    return (
        f'<path class="dimline" d="M{x1} {y} H{x2} M{x1} {y - t} V{y + t} M{x2} {y - t} V{y + t}"/>'
        f'<text class="dimtext" x="{(x1 + x2) / 2}" y="{y - 24}" text-anchor="middle">{label}</text>'
    )


def dim_v(x, y1, y2, label):
    t = 30
    return (
        f'<path class="dimline" d="M{x} {y1} V{y2} M{x - t} {y1} H{x + t} M{x - t} {y2} H{x + t}"/>'
        f'<text class="dimtext" x="{x - 24}" y="{(y1 + y2) / 2}" text-anchor="middle" '
        f'transform="rotate(-90 {x - 24} {(y1 + y2) / 2})">{label}</text>'
    )


def glow_defs(id_):
    return (
        f'<defs><filter id="{id_}" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feGaussianBlur stdDeviation="18"/></filter></defs>'
    )


def svg(viewbox, body, label):
    return f'<svg viewBox="{viewbox}" role="img" aria-label="{label}">{body}</svg>'


def elev_a():
    b = [glow_defs("ga")]
    b.append(f'<rect x="-40" y="-40" width="2480" height="1840" fill="none" stroke="{WARM}" stroke-width="40" filter="url(#ga)" opacity=".85"/>')
    b.append(f'<svg x="0" y="0" width="2400" height="300" viewBox="0 0 2400 300">{panel("02-header-sign-2400x300")}</svg>')
    b.append(f'<svg x="0" y="300" width="2400" height="1500" viewBox="0 0 2400 1500">{panel("01-backdrop-2400x1500")}</svg>')
    b.append(f'<rect x="200" y="1780" width="400" height="20" fill="#0B2B2E"/><rect x="1800" y="1780" width="400" height="20" fill="#0B2B2E"/>')
    b.append('<g opacity=".92">' + person(1020, 1650) + person(1380, 1720) + "</g>")
    b.append('<line class="floor" x1="-400" y1="1800" x2="2800" y2="1800"/>')
    b.append(dim_h(0, 2400, 1960, "2400"))
    b.append(dim_v(-130, 0, 1800, "1800"))
    b.append(dim_v(-300, 0, 300, "300"))
    b.append(dim_v(-300, 300, 1800, "1500"))
    b.append(dim_v(2560, 410, 1800, "1390 frame"))
    return svg("-420 -120 3140 2140", "".join(b), "Concept A front elevation")


def plan_a():
    b = ['<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
         f'<path d="M0 0 L10 5 L0 10 Z" fill="{art.GOLD}"/></marker></defs>']
    b.append(f'<rect x="0" y="0" width="2400" height="80" fill="{art.INK}"/>')
    b.append(f'<rect x="200" y="-160" width="400" height="400" fill="none" stroke="{art.INK}" stroke-width="12" opacity=".5"/>')
    b.append(f'<rect x="1800" y="-160" width="400" height="400" fill="none" stroke="{art.INK}" stroke-width="12" opacity=".5"/>')
    b.append(f'<rect x="1840" y="80" width="480" height="40" fill="{art.PAPER}" stroke="{art.INK}" stroke-width="8"/>')
    b.append('<text class="lbl" x="2080" y="200" text-anchor="middle">QR plate</text>')
    b.append(f'<rect x="600" y="260" width="1200" height="600" fill="none" stroke="{art.GOLD}" stroke-width="16"/>')
    b.append('<text class="lbl" x="1200" y="580" text-anchor="middle">Stand here</text>')
    b.append(f'<circle cx="1200" cy="1880" r="150" fill="{art.GOLD}"/>')
    b.append('<text class="lbl" x="1200" y="2110" text-anchor="middle">Phone stand</text>')
    b.append(f'<rect x="2900" y="140" width="600" height="60" fill="{art.INK}"/>')
    b.append('<text class="lbl" x="3200" y="300" text-anchor="middle">Sticker wall</text>')
    b.append(dim_v(-120, 80, 1880, "1800"))
    b.append(dim_h(0, 3500, 2380, "≈ 3600 footprint"))
    b.append(f'<path d="M-200 2200 C 200 1400, 500 1100, 800 900 M1500 900 C 1800 700, 2000 500, 2050 330 M2400 500 C 2700 650, 2900 500, 3050 330" '
             f'fill="none" stroke="{art.GOLD}" stroke-width="18" stroke-dasharray="40 30" marker-end="url(#arr)"/>')
    return svg("-420 -260 4100 2760", "".join(b), "Concept A plan view")


def elev_b():
    b = [glow_defs("gb")]
    b.append(f'<rect x="0" y="0" width="2400" height="300" fill="{art.PAPER}" stroke="{art.INK}" stroke-width="6"/>')
    b.append(f'<rect x="0" y="286" width="2400" height="14" fill="{art.GOLD}"/>')
    b.append(art.logo(800, 65, 800, 170))
    b.append(f'<rect x="450" y="300" width="1500" height="1500" class="venue"/>')
    b.append(f'<rect x="450" y="300" width="1500" height="1500" fill="{art.INK}" opacity=".55"/>')
    b.append(person(1020, 1650) + person(1380, 1720))
    b.append(f'<rect x="465" y="315" width="1470" height="1485" fill="none" stroke="{WARM}" stroke-width="40" filter="url(#gb)"/>')
    b.append(f'<rect x="450" y="300" width="1500" height="1500" fill="none" stroke="{art.GOLD}" stroke-width="16"/>')
    for x in (0, 1950):
        b.append(f'<rect x="{x}" y="300" width="450" height="1500" fill="{art.INK}"/>')
    b.append(f'<g transform="rotate(-90 300 1050)">'
             + art.text(300, 1050, "Check your policy.", 110, art.WHITE, 900, art.DISPLAY, "middle")
             + art.text(300, 1170, "Share your win.", 110, art.GOLD, 900, art.DISPLAY, "middle") + "</g>")
    b.append(f'<rect x="2000" y="700" width="350" height="520" rx="18" fill="{art.PAPER}"/>')
    b.append(art.qr(2025, 725, 300))
    b.append(art.text(2175, 1090, "Scan to check", 34, art.INK, 800, art.DISPLAY, "middle"))
    b.append(art.text(2175, 1140, "your policy", 34, art.INK, 800, art.DISPLAY, "middle"))
    b.append(art.text(2175, 1190, "capitupindia.com", 26, art.TEAL, 700, art.BODY, "middle"))
    b.append('<line class="floor" x1="-400" y1="1800" x2="2800" y2="1800"/>')
    b.append(dim_h(0, 2400, 1960, "2400"))
    b.append(dim_h(450, 1950, 1700, "1500 opening"))
    b.append(dim_v(-130, 0, 1800, "1800"))
    b.append(dim_v(-300, 0, 300, "300"))
    b.append(dim_h(1950, 2400, -40, "450"))
    return svg("-420 -160 3140 2180", "".join(b), "Concept B front elevation")


def elev_c():
    W, H, R = 1100, 1800, 120
    wx, wy, ww, wh = 120, 150, 860, 1100
    b = [glow_defs("gc")]
    b.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" class="venue"/>')
    b.append(person(550, 1720))
    b.append(f'<rect x="-10" y="-10" width="{W + 20}" height="{H + 20}" rx="{R}" fill="none" stroke="{WARM}" stroke-width="40" filter="url(#gc)"/>')
    shell = (f"M{R} 0 H{W - R} Q{W} 0 {W} {R} V{H - R} Q{W} {H} {W - R} {H} H{R} Q0 {H} 0 {H - R} V{R} Q0 0 {R} 0 Z "
             f"M{wx + 30} {wy} H{wx + ww - 30} Q{wx + ww} {wy} {wx + ww} {wy + 30} V{wy + wh - 30} Q{wx + ww} {wy + wh} "
             f"{wx + ww - 30} {wy + wh} H{wx + 30} Q{wx} {wy + wh} {wx} {wy + wh - 30} V{wy + 30} Q{wx} {wy} {wx + 30} {wy} Z")
    b.append(f'<path d="{shell}" fill="{art.INK}" fill-rule="evenodd"/>')
    b.append(f'<rect x="300" y="35" width="500" height="90" rx="12" fill="{art.PAPER}"/>')
    b.append(art.logo(320, 45, 460, 70))
    b.append(art.text(550, 1360, "Check your policy.", 78, art.WHITE, 900, art.DISPLAY, "middle"))
    b.append(art.text(550, 1450, "Share your win.", 78, art.GOLD, 900, art.DISPLAY, "middle"))
    b.append(f'<rect x="230" y="1510" width="640" height="110" rx="55" fill="{art.GOLD}"/>')
    b.append(art.check(300, 1535, 60, art.INK, 12))
    b.append(art.text(590, 1585, "Policy checked", 50, art.INK, 800, art.DISPLAY, "middle"))
    b.append(art.text(550, 1710, "capitupindia.com", 34, art.GOLD, 700, art.BODY, "middle"))
    b.append('<line class="floor" x1="-400" y1="1800" x2="1500" y2="1800"/>')
    b.append(dim_h(0, W, 1960, "1100"))
    b.append(dim_v(-130, 0, H, "1800"))
    b.append(dim_v(1260, wy, wy + wh, "1100 window"))
    return svg("-420 -120 1840 2140", "".join(b), "Concept C front elevation")


FILE_LABELS = {
    "01-backdrop-2400x1500": ("Backdrop fabric", "2400 × 1500 + 25 bleed · SEG dye-sub"),
    "02-header-sign-2400x300": ("Top sign", "2400 × 300 + 5 bleed · vinyl on ACP"),
    "03-floor-decal-1200x600": ("Floor decal", "1200 × 600 + 3 bleed · anti-slip"),
    "04-phone-spot-300": ("Phone spot", "Ø 300 + 3 bleed · anti-slip"),
    "05-sticker-wall-600x1800": ("Sticker wall", "600 × 1800 + 5 bleed · ACP"),
    "06-sticker-sheet-a4": ("Sticker sheet", "A4, six Ø 80 kiss-cut"),
    "07-report-card-prop-600x420": ("Report card prop", "600 × 420 + handle · 5 mm sunboard"),
}


def files():
    out = []
    for name, (title, spec) in FILE_LABELS.items():
        raw = (PRINT / "out" / "print" / f"{name}.svg").read_text()
        vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
        out.append(
            f'<div class="file"><div class="art"><svg viewBox="{vb}" role="img" aria-label="{title}">{inner(raw)}</svg></div>'
            f"<b>{title}</b><span>{spec}</span><span><code>{name}.pdf</code></span></div>"
        )
    return "".join(out)


def bom_rows():
    rows = [
        f'<tr><td>{a}</td><td>{s}</td><td class="n">{q}</td><td class="n">{inr(lo)}</td><td class="n">{inr(hi)}</td></tr>'
        for a, s, q, lo, hi in BOM
    ]
    lo, hi = sum(r[3] for r in BOM), sum(r[4] for r in BOM)
    rows.append(f'<tr class="total"><td>Total per unit</td><td>before GST</td><td></td><td class="n">₹{inr(lo)}</td><td class="n">₹{inr(hi)}</td></tr>')
    return "\n        ".join(rows)


def main():
    page = (HERE / "template.html").read_text()
    for key, val in {
        "ELEV_A": elev_a(), "PLAN_A": plan_a(), "ELEV_B": elev_b(), "ELEV_C": elev_c(),
        "BOM_ROWS": bom_rows(), "FILES": files(),
    }.items():
        page = page.replace("{{" + key + "}}", val)
    (HERE / "index.html").write_text(page)
    lo, hi = sum(r[3] for r in BOM), sum(r[4] for r in BOM)
    print(f"index.html written · Concept A BOM ₹{inr(lo)}–₹{inr(hi)} before GST")


if __name__ == "__main__":
    main()
