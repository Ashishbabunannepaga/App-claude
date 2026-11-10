# CapitUp event photo booth

A freestanding 1.8 m (6 ft) photo booth for events, aimed at young and working professionals and Gen Z.
The design uses a matte ink base, gold as the one accent, warm 2700 K LED edge lighting and Inter, the font the app uses.

**Open [`mockup/index.html`](mockup/index.html)** for the full concept pack: three concept sketches drawn to scale with
dimensions, a plan view, materials and cost, the print files, the visitor flow and the approval list.

Anything marked **APPROVAL** below needs sign-off from CapitUp before it is printed.

## Contents

| path | what |
| --- | --- |
| `mockup/index.html` | Concept pack (built from `template.html` by `build_mockup.py`) |
| `print/out/print/*.pdf` | Print-ready files, 1:1 in mm, with bleed, fonts embedded. Send these to the printer. |
| `print/out/proof/*.pdf, *.png` | The same artwork with trim (cyan) and safe-area (magenta) lines, for sign-off |
| `print/out/qr-capitupindia.svg` | The QR code on its own (360 mm, error correction Q, opens https://capitupindia.com) |
| `print/logo/` | Put the official logo here (see below) |

## The logo (APPROVAL)

The official CapitUp logo file is not in this repository (`mobile/assets/brand/` holds only a README), so nothing here
redraws it. Every logo position is an exact-size, labelled box. To finish the files:

1. Put the approved, tight-cropped vector master at `print/logo/capitup-logo.svg`.
2. Run the build (below). The logo is placed at its own aspect ratio inside each box, so its colours and spacing stay
   exactly as supplied.

The logo always sits on a light `#F6F8F7` plate, because the teal in the logo is too dark to read on the ink background.
If CapitUp has an approved on-dark version, the plates can be dropped.

## Concepts

| | size (W × H × D, mm) | for | ₹ per unit, before GST |
| --- | --- | --- | --- |
| **A · The Frame** (recommended) | 2400 × 1800 × 400 | Fabric wall with a lit top sign and gold corner brackets around 1–3 people. Tagline on the left, logo and QR plate on the right. | 45,400 – 69,600 |
| B · The Portal | 2400 × 1800 × 600 | Walk-through arch with LED around the opening. The most premium option and the heaviest. | 87,000 – 1,31,000 |
| C · The Phone | 1100 × 1800 × 450 | Giant phone standee with the screen cut out. The cheapest option, fits 1–2 people. | 20,000 – 32,000 |

## Materials and cost, Concept A (per unit, indicative 2026 metro rates, before GST)

| item | spec | qty | ₹ low | ₹ high |
| --- | --- | --- | ---: | ---: |
| SEG backdrop frame | 2400 × 1500, 80 mm aluminium profile, 2 feet, tool-free | 1 | 11,000 | 15,000 |
| Backdrop fabric | dye-sub, matte 230 gsm stretch polyester, silicone edge, fire-retardant | 1 | 5,500 | 8,000 |
| Header sign | 2400 × 300 × 80, 3 mm ACP, matte white vinyl + matte laminate, 2-part | 1 | 6,000 | 9,000 |
| Warm LED edge lighting | 2700 K COB 12 V strip ~13 m in aluminium channel, opal diffuser | 1 set | 4,500 | 7,000 |
| Driver and dimmer | 12 V 10 A SMPS, inline dimmer, extension, cable covers | 1 | 2,000 | 3,000 |
| Floor decal | 1200 × 600, anti-slip matte laminate | 2 | 1,200 | 2,000 |
| Phone-spot sticker | 300 mm round, anti-slip | 2 | 300 | 500 |
| Sticker wall | 600 × 1800, 3 mm ACP, matte laminate, A-frame | 1 | 4,000 | 6,000 |
| Stickers | 80 mm round, matte vinyl, kiss-cut, 6 designs | 600 | 2,400 | 4,200 |
| Policy report card prop | 600 × 420 + handle, 5 mm sunboard, router-cut | 3 | 1,500 | 2,400 |
| Phone stand | 1.8 m tripod, phone clamp, 25 cm warm ring light, Bluetooth shutter | 1 | 2,000 | 3,500 |
| Transport bags | padded bags + flat case | 1 set | 3,000 | 5,000 |
| Pre-press and proof | colour proof on real materials, test assembly | 1 | 2,000 | 4,000 |
| **Total** | | | **45,400** | **69,600** |

With 18% GST the total is ₹53,600–₹82,100. It does not include transport, set-up labour or venue power. Each event uses
about ₹2,400–4,200 of stickers. Get 2–3 vendor quotes before ordering (APPROVAL: budget and vendor).

## Print files (Concept A)

| file | finished size (mm) | bleed | material |
| --- | --- | --- | --- |
| `01-backdrop-2400x1500` | 2400 × 1500 | 25 | SEG fabric |
| `02-header-sign-2400x300` | 2400 × 300 | 5 | vinyl on ACP |
| `03-floor-decal-1200x600` | 1200 × 600 | 3 | anti-slip floor vinyl |
| `04-phone-spot-300` | Ø 300 | 3 | anti-slip floor vinyl |
| `05-sticker-wall-600x1800` | 600 × 1800 | 5 | ACP, matte laminate |
| `06-sticker-sheet-a4` | 210 × 297, six Ø 80 | 3 | matte vinyl, kiss-cut (magenta `cut` layer) |
| `07-report-card-prop-600x420` | 600 × 420 card + 120 × 160 handle | 3 | 5 mm sunboard, router-cut (magenta `cut` layer) |

Text sizes on the backdrop: the tagline is set in 142 mm type (readable from about 30 m) and the QR caption in 44 mm
type. The QR plate's centre is about 1.1 m above the floor.

Colours are brand hex values from `replica/design/tokens.json`. CMYK starting points: ink ~C88 M52 Y55 K62,
gold ~C0 M38 Y92 K0, teal ~C88 M28 Y56 K12. Approve colour on a printed proof of the real fabric and ACP (APPROVAL).

### Rebuild

```bash
pip install segno
```

```bash
cd marketing/photo-booth && python3 print/build.py && node print/render_pdf.js && python3 mockup/build_mockup.py
```

`render_pdf.js` uses Playwright's Chromium and needs the Inter font installed so it can be embedded in the PDFs.

## How a visitor uses it

1. **Spot it.** The lit top sign is visible over the crowd. One host asks, "Want a photo?"
2. **Grab a prop.** The "My Policy Report" card is a sample, marked as one, and shows no real policy and no personal data.
3. **Stand in the frame.** Up to 3 people stand on the "Stand here" decal inside the gold brackets.
4. **Take the photo on their own phone.** The visitor clips their phone onto the stand over the "Phone goes here" spot,
   1.8 m from the frame, then uses the Bluetooth shutter or the timer. The photo stays on their phone, and CapitUp stores
   nothing.
5. **Share it.** They post with #PolicyChecked and tag CapitUp (APPROVAL: hashtag and handle).
6. **Scan the QR code.** It is on the light plate to the right of the frame, and capitupindia.com opens in the browser.
7. **Stick your win.** Each visitor takes two stickers, one to keep and one for the sticker wall ("What did your policy
   surprise you with?").

**No client data at the booth.** Hosts don't collect policy numbers, phone numbers or documents, and they don't
photograph visitors on company devices. Anyone who wants a review signs up on the website, where consent is captured.
On the morning of each event, test the QR code on one iPhone and one Android phone from 3 m away.

## Needs CapitUp approval

- The official logo vector, clear-space and minimum-size rules, and whether there is an on-dark version
- The tagline: "Check your policy. Share your win." (alternatives: "Read the fine print. Strike a pose." ·
  "Policy checked. Main-character energy.")
- The supporting lines: "We read the fine print, so you don't have to." · "Policy review, in plain words" ·
  "Scan to check your policy" · "We don't sell insurance." Check them against what the service does and against IRDAI
  advertising norms.
- The hashtag #PolicyChecked and the social handle
- The six sticker lines: Policy checked · I read the fine print · Sub-limits? Spotted. · Claim-ready · Renewal sorted ·
  Adulting: insured
- The sample report card content
- The QR destination: plain https://capitupindia.com for now. Add UTM tags if event tracking is wanted.
- Colour proofs, budget, vendor, and venue rules (power, floor decals, fire-retardant certificate)
