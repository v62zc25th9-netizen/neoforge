#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Self-checking tests for neoforge-rominfo.

Same convention as the Verilog testbenches in sim/: build known inputs, assert
known outputs, print a count. No framework, no dependencies.

    python3 tools/test_rominfo.py
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "neoforge-rominfo")

KB = 1024
MB = 1024 * KB

checks = 0
failures = 0


def chk(name: str, got, want) -> None:
    global checks, failures
    checks += 1
    if got != want:
        failures += 1
        print(f"  FAIL {name}: got {got!r} want {want!r}")


def run(path: str):
    """Run the tool and return (exit_code, parsed_json)."""
    p = subprocess.run([sys.executable, TOOL, path, "--json"],
                       capture_output=True, text=True)
    try:
        return p.returncode, json.loads(p.stdout)
    except json.JSONDecodeError:
        return p.returncode, {"_stdout": p.stdout, "_stderr": p.stderr}


def levels(rep) -> list[str]:
    return [f["level"] for f in rep.get("findings", [])]


def texts(rep) -> str:
    return " ".join(f["text"] for f in rep.get("findings", []))


def write(path: str, size: int, fill: bytes = b"\0") -> None:
    with open(path, "wb") as f:
        f.write(fill * size)


def romset(d: str, **regions) -> str:
    """Build a ROM set directory. regions: p1=size, c1=size, ..."""
    os.makedirs(d, exist_ok=True)
    for name, size in regions.items():
        ext = name[0]
        write(os.path.join(d, f"t-{name}.{name}"), size)
    return d


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="rominfo-test-")
    print()
    print("neoforge-rominfo")
    print("========================================")
    print()

    # ---- 1: a well-formed ROM set --------------------------------------
    print("Test 1 - a well-formed ROM set")
    d = romset(os.path.join(tmp, "good"),
               p1=1 * MB, s1=128 * KB, m1=128 * KB, v1=512 * KB,
               c1=2 * MB, c2=2 * MB)
    code, rep = run(d)
    chk("exit code", code, 0)
    chk("no errors", "error" in levels(rep), False)
    chk("P size", rep["regions"]["P"], 1 * MB)
    chk("C size", rep["regions"]["C"], 4 * MB)
    chk("total", rep["total"], 1 * MB + 128 * KB + 128 * KB + 512 * KB + 4 * MB)
    print("  parsed, no findings, sizes correct.")
    print()

    # ---- 2: C ROMs must pair -------------------------------------------
    # Odd files carry bitplanes 0 and 1, even files 2 and 3, so an odd count
    # cannot be served to the serializer at all.
    print("Test 2 - C ROMs must come in pairs")
    d = romset(os.path.join(tmp, "odd"),
               p1=512 * KB, s1=128 * KB, m1=128 * KB, c1=512 * KB,
               c2=512 * KB, c3=512 * KB)
    code, rep = run(d)
    chk("exit code", code, 1)
    chk("has error", "error" in levels(rep), True)
    chk("names pairing", "pairs" in texts(rep), True)
    print("  three C ROMs rejected.")
    print()

    # ---- 3: paired C ROMs must match in size ---------------------------
    print("Test 3 - a C ROM pair must be the same size")
    d = romset(os.path.join(tmp, "mismatch"),
               p1=512 * KB, s1=128 * KB, m1=128 * KB,
               c1=512 * KB, c2=256 * KB)
    code, rep = run(d)
    chk("exit code", code, 1)
    chk("has error", "error" in levels(rep), True)
    print("  mismatched pair rejected.")
    print()

    # ---- 4: the 2 MB P ambiguity ---------------------------------------
    # romtool.py and neosdconv produce different .neo files at exactly this
    # size. Verified by experiment 2026-09-12. See docs/rom-format.md.
    print("Test 4 - P of exactly 2 MB is flagged")
    d = romset(os.path.join(tmp, "twomeg"),
               p1=2 * MB, s1=128 * KB, m1=128 * KB, c1=1 * MB, c2=1 * MB)
    code, rep = run(d)
    chk("exit code", code, 0)                       # a warning, not an error
    chk("warns", "warning" in levels(rep), True)
    chk("names both tools",
        "romtool" in texts(rep) and "neosdconv" in texts(rep), True)

    # and a 1 MB P must NOT be flagged for it
    d = romset(os.path.join(tmp, "onemeg"),
               p1=1 * MB, s1=128 * KB, m1=128 * KB, c1=1 * MB, c2=1 * MB)
    _, rep2 = run(d)
    chk("1 MB P not flagged", "neosdconv" in texts(rep2), False)
    print("  flagged at 2 MB, silent at 1 MB.")
    print()

    # ---- 5: .neo round trip --------------------------------------------
    print("Test 5 - a .neo container is parsed")
    psz, ssz, msz, v1, v2, csz = 1 * MB, 128 * KB, 128 * KB, 512 * KB, 0, 2 * MB
    hdr = b"NEO" + bytes([1])
    hdr += struct.pack("<6I", psz, ssz, msz, v1, v2, csz)
    hdr += struct.pack("<4I", 2026, 0, 0, 0x041)
    hdr += struct.pack("33s", b"NeoForge Test")
    hdr += struct.pack("17s", b"neoforge")
    hdr += bytes(4096 - len(hdr))
    path = os.path.join(tmp, "good.neo")
    with open(path, "wb") as f:
        f.write(hdr + bytes(psz + ssz + msz + v1 + v2 + csz))
    code, rep = run(path)
    chk("exit code", code, 0)
    chk("kind", rep["kind"], "neo")
    chk("name", rep["meta"]["name"], "NeoForge Test")
    chk("ngh", rep["meta"]["ngh"], "0x041")
    chk("P size", rep["regions"]["P"], psz)
    chk("V merges v1+v2", rep["regions"]["V"], v1 + v2)
    print("  header and regions read back.")
    print()

    # ---- 6: a .neo whose header lies ------------------------------------
    print("Test 6 - header sizes must match the file")
    hdr = b"NEO" + bytes([1]) + struct.pack("<6I", 99999999, 0, 0, 0, 0, 0)
    hdr += bytes(4096 - len(hdr))
    path = os.path.join(tmp, "liar.neo")
    with open(path, "wb") as f:
        f.write(hdr + bytes(1000))
    code, rep = run(path)
    chk("exit code", code, 1)
    chk("has error", "error" in levels(rep), True)
    print("  inconsistent header rejected.")
    print()

    # ---- 7: not a .neo at all -------------------------------------------
    # This crashed the first version - the header was rejected before the
    # metadata existed, and the renderer assumed it was there.
    print("Test 7 - a file that is not a .neo fails cleanly")
    path = os.path.join(tmp, "notneo.neo")
    with open(path, "wb") as f:
        f.write(b"PK\x03\x04" + bytes(5000))
    code, rep = run(path)
    chk("exit code", code, 1)
    chk("no traceback", "_stdout" in rep, False)
    chk("has error", "error" in levels(rep), True)
    print("  reported, not crashed.")
    print()

    # ---- 8: banking inference ------------------------------------------
    # $000000-$0FFFFF is fixed and never banked, so a P that fits there needs
    # no mapper. Above it, the rest is reached through $200000-$2FFFFF.
    print("Test 8 - banking is inferred from P size")
    d = romset(os.path.join(tmp, "nobank"),
               p1=1 * MB, s1=128 * KB, m1=128 * KB, c1=1 * MB, c2=1 * MB)
    _, rep = run(d)
    chk("1 MB needs no banking", rep["cartridge"]["banking"], "none")
    chk("zero bank bits", rep["cartridge"]["bank_bits"], 0)

    # Metal Slug X ships 1024k + 4096k. 4 MB banked, four banks, two bits -
    # which is exactly what PROGBK1's 74LS74 provides.
    d = romset(os.path.join(tmp, "msx"),
               p1=1 * MB, p2=4 * MB, s1=128 * KB, m1=128 * KB,
               c1=1 * MB, c2=1 * MB)
    _, rep = run(d)
    chk("5 MB banks", rep["cartridge"]["banks"], 4)
    chk("5 MB bits", rep["cartridge"]["bank_bits"], 2)
    chk("PROGBK1 suffices", rep["cartridge"]["progbk1_capacity"], True)
    print("  no banking at 1 MB; four banks and two bits at 5 MB.")
    print()

    # ---- 9: past PROGBK1 -------------------------------------------------
    # Metal Slug 3 ships 2 x 4096k. Seven banks needs three bits, and PROGBK1
    # has two - so that board cannot be a PROGBK1, and neither could a
    # NeoForge board that copies one.
    print("Test 9 - P beyond PROGBK1's capacity is called out")
    d = romset(os.path.join(tmp, "ms3"),
               p1=4 * MB, p2=4 * MB, m1=512 * KB, c1=1 * MB, c2=1 * MB)
    _, rep = run(d)
    chk("8 MB bits", rep["cartridge"]["bank_bits"], 3)
    chk("PROGBK1 insufficient", rep["cartridge"]["progbk1_capacity"], False)
    chk("says so", "PROGBK1" in texts(rep), True)
    print("  three bits needed, two available, reported.")
    print()

    # ---- 10: fix source --------------------------------------------------
    # Late CHAFIO games ship no S ROM and draw fix tiles from the C ROMs.
    print("Test 10 - a missing S ROM means fix comes from the C ROMs")
    chk("fix source", rep["cartridge"]["fix_source"], "C ROMs (no S ROM)")
    chk("CHAFIO mentioned", "CHAFIO" in texts(rep), True)

    d = romset(os.path.join(tmp, "hasS"),
               p1=512 * KB, s1=128 * KB, m1=128 * KB, c1=1 * MB, c2=1 * MB)
    _, rep2 = run(d)
    chk("S ROM present", rep2["cartridge"]["fix_source"], "S ROM")
    print("  distinguished both ways.")
    print()

    # ---- 11: what it refuses to guess -----------------------------------
    print("Test 11 - protection is never inferred")
    chk("not inferable", rep2["cartridge"]["protection"], "not inferable")
    print("  sizes constrain the board; they do not name it.")
    print()

    print("========================================")
    if failures == 0:
        print(f"PASS - {checks} checks, 0 failures")
    else:
        print(f"FAIL - {checks} checks, {failures} failures")
    print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
