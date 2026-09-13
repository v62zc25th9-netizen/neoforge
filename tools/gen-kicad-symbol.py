#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate KiCad symbols for the AES cartridge connectors from the pinout CSV.

    python3 tools/gen-kicad-symbol.py \\
        docs/data/aes-cartridge-pinout.csv \\
        hardware/lib/neoforge-aes.kicad_sym

The AES cartridge edge is two separate 100-pin connectors, CN4 on the CHA board
and CN5 on the PROG board, each with a top row (a) and a bottom row (b). This
emits one symbol per connector.

**Generated, never hand-edited.** The CSV is the single source of truth and was
built by cross-checking three independent sources — see docs/aes-connector.md.
If a pin is wrong, fix the CSV and re-run; editing the symbol makes the two
disagree silently, which is exactly the failure this script exists to prevent.

Pin electrical types are from the CARTRIDGE's point of view, because that is who
is designing a board. `input` means the console drives it and the cartridge
listens. This is worth getting right: it is what lets KiCad's ERC catch a
cartridge trying to drive a line the console already drives, which on a 200-pin
5V connector is the mistake that costs somebody an AES.

Anything not matched by the table below is emitted as `bidirectional` and listed
in the summary, so unclassified pins are visible rather than quietly assumed.
"""

from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict

# --------------------------------------------------------------------------
# Pin electrical type, from the cartridge's point of view.
#
# Each entry is (pattern, kicad_type, why). Order matters - first match wins.
# --------------------------------------------------------------------------
CLASSIFY = [
    # Power and no-connects
    (r"^GND$",              "power_in",     "ground"),
    (r"^VCC$",              "power_in",     "supply"),
    (r"^NC$",               "no_connect",   "not connected"),

    # Analogue audio passing through the cartridge
    (r"^[LR] (in|out)$",    "passive",      "analogue audio pass-through"),

    # --- Cartridge OUTPUTS: the few lines the cartridge drives -------------
    # Wait states. The cartridge tells the console how long to wait for it,
    # which is why our measurement work can sweep them directly.
    (r"^ROMWAIT$",          "output",       "cartridge sets P1 wait states"),
    (r"^PWAIT[01]$",        "output",       "cartridge sets P2 wait states"),
    (r"^PDTACK$",           "output",       "cartridge data acknowledge"),
    # Fix layer: S ROM straight to the console, never through the serializer.
    (r"^FIXD[0-7]$",        "output",       "fix tile data out"),
    # Serializer outputs. 32 C ROM lines are packed into these 8 plus opacity.
    (r"^G[AB]D[0-3]$",      "output",       "serialized sprite pixel data"),
    (r"^DOT[AB]$",          "output",       "sprite pixel opacity"),

    # --- Bidirectional buses ----------------------------------------------
    (r"^D(1[0-5]|[0-9])$",  "bidirectional", "68k data bus"),
    (r"^SDD[0-7]$",         "bidirectional", "Z80 data bus"),
    (r"^SD[RP]AD[0-7]$",    "bidirectional", "ADPCM data to the YM2610"),

    # --- Cartridge INPUTS: everything the console drives -------------------
    (r"^A(1[0-9]|[1-9])$",  "input",        "68k address bus"),
    (r"^P(2[0-3]|1[0-9]|[0-9])$", "input",  "PBUS from the LSPC"),
    (r"^SDA(1[0-5]|[0-9])$", "input",       "Z80 address bus"),
    (r"^SD[RP]A\d+$",       "input",        "ADPCM address from the YM2610"),
    (r"^(12M|24M|8M|4MB|68KCLKB)$", "input", "clock"),
    (r"^(PCK1B|PCK2B|LOAD|H|EVEN|2H1|CA4)$", "input", "LSPC video timing"),
    (r"^(AS|R/W|RESET)$",   "input",        "68k bus control"),
    (r"^ROMOE[LU]?$",       "input",        "P1 output enable"),
    (r"^PORT(OE|WE)[LU]$",  "input",        "P2 window strobes"),
    (r"^PORTADRS$",         "input",        "P2 window select"),
    (r"^SD(ROM|MRD|RD0|RD1)$", "input",     "Z80 ROM strobes"),
    (r"^SD[RP](MPX|OE)$",   "input",        "ADPCM strobes"),
]

PITCH = 2.54          # KiCad's standard grid
PIN_LEN = 5.08
HALF_W = 30.48        # half the body width


def classify(signal: str):
    for pattern, etype, why in CLASSIFY:
        if re.match(pattern, signal):
            return etype, why
    return "bidirectional", None      # unmatched - reported in the summary


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def pin_sexp(x: float, y: float, angle: int, etype: str,
             name: str, number: str) -> str:
    return (
        f'      (pin {etype} line (at {x:g} {y:g} {angle}) (length {PIN_LEN:g})\n'
        f'        (name "{esc(name)}" (effects (font (size 1.27 1.27))))\n'
        f'        (number "{esc(number)}" (effects (font (size 1.27 1.27))))\n'
        f'      )\n'
    )


def build_symbol(name: str, desc: str, rows: list[dict]) -> tuple[str, dict]:
    """rows: the CSV rows for one connector. Returns (sexp, stats)."""
    # Row 'a' is the top face, row 'b' the bottom. Left side of the symbol
    # carries 'a', right side 'b', both ordered by pin number - so the symbol
    # reads like the physical connector rather than like a functional grouping.
    def keyof(r):
        m = re.match(r"([ab])(\d+)", r["pin"])
        return (m.group(1), int(m.group(2)))

    a = sorted([r for r in rows if r["pin"].startswith("a")], key=keyof)
    b = sorted([r for r in rows if r["pin"].startswith("b")], key=keyof)
    n = max(len(a), len(b))

    top_y = (n - 1) * PITCH / 2.0
    body_top = top_y + PITCH
    body_bot = -top_y - PITCH

    stats = {"types": defaultdict(int), "unclassified": []}
    pins = ""

    for i, r in enumerate(a):
        etype, why = classify(r["signal"])
        stats["types"][etype] += 1
        if why is None:
            stats["unclassified"].append((r["pin"], r["signal"]))
        y = top_y - i * PITCH
        pins += pin_sexp(-(HALF_W + PIN_LEN), y, 0, etype, r["signal"], r["pin"])

    for i, r in enumerate(b):
        etype, why = classify(r["signal"])
        stats["types"][etype] += 1
        if why is None:
            stats["unclassified"].append((r["pin"], r["signal"]))
        y = top_y - i * PITCH
        pins += pin_sexp(HALF_W + PIN_LEN, y, 180, etype, r["signal"], r["pin"])

    s = f'''  (symbol "{name}"
    (pin_names (offset 1.016))
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "J" (at {-HALF_W:g} {body_top + 2.54:g} 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "{esc(name)}" (at {-HALF_W:g} {body_top + 5.08:g} 0)
      (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://github.com/v62zc25th9-netizen/neoforge/blob/main/docs/aes-connector.md" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Description" "{esc(desc)}" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide))
    (symbol "{name}_0_1"
      (rectangle (start {-HALF_W:g} {body_top:g}) (end {HALF_W:g} {body_bot:g})
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "{name}_1_1"
{pins}    )
  )
'''
    return s, stats


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    csv_path, out_path = sys.argv[1], sys.argv[2]

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    by_conn = defaultdict(list)
    for r in rows:
        by_conn[(r["connector"], r["board"])].append(r)

    parts = []
    all_stats = {}
    for (conn, board) in sorted(by_conn):
        name = f"AES_{conn}_{board}"
        desc = (f"Neo Geo AES cartridge connector {conn} ({board} board), "
                f"100 pins. Directions are from the cartridge's point of view.")
        sexp, stats = build_symbol(name, desc, by_conn[(conn, board)])
        parts.append(sexp)
        all_stats[name] = (stats, len(by_conn[(conn, board)]))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write('(kicad_symbol_lib\n')
        f.write('  (version 20231120)\n')
        f.write('  (generator "neoforge gen-kicad-symbol.py")\n')
        f.write('  (generator_version "8.0")\n')
        for p in parts:
            f.write(p)
        f.write(')\n')

    # ---- summary, so the classification is reviewable rather than trusted --
    print(f"wrote {out_path}")
    print()
    total_unclassified = 0
    for name, (stats, count) in all_stats.items():
        print(f"  {name}  ({count} pins)")
        for etype, n in sorted(stats["types"].items(), key=lambda kv: -kv[1]):
            print(f"      {etype:<15} {n:>4}")
        if stats["unclassified"]:
            total_unclassified += len(stats["unclassified"])
            print(f"      -- not matched by the direction table, "
                  f"emitted as bidirectional:")
            for pin, sig in stats["unclassified"]:
                print(f"         {pin:<5} {sig}")
        print()

    if total_unclassified:
        print(f"{total_unclassified} pin(s) unclassified. Not an error - but "
              f"each one is a direction ERC cannot check.")
    else:
        print("every pin classified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
