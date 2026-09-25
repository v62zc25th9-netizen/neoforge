#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Self-tests for neoforge-netcheck. No framework, no dependencies.

    python3 tools/test_netcheck.py

Builds synthetic KiCad netlists from the pinout CSV, damages them in specific
ways, and asserts the checker notices. Same convention as test_rominfo.py and
the testbenches in sim/: known input, known output, print a count.

The point is that the checker must fail on a board that would not work. A
checker that only passes good input is worth nothing.
"""

from __future__ import annotations

import csv
import importlib.util
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "neoforge-netcheck")
CSVP = os.path.join(ROOT, "docs", "data", "aes-cartridge-pinout.csv")

spec = importlib.util.spec_from_loader(
    "netcheck", importlib.machinery.SourceFileLoader("netcheck", TOOL))
nc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nc)

passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok    {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}   {detail}")


def pins_for(board, connector):
    with open(CSVP, newline="", encoding="utf-8") as f:
        return {r["pin"]: r["signal"] for r in csv.DictReader(f)
                if r["board"] == board and r["connector"] == connector}


def netlist(ref, mapping):
    """Emit a minimal but structurally real KiCad netlist."""
    by_net = {}
    for pin, net in mapping.items():
        if net is None:
            continue
        by_net.setdefault(net, []).append(pin)
    out = ['(export (version "E")', '  (nets']
    for i, (net, pl) in enumerate(sorted(by_net.items()), 1):
        out.append(f'    (net (code "{i}") (name "{net}")')
        for p in pl:
            out.append(f'      (node (ref "{ref}") (pin "{p}") (pintype "passive"))')
        out.append("    )")
    out.append("  )")
    out.append(")")
    return "\n".join(out)


def run(text, *args):
    with tempfile.NamedTemporaryFile("w", suffix=".net", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        r = subprocess.run([sys.executable, TOOL, path, *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr
    finally:
        os.unlink(path)


print("neoforge-netcheck self-tests")
print()

# ---- 1. a correct PROG connector -----------------------------------------
print("1. a correct netlist")
prog = pins_for("PROG", "CN5")
rc, out = run(netlist("J1", dict(prog)))
check("exit 0", rc == 0, f"rc={rc}")
check("reports a match", "every connector pin matches" in out)
check("identifies the board", "PROG CN5" in out, out[:200])

# ---- 2. two pins transposed ----------------------------------------------
print("\n2. two pins transposed - the error that costs a board")
bad = dict(prog)
bad["b30"], bad["b31"] = prog["b31"], prog["b30"]
rc, out = run(netlist("J1", bad))
check("exit 1", rc == 1, f"rc={rc}")
check("flags b30", "b30" in out and "wrong net" in out)
check("flags b31", "b31" in out)
check("refuses fabrication", "Do not fabricate" in out)

# ---- 3. a missing pin ------------------------------------------------------
print("\n3. a pin absent from the netlist")
bad = dict(prog); bad.pop("b28")
rc, out = run(netlist("J1", bad))
check("exit 1", rc == 1)
check("names the missing pin", "b28" in out and "missing" in out)

# ---- 4. a pin the pinout does not know ------------------------------------
print("\n4. a pin the pinout does not contain")
bad = dict(prog); bad["b99"] = "MYSTERY"
rc, out = run(netlist("J1", bad))
check("exit 1", rc == 1)
check("names it", "b99" in out and "not in the pinout" in out)

# ---- 5. an NC pin wired to something --------------------------------------
print("\n5. an NC pin quietly connected")
cha = pins_for("CHA", "CN4")
ncpins = [p for p, s in cha.items() if s.upper() == "NC"]
check("the CHA connector has NC pins to test", len(ncpins) >= 1, str(ncpins))
if ncpins:
    good = {p: (None if s.upper() == "NC" else s) for p, s in cha.items()}
    rc, out = run(netlist("J2", good))
    check("unconnected NC passes", rc == 0, out[:300])
    bad = dict(good); bad[ncpins[0]] = "SOMETHING"
    rc, out = run(netlist("J2", bad))
    check("connected NC fails", rc == 1)
    check("names the NC pin", ncpins[0] in out and "NC pin is connected" in out)

# ---- 6. lenient net naming -------------------------------------------------
print("\n6. legitimate net-name decoration is accepted")
lenient = {}
for p, s in prog.items():
    u = s.upper()
    if u == "VCC":
        lenient[p] = "+5V"
    elif u == "GND":
        lenient[p] = "VSS"
    elif u == "AS":
        lenient[p] = "/nAS"
    elif u == "R/W":
        lenient[p] = "R/W"
    else:
        lenient[p] = "/" + s
rc, out = run(netlist("J1", lenient))
check("+5V counts as VCC, VSS as GND, /nAS as AS", rc == 0, out[:400])

# ---- 7. the CHA connector is recognised too -------------------------------
print("\n7. the CHA connector")
good = {p: (None if s.upper() == "NC" else s) for p, s in cha.items()}
rc, out = run(netlist("J2", good))
check("exit 0", rc == 0)
check("identifies CHA CN4", "CHA CN4" in out, out[:200])

# ---- 8. a netlist with no connector at all --------------------------------
print("\n8. a netlist containing no connector")
rc, out = run(netlist("U1", {"1": "A", "2": "B"}))
check("exit 1", rc == 1)
check("says so plainly", "no connector found" in out)

# ---- 9. canonicalisation unit checks --------------------------------------
print("\n9. net-name canonicalisation")
check("nAS == AS", nc.family("nAS") == nc.family("AS"))
check("/AS == AS", nc.family("/AS") == nc.family("AS"))
check("AS_N == AS", nc.family("AS_N") == nc.family("AS"))
check("+5V == VCC", nc.family("+5V") == nc.family("VCC"))
check("VSS == GND", nc.family("VSS") == nc.family("GND"))
check("R/W == R_W", nc.family("R/W") == nc.family("R_W"))
check("L in == L_in", nc.family("L in") == nc.family("L_in"))
check("D0 != D1", nc.family("D0") != nc.family("D1"))
check("VCC != GND", nc.family("VCC") != nc.family("GND"))

# ---- 10. round trip: the generator's net names must satisfy the checker ----
print("\n10. round trip against gen-kicad-sch's naming")
def gen_netname(sig):
    """Mirror of netname() in gen-kicad-sch.py."""
    return re.sub(r"\s+", "_", sig.strip().replace("/", "_"))

mismatched = [s for s in set(prog.values()) | set(cha.values())
              if s.upper() != "NC" and nc.family(gen_netname(s)) != nc.family(s)]
check("every CSV signal survives the generator's renaming",
      not mismatched, str(sorted(mismatched)[:5]))

renamed = {p: gen_netname(s) for p, s in prog.items()}
rc, out = run(netlist("J1", renamed))
check("a sheet built with generated names passes clean", rc == 0, out[:300])

print()
print(f"{passed + failed} checks, {failed} failures")
sys.exit(1 if failed else 0)
