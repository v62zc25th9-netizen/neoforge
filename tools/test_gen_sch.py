#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Self-tests for gen-kicad-sch.py.

    python3 tools/test_gen_sch.py

The sheet is generated so that nobody transcribes 200 pins by hand. That only
helps if the generator puts each label on the pin it names - so these tests
recompute every pin position independently and check what actually landed there.
"""

from __future__ import annotations

import collections
import csv
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "tools", "gen-kicad-sch.py")
CSVP = os.path.join(ROOT, "docs", "data", "aes-cartridge-pinout.csv")

# Independent copies of the geometry. If the generator's constants drift from
# gen-kicad-symbol.py these tests should fail, so they are NOT imported.
PITCH, PIN_LEN, HALF_W = 2.54, 5.08, 30.48
OX, OY, GAP = 150.0, 160.0, 2.54

passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok    {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}   {detail}")


def generate(board):
    out = os.path.join(tempfile.mkdtemp(), f"{board}.kicad_sch")
    r = subprocess.run([sys.executable, GEN, board, out],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit(f"generator failed for {board}:\n{r.stdout}{r.stderr}")
    # the tool writes relative to the repo root
    path = out if os.path.exists(out) else os.path.join(ROOT, out)
    return open(path, encoding="utf-8").read()


def expected(board):
    rows = [r for r in csv.DictReader(open(CSVP, newline="", encoding="utf-8"))
            if r["board"] == board]
    by = collections.defaultdict(list)
    for r in rows:
        m = re.match(r"([ab])(\d+)$", r["pin"])
        by[m.group(1)].append((int(m.group(2)), r))
    for k in by:
        by[k].sort()
    n = max(len(by["a"]), len(by["b"]))
    top = (n - 1) * PITCH / 2
    out = {}
    for row, sign in (("a", -1), ("b", 1)):
        for idx, (num, r) in enumerate(by[row]):
            x = OX + sign * (HALF_W + PIN_LEN)
            y = OY - (top - idx * PITCH)
            out[f"{row}{num}"] = (round(x, 2), round(y, 2), r["signal"])
    return out


print("gen-kicad-sch self-tests")

for board in ("PROG", "CHA"):
    print(f"\n{board}")
    txt = generate(board)
    check("parentheses balanced", txt.count("(") == txt.count(")"),
          f'{txt.count("(")}/{txt.count(")")}')
    check("warns against hand-editing", "Do not hand-edit" in txt)

    labels = {(round(float(m.group(2)), 2), round(float(m.group(3)), 2)): m.group(1)
              for m in re.finditer(
                  r'\(global_label "([^"]+)" \(shape \w+\) \(at ([-\d.]+) ([-\d.]+)', txt)}
    ncs = {(round(float(m.group(1)), 2), round(float(m.group(2)), 2))
           for m in re.finditer(r'\(no_connect \(at ([-\d.]+) ([-\d.]+)\)', txt)}

    exp = expected(board)
    wrong = []
    for pin, (x, y, sig) in exp.items():
        if sig.strip().upper() == "NC":
            if (x, y) not in ncs:
                wrong.append((pin, "no no-connect flag at this pin"))
            continue
        want = sig.replace("/", "_").replace(" ", "_")
        got = labels.get((round(x + (GAP if x > OX else -GAP), 2), y))
        if got != want:
            wrong.append((pin, f"want {want}, got {got}"))
    check(f"all {len(exp)} pins carry the right net", not wrong,
          "; ".join(f"{p}: {w}" for p, w in wrong[:3]))

    check("no two labels share a position",
          len(labels) + len(ncs) == len(exp),
          f"{len(labels)} labels + {len(ncs)} NC vs {len(exp)} pins")

    nc_expected = sum(1 for _, _, s in exp.values() if s.strip().upper() == "NC")
    check(f"{nc_expected} NC pin(s) get a flag, not a label", len(ncs) == nc_expected,
          f"got {len(ncs)}")
    check("no pin is labelled with the literal net 'NC'",
          "NC" not in labels.values())

    # The first version shipped an empty lib_symbols and KiCad drew a "??"
    # placeholder instead of the connector. Guard against that returning.
    conn = "CN5" if board == "PROG" else "CN4"
    sym = f"AES_{conn}_{board}"
    check("symbol definition is embedded in the sheet",
          f'(symbol "neoforge-aes:{sym}"' in txt)
    check("the embedded definition carries its pins",
          txt.count("(pin ") >= 100, f'{txt.count("(pin ")} pin entries')
    check("lib_symbols is not empty", "(lib_symbols)" not in txt)

    check("regenerating is byte-identical", generate(board) == txt)

print()
print(f"{passed + failed} checks, {failed} failures")
sys.exit(1 if failed else 0)
