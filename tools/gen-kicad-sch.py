#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the cartridge-connector schematic sheet from the pinout CSV.

    python3 tools/gen-kicad-sch.py PROG hardware/neoforge-prog-connector.kicad_sch
    python3 tools/gen-kicad-sch.py CHA  hardware/neoforge-cha-connector.kicad_sch

**Generated. Do not hand-edit.** Fix the CSV and re-run. Editing the sheet makes
it disagree with the pinout silently, which is the failure this exists to stop.

WHY GENERATE THIS SHEET AND NOT THE REST
----------------------------------------
docs/data/aes-cartridge-pinout.csv is verified pin for pin against two
independent sources. The connector sheet is 200 pins of pure transcription from
it, and the failure mode of transcribing 200 things by hand is one silent
transposition on a 5V edge connector - outputs driven into lines the console
also drives.

So the boundary is drawn where the risk is: **this sheet is generated, the logic
sheet is drawn by hand.** Decode, wait-state resistors, memory and power are a
couple of dozen parts that need judgement, and a human-drawn sheet is what a
reviewer can read.

`tools/neoforge-netcheck` then validates whatever KiCad exports, so a mistake in
either half is caught before fabrication.

HOW IT CONNECTS
---------------
No wires. Each pin gets a **global label placed exactly at that pin's connection
point**, which is how KiCad forms the net. Wires would mean matching endpoint
geometry to sub-millimetre precision for 200 segments; labels-at-pins needs the
position right once, per pin, from the same arithmetic the symbol generator used.

THE Y-AXIS TRAP
---------------
Symbol libraries measure Y **upwards**. Schematic sheets measure Y
**downwards**. A pin drawn at symbol-y = +10 therefore lands at schematic-y =
origin_y - 10. Getting this backwards mirrors the connector top to bottom and
every label lands on the wrong pin - a failure that looks plausible and is
caught only by netcheck or by a dead board. It is the one line in this file
worth re-reading.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import sys
from collections import defaultdict

# Must match tools/gen-kicad-symbol.py exactly, or labels miss their pins.
PITCH = 2.54
PIN_LEN = 5.08
HALF_W = 30.48

ORIGIN_X = 150.0      # where the connector body sits on the sheet, mm
ORIGIN_Y = 160.0
LABEL_GAP = 2.54      # how far past the pin end the label text starts

LIB = "neoforge-aes"
CSV_DEFAULT = "docs/data/aes-cartridge-pinout.csv"

# Direction, from the cartridge's point of view, drives the label shape so the
# sheet reads correctly and ERC has something to check. Mirrors the table in
# gen-kicad-symbol.py; anything unmatched becomes bidirectional.
SHAPE = {
    "input": "input", "output": "output", "bidirectional": "bidirectional",
    "power_in": "input", "passive": "passive", "no_connect": "passive",
}


def uuid_for(*parts) -> str:
    """Deterministic UUIDs, so regenerating produces an identical file."""
    h = hashlib.sha1(("neoforge:" + ":".join(str(p) for p in parts)).encode()).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def netname(sig: str) -> str:
    """A label KiCad will accept, keeping the signal readable."""
    n = sig.strip()
    n = n.replace("/", "_")          # R/W -> R_W
    n = re.sub(r"\s+", "_", n)       # "L in" -> L_in
    return n


def load(csv_path, board):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["board"] == board]
    if not rows:
        raise SystemExit(f"gen-kicad-sch: no rows for board {board}")
    conn = rows[0]["connector"]
    by_row = defaultdict(list)
    for r in rows:
        m = re.match(r"([ab])(\d+)$", r["pin"])
        if not m:
            raise SystemExit(f"gen-kicad-sch: unparseable pin {r['pin']}")
        by_row[m.group(1)].append((int(m.group(2)), r))
    for k in by_row:
        by_row[k].sort()
    return conn, by_row


def no_connect(x, y):
    """A pin the pinout calls NC gets a no-connect flag, NOT a label.

    Labelling them would tie every NC pin to a net called NC - i.e. wire them
    to each other. Harmless here because both are genuinely unconnected, but
    wrong, and the sort of wrong that stops being harmless the moment somebody
    copies the pattern onto a pin that matters.
    """
    return (f'  (no_connect (at {x:g} {y:g}) '
            f'(uuid "{uuid_for("nc", x, y)}"))\n')


def label(x, y, text, shape, mirrored):
    """A global label at (x, y). Justify away from the body so text does not
    overlap the symbol."""
    just = "right" if mirrored else "left"
    ang = 180 if mirrored else 0
    return (
        f'  (global_label "{esc(text)}" (shape {shape}) (at {x:g} {y:g} {ang})\n'
        f'    (effects (font (size 1.27 1.27)) (justify {just}))\n'
        f'    (uuid "{uuid_for("lbl", text, x, y)}")\n'
        f'  )\n'
    )


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    board, out_path = sys.argv[1].upper(), sys.argv[2]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn, by_row = load(os.path.join(root, CSV_DEFAULT), board)

    sym = f"AES_{conn}_{board}"
    ref = "J1" if board == "PROG" else "J2"
    n = max(len(by_row["a"]), len(by_row["b"]))
    top_y = (n - 1) * PITCH / 2.0

    body = []
    labels = []
    used = set()

    for row, sign, mirrored in (("a", -1, True), ("b", +1, False)):
        for idx, (num, r) in enumerate(by_row[row]):
            # symbol-space Y, exactly as gen-kicad-symbol.py computes it
            sym_y = top_y - idx * PITCH
            # ---- the Y-axis trap: symbol Y is up, sheet Y is down ----
            x = ORIGIN_X + sign * (HALF_W + PIN_LEN)
            y = ORIGIN_Y - sym_y
            if (x, y) in used:
                raise SystemExit(f"gen-kicad-sch: two pins at {x},{y} - geometry is wrong")
            used.add((x, y))
            if r["signal"].strip().upper() == "NC":
                labels.append(no_connect(x, y))
            else:
                shape = SHAPE.get(r.get("direction", ""), "bidirectional")
                labels.append(label(x + sign * LABEL_GAP, y,
                                    netname(r["signal"]), shape, mirrored))
            body.append(f'    (pin "{r["pin"]}" (uuid "{uuid_for("pin", ref, r["pin"])}"))\n')

    sheet_uuid = uuid_for("sheet", board)
    sym_uuid = uuid_for("sym", ref, board)

    out = []
    out.append('(kicad_sch (version 20230121) (generator "neoforge gen-kicad-sch.py")\n')
    out.append(f'  (uuid "{sheet_uuid}")\n')
    out.append('  (paper "A3")\n')
    out.append('  (title_block\n')
    out.append(f'    (title "NeoForge {board} cartridge connector")\n')
    out.append('    (comment 1 "GENERATED from docs/data/aes-cartridge-pinout.csv")\n')
    out.append('    (comment 2 "Do not hand-edit. Fix the CSV and re-run tools/gen-kicad-sch.py.")\n')
    out.append('    (comment 3 "Verify with tools/neoforge-netcheck before fabricating.")\n')
    out.append('  )\n')
    out.append('  (lib_symbols)\n')
    out.append(f'  (symbol (lib_id "{LIB}:{sym}") (at {ORIGIN_X:g} {ORIGIN_Y:g} 0) (unit 1)\n')
    out.append('    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)\n')
    out.append(f'    (uuid "{sym_uuid}")\n')
    out.append(f'    (property "Reference" "{ref}" (at {ORIGIN_X - HALF_W:g} {ORIGIN_Y - top_y - 7.62:g} 0)\n')
    out.append('      (effects (font (size 1.27 1.27)) (justify left)))\n')
    out.append(f'    (property "Value" "{sym}" (at {ORIGIN_X - HALF_W:g} {ORIGIN_Y - top_y - 5.08:g} 0)\n')
    out.append('      (effects (font (size 1.27 1.27)) (justify left)))\n')
    out.extend(body)
    out.append(f'    (instances (project "neoforge" (path "/{sheet_uuid}" (reference "{ref}") (unit 1))))\n')
    out.append('  )\n')
    out.extend(labels)
    out.append(')\n')

    os.makedirs(os.path.dirname(os.path.join(root, out_path)) or ".", exist_ok=True)
    with open(os.path.join(root, out_path), "w", encoding="utf-8") as f:
        f.writelines(out)

    print(f"wrote {out_path}")
    nc = sum(1 for r in sum(by_row.values(), [])
             if r[1]["signal"].strip().upper() == "NC")
    print(f"  {sym} as {ref}, {len(labels) - nc} pins labelled, {nc} no-connect flag(s)")
    print(f"  row a at x={ORIGIN_X - (HALF_W + PIN_LEN):g}, row b at x={ORIGIN_X + (HALF_W + PIN_LEN):g}")
    print(f"  y from {ORIGIN_Y - top_y:g} to {ORIGIN_Y + top_y:g}, {PITCH:g} mm pitch")
    print()
    print("  next: open in KiCad, then export a netlist and run")
    print("        tools/neoforge-netcheck <netlist>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
