#!/usr/bin/env python3
"""Generate the NeoForge cartridge block diagram as SVG.

The diagram answers one question: *which chips does a NeoForge cartridge have
to contain, and where does each one come from?*  Every block is tagged with a
sourcing decision, because that is the thing a reader actually needs - a block
diagram that only shows data flow would be prettier and less useful.

The chip list below is the single source of truth. It is derived from, and must
stay consistent with:

    docs/teardown-fatal-fury-special.md   what a real cartridge contains
    docs/serializer.md                    what NEO-ZMC2 and NEO-273 do
    docs/cartridge-architecture.md        region bus widths
    docs/board-zero.md                    which blocks board zero omits

Run:  python3 tools/gen-block-diagram.py
Out:  docs/img/block-diagram.svg   (deterministic - byte-identical across runs)

MIT licensed, like everything in tools/.
"""

import html
import os

W, H = 1240, 1010

# Sourcing categories. The colours are chosen to stay legible on GitHub in both
# light and dark themes, which is why the diagram paints its own background
# rather than inheriting one.
CAT = {
    "mem":     ("#dbeafe", "#1e3a8a", "Memory - buy off the shelf"),
    "logic":   ("#dcfce7", "#14532d", "Commodity logic - buy (74-series)"),
    "custom":  ("#fee2e2", "#7f1d1d", "SNK custom - must be replaced"),
    "console": ("#e5e7eb", "#111827", "Inside the console - not ours"),
}

FONT = "ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

out = []
def e(s): out.append(s)
def esc(s): return html.escape(str(s), quote=True)

def box(x, y, w, h, title, sub="", cat="mem", bz=False, note=""):
    """One block. bz=True marks it as present on board zero."""
    fill, ink, _ = CAT[cat]
    sw, dash = (3, "") if bz else (1.5, "")
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" '
      f'stroke="{ink}" stroke-width="{sw}"{dash}/>')
    ty = y + 22
    e(f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" font-family="{FONT}" '
      f'font-size="15" font-weight="700" fill="{ink}">{esc(title)}</text>')
    if sub:
        e(f'<text x="{x+w/2}" y="{ty+17}" text-anchor="middle" font-family="{MONO}" '
          f'font-size="11.5" fill="{ink}" opacity="0.85">{esc(sub)}</text>')
    if note:
        e(f'<text x="{x+w/2}" y="{y+h-9}" text-anchor="middle" font-family="{FONT}" '
          f'font-size="10.5" fill="{ink}" opacity="0.75">{esc(note)}</text>')
    if bz:
        e(f'<circle cx="{x+w-13}" cy="{y+13}" r="8" fill="{ink}"/>')
        e(f'<text x="{x+w-13}" y="{y+17}" text-anchor="middle" font-family="{FONT}" '
          f'font-size="10" font-weight="700" fill="{fill}">0</text>')

def panel(x, y, w, h, label, note=""):
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" '
      f'stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="7 5"/>')
    e(f'<text x="{x+14}" y="{y+22}" font-family="{FONT}" font-size="15" '
      f'font-weight="700" fill="#4b5563">{esc(label)}</text>')
    if note:
        e(f'<text x="{x+w-14}" y="{y+22}" text-anchor="end" font-family="{FONT}" '
          f'font-size="11.5" fill="#6b7280">{esc(note)}</text>')

def arrow(x1, y1, x2, y2, label="", side="right", dashed=False, above=False):
    """above=True puts the label centred clear of the line, which is what short
    arrows between two adjacent boxes need - a side label lands inside a box."""
    d = ' stroke-dasharray="5 4"' if dashed else ""
    e(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4b5563" '
      f'stroke-width="1.6" marker-end="url(#a)"{d}/>')
    if not label:
        return
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if above:
        e(f'<text x="{mx}" y="{my-7}" text-anchor="middle" font-family="{MONO}" '
          f'font-size="10.5" fill="#374151">{esc(label)}</text>')
        return
    anchor = "start" if side == "right" else "end"
    dx = 8 if side == "right" else -8
    e(f'<text x="{mx+dx}" y="{my+4}" text-anchor="{anchor}" font-family="{MONO}" '
      f'font-size="11" fill="#374151">{esc(label)}</text>')

e(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
  f'viewBox="0 0 {W} {H}" role="img" aria-label="NeoForge AES cartridge block diagram">')
e('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
  'markerHeight="6" orient="auto-start-reverse">'
  '<path d="M 0 0 L 10 5 L 0 10 z" fill="#4b5563"/></marker></defs>')
e(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

e(f'<text x="28" y="40" font-family="{FONT}" font-size="23" font-weight="800" '
  f'fill="#111827">What a NeoForge AES cartridge has to contain</text>')
e(f'<text x="28" y="63" font-family="{FONT}" font-size="13.5" fill="#6b7280">'
  'Every block tagged by where the part comes from. Blocks marked '
  '● 0 are the only ones board zero fits.</text>')

# --- console -----------------------------------------------------------------
box(28, 84, W - 56, 86, "AES console", "", "console",
    note="68000 @ 12.083915 MHz   \u00b7   LSPC2-A2 video   \u00b7   Z80 + YM2610 audio   \u00b7   NEO-C1 / NEO-E0 decode")
e(f'<text x="{W/2}" y="{84+54}" text-anchor="middle" font-family="{FONT}" font-size="12.5" '
  f'fill="#374151">all cartridge decode and all timing originate here \u2014 the cartridge is a slave on every bus</text>')

# --- edge connectors ---------------------------------------------------------
box(70, 196, 440, 46, "CN5 \u2014 PROG edge", "2 \u00d7 50 pins \u00b7 2.54 mm pitch \u00b7 1.65 mm board", "console", bz=True)
box(730, 196, 440, 46, "CN4 \u2014 CHA edge", "2 \u00d7 50 pins \u00b7 2.54 mm pitch \u00b7 1.65 mm board", "console")
arrow(290, 170, 290, 194)
arrow(950, 170, 950, 194)

# --- what crosses each connector --------------------------------------------
def band(cx, lines):
    for i, t in enumerate(lines):
        e(f'<text x="{cx}" y="{262 + i*16}" text-anchor="middle" font-family="{MONO}" '
          f'font-size="11" fill="#374151">{esc(t)}</text>')
band(290, ["A1\u2013A19  D0\u2013D15  /ROMOE  /ROMOEU  /ROMOEL  /PORTOEU  /PORTOEL",
           "SDRAD0\u20137  SDRA8\u20139  SDRA20\u201323  SDRMPX  /SDROE   \u2192  V",
           "/ROMWAIT  /PWAIT0  /PWAIT1  PDTACK   \u2190  back to the console"])
band(950, ["PBUS P0\u2013P22  PCK1B  PCK2B  2H1  LOAD  H  EVEN  12M  CA4",
           "SDA0\u201315  SDRD0\u20131  /SDMRD  /SDROM   \u2192  M",
           "GAD0\u20133  GBD0\u20133  DOTA  DOTB  FIXD   \u2190  back to the console"])
arrow(490, 242, 490, 296)
arrow(1150, 242, 1150, 296)

# --- PROG --------------------------------------------------------------------
panel(44, 300, 492, 412, "PROG board", "the 68000 bus and the sound samples")

box(70, 332, 200, 76, "P ROM", "16-bit \u00b7 $000000\u2013$0FFFFF", "mem", bz=True,
    note="2 \u00d7 SST39SF040, 5 V, 70 ns")
box(310, 332, 200, 76, "P ROM, banked", "16-bit \u00b7 $200000\u2013$2FFFFF", "mem",
    note="absent on board zero")
box(70, 424, 200, 60, "/PORTOE gate", "74LS08", "logic", note="no /PORTOE pin exists")
box(310, 424, 200, 60, "bank latch", "74LS74 \u00b7 2 bits", "logic", note="drives P2 A20/A21")
arrow(410, 424, 410, 410)

box(70, 500, 200, 76, "V ROM", "8-bit \u00b7 ADPCM samples", "mem", note="up to 16 MB")
box(310, 500, 200, 76, "NEO-PCM", "SNK custom", "custom", note="de-multiplexes the ADPCM bus")
arrow(308, 538, 272, 538, "V address", above=True)

box(70, 592, 440, 50, "V ROM chip select", "74LS139", "logic")
box(70, 656, 440, 44, "wait-state network", "4 \u00d7 220 \u03a9 \u2192 VCC", "logic", bz=True)

# --- CHA ---------------------------------------------------------------------
panel(704, 300, 492, 412, "CHA board", "sprites, the fix layer and the Z80")

box(730, 332, 200, 76, "C ROM", "32-bit \u00b7 sprite tiles", "mem", note="the bandwidth problem")
box(970, 332, 200, 76, "NEO-ZMC2 \u00b7 dot", "SNK custom", "custom",
    note="\u2192 GAD/GBD + DOTA/DOTB")
arrow(932, 370, 968, 370, "CR0\u201331", above=True)

box(730, 424, 200, 60, "NEO-273", "SNK custom", "custom", note="C + S address latches")
box(970, 424, 200, 60, "the S half of it", "2 \u00d7 74HCT374", "logic", note="latches + wiring")
arrow(932, 454, 968, 454)

box(730, 500, 200, 76, "S ROM", "8-bit \u00b7 fix tiles", "mem", note="straight to the edge")
box(970, 500, 200, 76, "M ROM", "8-bit \u00b7 Z80 code", "mem")
arrow(830, 486, 830, 498)

box(730, 592, 200, 50, "NEO-ZMC2 \u00b7 zmc", "SNK custom", "custom")
box(970, 592, 200, 50, "glue", "74LS74 \u00b7 LS139 \u00b7 LS32", "logic")
arrow(930, 617, 968, 617, "", side="right", dashed=True)
e(f'<text x="830" y="{660}" text-anchor="middle" font-family="{FONT}" font-size="11" '
  f'fill="#7f1d1d">Z80 banker \u2014 omit entirely if the M ROM fits in 32 KB</text>')

# --- legend ------------------------------------------------------------------
ly = 736
e(f'<text x="28" y="{ly}" font-family="{FONT}" font-size="15" font-weight="700" '
  f'fill="#111827">Where each part comes from</text>')
lx = 28
for key in ("mem", "logic", "custom", "console"):
    fill, ink, label = CAT[key]
    e(f'<rect x="{lx}" y="{ly+14}" width="20" height="20" rx="4" fill="{fill}" '
      f'stroke="{ink}" stroke-width="1.5"/>')
    e(f'<text x="{lx+28}" y="{ly+29}" font-family="{FONT}" font-size="12.5" '
      f'fill="#374151">{esc(label)}</text>')
    lx += 300
e(f'<circle cx="38" cy="{ly+58}" r="8" fill="#111827"/>')
e(f'<text x="38" y="{ly+62}" text-anchor="middle" font-family="{FONT}" font-size="10" '
  f'font-weight="700" fill="#ffffff">0</text>')
e(f'<text x="56" y="{ly+62}" font-family="{FONT}" font-size="12.5" fill="#374151">'
  'on board zero — everything else is deliberately absent from the first board</text>')

# --- the three customs -------------------------------------------------------
ty = ly + 92
e(f'<rect x="28" y="{ty}" width="{W-56}" height="150" rx="9" fill="#fef2f2" '
  f'stroke="#7f1d1d" stroke-width="1.5"/>')
e(f'<text x="48" y="{ty+28}" font-family="{FONT}" font-size="15" font-weight="700" '
  f'fill="#7f1d1d">The three SNK customs, and what replacing each one costs</text>')
rows = [
 ("NEO-273", "CHA", "20-bit C + 16-bit S address latches off PBUS, with nibble rotations",
  "S half is 2 × 74HCT374. The rotations are wiring."),
 ("NEO-ZMC2 · dot", "CHA", "serializes 32 bits of C into GAD/GBD + DOTA/DOTB at 12 MHz",
  "programmable logic, or buy a replacement board"),
 ("NEO-PCM", "PROG", "services the YM2610's multiplexed ADPCM address bus",
  "NOT YET ANALYSED — the least understood part of the cartridge"),
]
for i, (name, board, job, route) in enumerate(rows):
    y = ty + 54 + i * 31
    e(f'<text x="48" y="{y}" font-family="{MONO}" font-size="12.5" font-weight="700" '
      f'fill="#7f1d1d">{esc(name)}</text>')
    e(f'<text x="200" y="{y}" font-family="{MONO}" font-size="12" fill="#991b1b">{esc(board)}</text>')
    e(f'<text x="258" y="{y}" font-family="{FONT}" font-size="12.5" fill="#374151">{esc(job)}</text>')
    e(f'<text x="{W-48}" y="{y}" text-anchor="end" font-family="{FONT}" font-size="12.5" '
      f'font-weight="600" fill="#7f1d1d">{esc(route)}</text>')

e(f'<text x="28" y="{H-14}" font-family="{FONT}" font-size="11" fill="#9ca3af">'
  'Generated by tools/gen-block-diagram.py · github.com/v62zc25th9-netizen/neoforge '
  '· sources in docs/teardown-fatal-fury-special.md, serializer.md, '
  'cartridge-architecture.md, board-zero.md</text>')
e('</svg>')

path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "docs", "img", "block-diagram.svg")
with open(os.path.normpath(path), "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("wrote docs/img/block-diagram.svg")
