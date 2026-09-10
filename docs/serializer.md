# NEO-ZMC2 — what the cartridge chip actually does

On AES this chip lives **inside the cartridge**. It is the reason there is no
such thing as a dumb ROM-only AES cart that can display sprites, and it is the
single part NeoForge must either buy, rebuild, or prove it can do without.

This document is what we know from simulation. Everything here is derived from
`neogeodev/NeoGeoFPGA-sim` (GPL-3.0) and checked with self-checking testbenches
in `sim/`. **None of it is from a datasheet**, because no datasheet is public.

    cd sim && make        # runs both testbenches

Deliberately not consulted: `neogeodev/NeoChips`, which contains a NEO-ZMC2
implementation under GPL-2.0-only. That licence cannot be combined with ours.
See `LICENSE.md`. Nothing in this document was derived from it.

---

## The chip is two unrelated blocks in one package

`Video/neo_zmc2.v` names both:

```verilog
module neo_zmc2(...);
    //zmc2_zmc ZMC2ZMC(SDRD0, SDA_L, SDA_U, MA);        // commented out
    zmc2_dot ZMC2DOT(CLK_12M, EVEN, LOAD, H, CR, GAD, GBD, DOTA, DOTB);
endmodule
```

| Block | Job | Talks to |
|---|---|---|
| `zmc2_dot` | Serializes sprite pixels | LSPC, via `GAD`/`GBD` |
| `zmc2_zmc` | Banks the Z80's program ROM | Z80, via `MA[21:11]` |

They share nothing — not a clock, not a signal, not a purpose. They are in one
package because both needed to be in the cartridge and SNK had a package to
fill. Treat them as two chips that happen to be soldered down as one.

**`zmc2_zmc` does not exist as a module in NeoGeoFPGA-sim.** Only the
commented-out instantiation above names it. `Cartridge/zmc.v` has the identical
port list and is instantiated in `mvs_cha.v` with exactly those four signals, so
we treat `zmc` as the same logic under a different name. `[UNVERIFIED]` — that
identification is from the port list and the usage, not from an upstream
statement.

---

## Block 1 — `zmc2_dot`, the sprite serializer

**Testbench:** `sim/zmc2_dot_tb.v`. **Result:** 20 checks, 0 failures.
`[MEASURED: 2026-09-05]`

Twenty-five lines of Verilog: a 32-bit shift register, a two-bit shift whose
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

Inferred from the HDL, then confirmed by the testbench round-tripping known
pixel values:

| Shift register bits | C ROM byte | Contributes |
|---|---|---|
| `SR[31:24]` | byte 0 | pixel bit 3 (MSB) |
| `SR[23:16]` | byte 1 | pixel bit 2 |
| `SR[15:8]`  | byte 2 | pixel bit 1 |
| `SR[7:0]`   | byte 3 | pixel bit 0 (LSB) |

Within each byte, bit 7 is the **leftmost** of the eight pixels.

**A caveat the reference itself raises.** How C1/C2 data lands in those 32 bits
is not settled upstream. `aes_cha.v` says `assign CR = {C1DATA, C2DATA};` with
the comment *"Other way around ?"*, and `mvs_cha.v` byteswaps differently again
with a `Todo`. The bitplane layout above is what `zmc2_dot` does with whatever
it is handed; **which C ROM byte arrives on which of those lines is a separate
question that the model is openly unsure about.** Our own test ROM renders
correctly in GnGeo, so ngdevkit and GnGeo agree with each other — that is not
the same as either agreeing with silicon.

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

## Block 2 — `zmc2_zmc`, the Z80 mapper

**Testbench:** `sim/zmc_tb.v`. **Result:** 45 checks, 0 failures.
`[MEASURED: 2026-09-10]`

The Z80 has 16 address lines. M ROMs are larger than 64 KB. Four bank registers
redirect four windows of Z80 address space into an 11-bit upper address,
`MA[21:11]`, which is concatenated with `SDA[10:0]` to address the M ROM.

| Z80 range | Window | Register | `MA` composition | Reach |
|---|---|---|---|---|
| `0000-7FFF` | 32 KB | *none* | `{6'b0, A[15:11]}` | pass-through |
| `8000-BFFF` | 16 KB | `RANGE_3` | `{RANGE_3, A[13:11]}` | 4 MB |
| `C000-DFFF` | 8 KB | `RANGE_2` | `{1'b0, RANGE_2, A[12:11]}` | 2 MB |
| `E000-EFFF` | 4 KB | `RANGE_1` | `{2'b0, RANGE_1, A[11]}` | 1 MB |
| `F000-F7FF` | 2 KB | `RANGE_0` | `{3'b0, RANGE_0}` | 512 KB |

Smaller window, smaller reach — each register is 8 bits, so the window size sets
how far 256 banks can span. The testbench checks each window against an
independently computed `bank × window_size + offset` rather than against a
restatement of the same expression:

```
  reg     bank  Z80 addr  ->  M1 byte addr   expected
  RANGE_3   5a     9abc    ->     169abc       169abc
  RANGE_2   33     cdef    ->     066def       066def
  RANGE_1   77     eabc    ->     077abc       077abc
  RANGE_0   11     f123    ->     008923       008923
```

### How a bank gets programmed

Not by a write. By a **read**: `SDA_L` (the low address bits) picks the
register, `SDA_U` (the high address byte) carries the value, and the register
latches on the rising edge of `SDRD0`. On a Z80 `IN A,(n)` the accumulator
appears on the high address byte — so `ld a,bank / in a,(port)` sets a bank, and
the byte the Z80 reads back is discarded.

### Three things the model tells us that are easy to miss

**The registers have no reset.** `zmc.v` carries the comment `// Initialize ?`
and models them as X. A Z80 program must therefore program all four registers
before executing from any banked window, or stay entirely inside the
pass-through region. `[UNVERIFIED]` on real silicon — the chip may well power up
at zero. Do not depend on it.

**`F800-FFFF` aliases `F000-F7FF`.** `MA` for the top window is
`{3'b000, RANGE_0}` and ignores `A11`. Invisible in practice, because Z80 work
RAM is decoded up there on the motherboard and never reaches the cartridge — but
a cartridge that mapped ROM into `F800` would find it mirrored.

**The M1 path exists in two configurations,** and which one a cartridge uses
changes how much ROM is reachable without banking:

| Configuration | M ROM address | Unbanked reach |
|---|---|---|
| No ZMC in the path (`rom_m1 M1(SDA, ...)`, commented *"Joyjoy doesn't use ZMC"*) | `SDA[15:0]` | 64 KB, all of it |
| ZMC in the path | `{MA[21:11], SDA[10:0]}` | 32 KB, then banked |

---

## The reference has a width bug, and it is worth knowing about

`zmc.v` line 27:

```verilog
wire BANKSEL = SDA_U[15:8];      // BANKSEL is one bit
```

`BANKSEL` is declared as a scalar. Verilog truncates the 8-bit right-hand side
to the least significant bit, so only `SDA_U[8]` survives, and every bank
register can hold **only 0 or 1**:

```
  wrote RANGE_3 = 5a
    reference MA = 000  -> bank 000
    corrected MA = 2d0  -> bank 05a
```

This is a bug in the simulation model, not a property of the silicon — the
surrounding code plainly intends eight bits, and the author's own comments
(`RANGE_2` "512 ? Can only access max. 2MB ROM") only make sense with an 8-bit
register. It is invisible in normal use because `testbench_1.v` never
instantiates `zmc` at all.

`sim/zmc_tb.v` therefore carries `zmc_fixed`, a corrected model differing in
exactly one character class:

```verilog
wire [7:0] BANKSEL = SDA_U[15:8];
```

Everything else is preserved verbatim, including the missing reset, so it stays
a faithful model of the chip rather than an improvement of it. The testbench
runs both and shows the divergence rather than quietly using the fixed one.

**To do:** report this upstream. It is a one-line fix and the project should get
it back. See `roadmap.md` Phase 3.

---

## What this means for NeoForge

**A fix-layer-only development cartridge needs neither block.**

- Not `zmc2_dot`: the fix layer bypasses the serializer entirely, and a
  cartridge that holds `DOTA`/`DOTB` low simply cannot draw sprites. This is
  `docs/open-questions.md` Q1, answered in simulation and now awaiting a
  hardware result — see `rom/RESULTS.md`.
- Not `zmc2_zmc`: **a Z80 driver that fits in the unbanked region needs no
  mapper.** 32 KB in the ZMC configuration, 64 KB without. A minimal sound
  driver is far smaller than either.

That is a stronger statement of Q1 than we had, and it makes the first PCB
simpler than the roadmap assumed: no custom silicon, no CPLD, no donor chip.
Just ROMs, address decoding, and two grounded pins.

**A cartridge that runs commercial games needs both.** Any game with an M ROM
over 64 KB banks it, and any game with sprites needs the serializer. That is
Phase 6 and Phase 9, and nothing here makes them easier.

**The serializer is a bounded problem.** A 32-bit shift register, a mux, four
8-bit registers and some address arithmetic — comfortably inside a small CPLD.
What stays hard is unchanged and is where the effort should go:

- meeting real AES bus timing, which nobody has published and we have not measured
- 5V tolerance across a 200-pin connector
- proving equivalence against hardware rather than against a model

---

## What is still unknown

- **Which C ROM byte lands on which serializer input.** The reference is
  explicitly unsure, in two files, in two different ways. Settling this needs
  either a hardware capture or a careful read of a known-good ROM set against
  the wiki's graphics format.
- **Whether the bank registers reset to a known value on power-up.**
- **Everything about timing.** These testbenches prove function, not timing. A
  model that produces the right values at the wrong moment is still a cartridge
  that does not boot. `docs/open-questions.md` Q3.
- **Whether `zmc` really is `zmc2_zmc`.** The port list and usage say yes.
  Nothing authoritative does.

---

*Corrections welcome and actively wanted. Open an issue.*
