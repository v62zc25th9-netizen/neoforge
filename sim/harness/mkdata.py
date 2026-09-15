#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the $readmemh data files the NeoGeoFPGA-sim model reads.

    python3 mkdata.py <rom-dir> <out-dir>

<rom-dir> holds the unpacked contents of ngdevkit's neogeo.zip (nullbios) and
our own cartridge ROM set. Both are open — see ../../docs/simulation-harness.md
for why that matters more than it looks.

BYTE ORDER
----------
This is the part that fails silently if you get it wrong, so it was settled by
evidence rather than by convention.

Both aes-bios.bin and our own p1 begin `10 00 00 f3 c0 00 ...`. Read as-is that
is SSP=0x100000f3, PC=0xc0000043 - a stack pointer that masks to 0x0000f3,
which is nonsense. Read byte-swapped it is **SSP=0x0010f300** (the top of the
Neo Geo's 64 KB work RAM at $100000) and **PC=0x00c04300** (inside the BIOS at
$C00000). Only one of those is a machine that boots.

So both files are stored byte-swapped relative to 68000 order. The two ROM
models then disagree about whose job it is to undo that:

    rom_p1.v      assign OUT = {DATAOUT[7:0], DATAOUT[15:8]}   <- swaps
    rom_sp.v      assign OUT = DATA                            <- does not

Hence `p1` is stored big-endian and left for the model to swap, while `sps2` is
pre-swapped here. Same input bytes, opposite treatment, because the models
differ. `[MEASURED: 2026-09-15]`

SPARSE FILL
-----------
The model's arrays are sized for the largest cartridges - 4 MB per C ROM, 4 MB
per V ROM. Ours are mostly empty, and writing 75 MB of text so Verilator can
parse zeroes back is wasteful. We write only the real data; Verilator
zero-initialises the rest.

Note that is Verilator behaviour. Icarus leaves unwritten entries as X, and X
propagating out of a ROM is the kind of failure that looks like a timing bug.
If this harness is ever run under Icarus, fill the arrays completely.
"""

from __future__ import annotations

import os
import sys

PER_LINE = 16


def words_be(data: bytes) -> list[int]:
    """16-bit words, big-endian: the file's own byte order."""
    return [(data[i] << 8) | data[i + 1] for i in range(0, len(data) - 1, 2)]


def words_swapped(data: bytes) -> list[int]:
    """16-bit words with the byte pair swapped."""
    return [(data[i + 1] << 8) | data[i] for i in range(0, len(data) - 1, 2)]


def write_hex(path: str, values: list[int], digits: int) -> None:
    with open(path, "w") as f:
        for i in range(0, len(values), PER_LINE):
            f.write(" ".join(f"{v:0{digits}x}" for v in values[i:i + PER_LINE]))
            f.write("\n")


def emit(out_dir, name, values, digits, note=""):
    path = os.path.join(out_dir, name)
    write_hex(path, values, digits)
    kind = f"{digits * 4}-bit"
    print(f"  {name:<26} {len(values):>9} x {kind:<7} "
          f"{os.path.getsize(path) // 1024:>6} KB  {note}")


def read(rom_dir: str, name: str) -> bytes:
    p = os.path.join(rom_dir, name)
    if not os.path.exists(p):
        raise SystemExit(f"mkdata: missing {p}")
    with open(p, "rb") as f:
        return f.read()


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    rom_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    print(f"building $readmemh data in {out_dir}")
    print()

    # ---- BIOS side, all from nullbios ---------------------------------
    bios = read(rom_dir, "aes-bios.bin")          # AES, not the MVS sp-s2
    emit(out_dir, "rom_sp-s2_fast.txt", words_swapped(bios), 4,
         "nullbios AES, pre-swapped")

    emit(out_dir, "rom_sfix.txt", list(read(rom_dir, "sfix.sfix")), 2,
         "nullbios fix tiles")

    # The LO ROM array is 64 KB but the file is 128 KB of two identical
    # halves. Verified rather than assumed: both halves compare equal.
    lo = read(rom_dir, "000-lo.lo")
    half = len(lo) // 2
    if lo[:half] != lo[half:]:
        raise SystemExit("mkdata: 000-lo.lo halves differ - do not truncate blindly")
    emit(out_dir, "rom_l0.txt", list(lo[:65536]), 2,
         "zoom table, mirrored halves confirmed")

    # ---- cartridge side, all ours -------------------------------------
    p1 = read(rom_dir, "neoforge-fixtest-p1.p1")
    emit(out_dir, "data_p1_skipclear.txt", words_be(p1), 4,
         "ours; rom_p1.v swaps on output")

    emit(out_dir, "data_s1.txt", list(read(rom_dir, "neoforge-fixtest-s1.s1")), 2,
         "ours")
    emit(out_dir, "data_m1.txt", list(read(rom_dir, "neoforge-fixtest-m1.m1")), 2,
         "ours")
    emit(out_dir, "data_v1.txt", list(read(rom_dir, "neoforge-fixtest-v1.v1")), 2,
         "ours")
    emit(out_dir, "data_v2.txt", [], 2, "empty - one ADPCM region")

    # rom_c*.v do NOT swap on output, unlike rom_p1.v. Stored big-endian.
    # [UNVERIFIED] - this ROM barely matters for a fix-layer test (the C data
    # is one solid tile) and aes_cha.v itself carries an "Other way around ?"
    # comment about how C1/C2 combine. Revisit before trusting sprite output.
    emit(out_dir, "data_c1.txt", words_be(read(rom_dir, "neoforge-fixtest-c1.c1")), 4,
         "ours [UNVERIFIED byte order]")
    emit(out_dir, "data_c2.txt", words_be(read(rom_dir, "neoforge-fixtest-c2.c2")), 4,
         "ours [UNVERIFIED byte order]")
    emit(out_dir, "data_c3.txt", [], 4, "empty")
    emit(out_dir, "data_c4.txt", [], 4, "empty")

    # ---- RAM images: empty, so Verilator zero-fills --------------------
    for n in ("raminit_68kram_l", "raminit_68kram_u", "raminit_sram_l",
              "raminit_sram_u", "raminit_z80", "raminit_memcard",
              "data_pal_l", "data_pal_u", "data_fvram_l", "data_fvram_u",
              "data_svram_l", "data_svram_u"):
        emit(out_dir, f"{n}.txt", [], 2, "zero-filled by the simulator")

    print()
    print("done. 24 files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
