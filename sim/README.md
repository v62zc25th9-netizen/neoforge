# Simulation

Verilog simulation of AES cartridge logic, starting with the piece NeoForge has
to reproduce: NEO-ZMC2.

    make        # fetch the reference sources, build, run both testbenches
    make wave-dot / make wave-zmc    # same, then open a waveform in GTKWave
    make clean

Requires Icarus Verilog (`brew install icarus-verilog`, `apt install iverilog`).

## What is here

| Testbench | Device under test | Result |
|---|---|---|
| `zmc2_dot_tb.v` | `zmc2_dot` — the sprite serializer datapath | 20 checks, 0 failures `[MEASURED: 2026-09-05]` |
| `zmc_tb.v` | `zmc` — the Z80 mapper, NEO-ZMC2's other half | 45 checks, 0 failures `[MEASURED: 2026-09-10]` |

**The analysis lives in [`docs/serializer.md`](../docs/serializer.md)** — what
each block does, the bitplane layout, the bank windows, what it means for the
project, and what is still unknown. This file is just how to run it.

`zmc_tb.v` also carries `zmc_fixed`, our own corrected copy of the reference.
The reference declares its bank-select wire as a scalar and truncates an 8-bit
value to one bit, so bank registers can only hold 0 or 1. The testbench
instantiates both and shows the divergence rather than quietly substituting the
fixed one. Details and the upstream report are in `docs/serializer.md`.

## On not vendoring the reference sources

`zmc2_dot.v` and `zmc.v` come from `neogeodev/NeoGeoFPGA-sim` and are
**GPL-3.0-or-later**. The Makefile clones the upstream repository into
`.reference/` and compiles against it there rather than copying the files in, so
foreign sources stay in their own tree under their own terms and this
repository's licensing statements stay true.

NeoForge's HDL is GPL-3.0-or-later for exactly this reason — the choice is
forced by the lineage, not preferred. `neogeodev/NeoChips` also implements
NEO-ZMC2 but is GPL-2.0-**only**, which cannot be combined with ours; nothing
here was derived from it. See [`LICENSE.md`](../LICENSE.md).

## The whole-console harness

Running a NeoForge ROM through a full model of the Neo Geo — and sweeping the
cartridge's access time in it — has been scoped and is buildable.
See [`docs/simulation-harness.md`](../docs/simulation-harness.md).
`[MEASURED: 2026-09-12]`

Short version: the model compiles under Icarus with everything resolved except
the CPU, which is VHDL. **fx68k** under **Verilator 5** replaces it — and
improves on it, since Verilator 5 honours `#delay` and fx68k is
microcode-accurate where TG68K is not. Every input has an open equivalent in
ngdevkit, so the harness needs no dumps.

**It now lints clean.** `[MEASURED: 2026-09-12]` `harness/` holds the fx68k
shim, the patch set and a Makefile — `cd harness && make lint`. It does not run
yet; `harness/README.md` is precise about what remains, and the clock-phase
alignment is the real risk.

## Next

- [ ] Report the `BANKSEL` width bug upstream — one line, and they should have it
- [ ] Report the `neo_c1.v` duplicate declaration upstream — `nPORT_ZONE` is
      declared both as an `output` and as a `wire`, so the model **does not
      compile with Icarus Verilog at all** as shipped. Also one line.
- [ ] Report the `neogeo.v` ADPCM bus direction upstream — `SDRAD` and `SDPAD`
      are declared `input` there while `ym2610` declares them `inout` and the
      cartridge drives them. Verilator rejects it; Icarus is lax. One line.
- [ ] Drive the serializer from real C ROM data (our own tiles) rather than
      synthetic lines, and settle the C1/C2 byte-order question the reference
      raises in two places and answers in neither
- [ ] Bring up `Cartridge/aes_cha.v` — the full AES CHA board model
- [ ] Compare against `FusionConverter`'s CPLD sources (licence unchecked first)
- [ ] Eventually: compare simulation against `[MEASURED]` captures from real
      hardware, which is roadmap Phase 5 and the only thing that settles it
