#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
#
# NeoForge - fixes applied to the fetched NeoGeoFPGA-sim tree.
#
# The reference sources are GPL-3.0 and are NOT vendored into this repository;
# the Makefile clones them into ../../.reference and this script patches that
# working copy. Keeping our changes here rather than in a copied tree means
# they stay visible, reviewable, and easy to send upstream.
#
# Three of the four are genuine upstream bugs. All three should be reported.
# See docs/simulation-harness.md.
#
#   ./patch-reference.sh ../../.reference/NeoGeoFPGA-sim

set -e
REF="${1:?usage: patch-reference.sh <path to NeoGeoFPGA-sim>}"
cd "$REF"

say() { printf '  %s\n' "$1"; }

# -------------------------------------------------------------------------
# 1. BUG: System/neo_c1.v declares nPORT_ZONE twice
#
# It is an `output` in the port list and a `wire` again in the body. Icarus
# rejects this outright, which means the model as shipped does not compile
# with Icarus at all.
# -------------------------------------------------------------------------
if grep -q '^	wire nPORT_ZONE;' System/neo_c1.v; then
    sed -i.bak '/^	wire nPORT_ZONE;/d' System/neo_c1.v
    say "neo_c1.v: removed duplicate nPORT_ZONE declaration"
fi

# -------------------------------------------------------------------------
# 2. BUG: neogeo.v declares the ADPCM buses as inputs
#
# SDRAD and SDPAD are `input [7:0]` on neogeo's port list, but ym2610 declares
# them `inout` and the cartridge's pcm.v drives them. Verilator catches this as
# ASSIGNIN; Icarus is lax about it.
# -------------------------------------------------------------------------
if grep -q '^	input \[7:0\] SDRAD,' neogeo.v; then
    sed -i.bak 's/^	input \[7:0\] SDRAD,/	inout [7:0] SDRAD,/; s/^	input \[7:0\] SDPAD,/	inout [7:0] SDPAD,/' neogeo.v
    say "neogeo.v: SDRAD/SDPAD are inout, not input"
fi

# -------------------------------------------------------------------------
# 3. NOT A BUG, but needed: route CLK_24M to the CPU
#
# fx68k runs from a clock at twice the 68000 rate with phase enables, and
# CLK_24M already exists one level up. tg68 did not need it, so it was never
# routed down. See tg68.sv.
# -------------------------------------------------------------------------
if ! grep -q 'CLK_24M, CLK_68KCLK' CPUs/cpu_68k.v; then
    sed -i.bak 's/^	input CLK_68KCLK,/	input CLK_68KCLK,\n	input CLK_24M,/' CPUs/cpu_68k.v
    sed -i 's/^		\.clk(CLK_68KCLK),/		.clk(CLK_68KCLK),\n		.clk_2x(CLK_24M),/' CPUs/cpu_68k.v
    sed -i 's/cpu_68k M68KCPU(CLK_68KCLK, nRESET,/cpu_68k M68KCPU(CLK_68KCLK, CLK_24M, nRESET,/' neogeo.v
    say "cpu_68k.v + neogeo.v: routed CLK_24M to the CPU for fx68k's phase enables"
fi

# -------------------------------------------------------------------------
# 4. BUG, already known: the M1 bankswitcher truncates its bank value
#
# Cartridge/zmc.v declares `wire BANKSEL = SDA_U[15:8]` as a scalar, so the
# eight-bit value keeps only its LSB and every bank register can hold 0 or 1.
# Documented and demonstrated in sim/zmc_tb.v and docs/serializer.md. Patched
# here so the harness does not inherit it.
# -------------------------------------------------------------------------
if grep -q '^	wire BANKSEL = SDA_U\[15:8\];' Cartridge/zmc.v; then
    sed -i.bak 's/^	wire BANKSEL = SDA_U\[15:8\];/	wire [7:0] BANKSEL = SDA_U[15:8];/' Cartridge/zmc.v
    say "zmc.v: BANKSEL widened to 8 bits"
fi

printf '%s\n' "reference tree patched."

# -------------------------------------------------------------------------
# 5. NOT A BUG: export the signals an AES cartridge needs
#
# neogeo.v's port list was written for testbench_1, which drives an MVS cart.
# aes_cart.v needs six signals that exist inside neogeo as implicit wires but
# are never brought out: nRESET, nROMOEL, nROMOEU, CLK_24M, SDRD0 and SDRD1.
#
# Appended to the end of the port list so positional instantiations elsewhere
# keep working. Our own testbench connects by name.
# -------------------------------------------------------------------------
if ! grep -q 'NeoForge: exported for the AES cartridge' neogeo.v; then
    python3 - "$PWD/neogeo.v" <<'PY'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8', errors='surrogateescape').read()
old = "\toutput VIDEO_SYNC\n"
new = ("\toutput VIDEO_SYNC,\n\n"
       "\t// NeoForge: exported for the AES cartridge model. These all exist\n"
       "\t// as implicit wires driven by submodules; only the port list was\n"
       "\t// missing them, because it was written for the MVS testbench.\n"
       "\toutput nRESET,\n"
       "\toutput nROMOEL, nROMOEU,\n"
       "\toutput CLK_24M,\n"
       "\toutput SDRD0, SDRD1\n")
assert old in s, "neogeo.v: VIDEO_SYNC port not found"
io.open(p, 'w', encoding='utf-8', errors='surrogateescape').write(s.replace(old, new, 1))
PY
    say "neogeo.v: exported nRESET, nROMOEL/U, CLK_24M, SDRD0/1 for aes_cart"
fi
