# Simulation

Verilog simulation of AES cartridge logic, starting with the piece NeoForge
has to reproduce: the sprite serializer.

    make        # fetch the reference sources, build, run
    make wave   # same, then open the waveform in GTKWave
    make clean

Requires Icarus Verilog (`brew install icarus-verilog`, `apt install iverilog`).

## On not vendoring the reference sources

`zmc2_dot.v` comes from `neogeodev/NeoGeoFPGA-sim` and is **GPL-3.0**. This
repository is currently MIT. Copying that file in would create a licence
conflict nobody has resolved, so the Makefile clones the upstream repo into
`.reference/` instead and compiles against it there. The GPL source stays in
its own tree under its own terms, and NeoForge ships only the testbench.

This is a workaround, not a decision. See roadmap Phase 0 — the licensing split
has to be settled before any of this becomes a real deliverable.

---

## `zmc2_dot_tb.v` — the sprite serializer datapath

**What it tests:** `zmc2_dot`, the pixel-serializing core of NEO-ZMC2 / PRO-CT0,
written by Kyuusaku. On AES this chip lives in the cartridge, which is the
reason a plain EPROM-only AES cart cannot work.

**Result:** 20 checks, 0 failures. `[MEASURED: 2026-09-05]`

### What the serializer actually does

Twenty-five lines of Verilog. A 32-bit shift register, a two-bit shift whose
direction is chosen by `H`, and a 4:1 output mux selected by `{EVEN, H}`.

Per load it takes 32 bits of C ROM — four bitplane bytes covering one 8-pixel
line of a sprite tile — and emits **two 4-bit packed pixels per 12 MHz clock,
four clocks per tile line**:

```
C ROM line = 011e66aa
  planes: b0=00000001 b1=00011110 b2=01100110 b3=10101010

  clk | GBD GAD | DOTB DOTA
  ----+---------+----------
   0  |  1   2  |   1    1
   1  |  3   4  |   1    1
   2  |  5   6  |   1    1
   3  |  7   8  |   1    1
```

Eight pixels with colour indices 1..8, packed into four bitplanes, coming back
out in order. That is the whole function.

### Bitplane layout `[MEASURED: 2026-09-05]`

Inferred from the HDL and then confirmed by the testbench round-tripping known
pixel values:

| Shift register bits | C ROM byte | Contributes |
|---|---|---|
| `SR[31:24]` | byte 0 | pixel bit 3 (MSB) |
| `SR[23:16]` | byte 1 | pixel bit 2 |
| `SR[15:8]`  | byte 2 | pixel bit 1 |
| `SR[7:0]`   | byte 3 | pixel bit 0 (LSB) |

Within each byte, bit 7 is the **leftmost** of the eight pixels.

### `H` is horizontal flip

Same data, `H` inverted, comes back reversed in pairs — 7,8 / 5,6 / 3,4 / 1,2.
Pairs stay together because two pixels are emitted per clock; the sequence of
pairs runs backwards. Flip is free: it is the shift direction, not a separate
data path.

### `DOTA` / `DOTB` are only opacity

```verilog
{DOTA, DOTB} <= {|GAD, |GBD};
```

Nothing more than "is this pixel non-zero" — colour 0 is transparent on the Neo
Geo. Confirmed by tests 3 and 4: an all-zero line holds both low, and an
alternating line tracks per-pixel.

They are also **not consumed by NEO-B1**. They return to the LSPC, and
`neogeo.v` recomputes them locally as `{|GAD, |GBD}` rather than using the
cartridge's, with the testbench noting they are redundant. The real payload
crossing the connector is `GAD`/`GBD`.

---

## Why this matters to the project

The serializer has been the project's stated hardest problem — the reason
programmable logic had to come before a first PCB. Having read it: the pixel
datapath is a shift register and a mux, comfortably inside a small CPLD.

That does **not** make the hardware easy. What remains hard is unchanged, and
is where the effort should go:

- meeting real AES bus timing, which nobody has published and we have not measured
- 5V tolerance across a 200-pin connector
- whatever `zmc2_zmc` (the M1 bankswitching half of NEO-ZMC2) turns out to require
- proving equivalence against hardware rather than against a model

But "implement the serializer" is now a bounded task with a published
reference, a testbench, and a passing result — rather than an open question.

## Next

- [ ] Simulate `neo_zmc2` whole, including the `zmc2_zmc` bankswitching half
- [ ] Drive it from real C ROM data (homebrew tiles) rather than synthetic lines
- [ ] Bring up `Cartridge/aes_cha.v` — the full AES CHA board model
- [ ] Compare against `FusionConverter`'s CPLD sources
- [ ] Eventually: compare simulation against `[MEASURED]` captures from real
      hardware, which is roadmap Phase 5 and the only thing that settles it
