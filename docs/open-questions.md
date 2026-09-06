# Open Questions

Unresolved technical questions that materially affect NeoForge's design.

Each question states what we think, why we think it, what would settle it, and
what changes if the answer goes either way. Entries follow the evidence
convention in `CLAUDE.md`. A question leaves this file only when something
external answers it — reasoning our way to a conclusion is not an answer.

---

## Q1 — Does a fix-layer-only ROM require a working sprite serializer?

**Status:** `[ANSWERED IN SIMULATION — 2026-09-06]` · **No.** A fix-layer-only
AES cartridge does not need a serializer — it needs **DOTA and DOTB tied low.**

### The answer

Traced through `neogeodev/NeoGeoFPGA-sim`. Four findings, in the order they
close the question.

**1. On the cartridge, the fix path never meets the serializer.**
`Cartridge/aes_cha.v`:

```verilog
rom_s1   S1   (S_ADDR[16:0], FIXD);                              // fix -> edge
neo_zmc2 ZMC2 (CLK_12M, EVEN, LOAD, H, CR, GAD, GBD, DOTA, DOTB); // sprites
```

`FIXD` runs from the S ROM straight to the edge connector. `[VERIFIED: aes_cha.v]`

**2. In NEO-B1, an opaque fix pixel beats sprites outright.**

```verilog
assign FIX_OPAQUE = |{FIX_COLOR};
assign PA_MUX_A   = FIX_OPAQUE ? {4'b0000, FIX_PAL_REG, FIX_COLOR} : RAM_MUX_OUT;
```

`[VERIFIED: neo_b1.v]`

**3. DOTA/DOTB gate sprite line-buffer writes.** This is the mechanism that
decides everything. In `Video/lspc2_a2.v`, with the author's own comment:

```verilog
// Enable writes for opaque pixels only
assign T17A_OUT = ~&{DOTA, ~T50A_OUT};
assign T22B_OUT = ~&{DOTB, ~T40A_OUT};
```

Those feed the `WE1`–`WE4` line-buffer write enables. **With DOTA and DOTB low,
no sprite-pixel write can fire** — the only writes remaining are the periodic
clearing pulses gated by `SS1`/`SS2`. `[VERIFIED: lspc2_a2.v]`

**4. Clearing writes ignore GAD/GBD entirely.** `Video/linebuffer.v`:

```verilog
assign COLOR_GATED  = COLOR_INDEX | {4{CLEARING}};
assign DATA_IN[3:0] = COLOR_GATED;
assign DATA_IN[11:4] = PAL_REG | {8{CLEARING}};
```

When `CLEARING` is asserted, `DATA_IN` is forced to all ones — palette entry
`0xFFF`, the Neo Geo backdrop colour — regardless of what `COLOR_INDEX` (that
is, `GAD`/`GBD`) happens to be. `[VERIFIED: linebuffer.v]`

### Therefore

Hold DOTA and DOTB low and the sprite path writes nothing but backdrop. The
`GAD`/`GBD` lines can float at the connector with no serializer fitted and it
does not matter, because nothing ever latches them. Transparent fix pixels fall
through to a line buffer containing the backdrop colour, which is exactly what
they should show.

**A fix-only AES development cartridge is a plain EPROM board plus two pins
tied to ground.**

### Caveats — this is simulation, not hardware

- `[VERIFIED: HDL]`, not `[MEASURED]`. NeoGeoFPGA-sim is an excellent
  reverse-engineered model traced from die photographs, but it is a model.
- The LSPC's real input behaviour with these pins undriven is unknown. Tying
  them low is the correct action either way — it removes the question rather
  than betting on a pull-down existing.
- Sprites will not display. That is the entire point and it is fine for a
  development cartridge. The AES BIOS boot animation is sprite-based, so expect
  it to be absent or backdrop-coloured; the system should still run.
- Nothing here has been checked against real silicon. It becomes `[MEASURED]`
  at roadmap Phase 5 and not before.

### What this changes

- **Phase 7 can precede Phase 6.** The first NeoForge PCB needs no CPLD, no
  donor chip, and no custom silicon: P/S/M/V ROMs, address decoding, and DOTA
  and DOTB grounded.
- **Q2 stops blocking the first board** and becomes a Phase 8 concern.
- The claim that "there is no such thing as a dumb ROM-only AES cart" needs
  qualifying throughout the docs. The accurate statement is that there is no
  dumb AES cart *that can display sprites*.

### Still to confirm

- [ ] Update `docs/cartridge-architecture.md` §1, which currently states the
      unqualified version.
- [ ] Check whether `nullbios` touches sprite registers during boot.
- [ ] Simulate `aes_cha.v` with `neo_zmc2` removed, `GAD`/`GBD` driven to `x`
      and DOTA/DOTB low, and confirm the palette address bus stays clean.
- [ ] Measure on hardware. Phase 5.

---

## Q2 — Which serializer strategy for the first NeoForge hardware?

**Status:** `[UNVERIFIED]` · Carried over from `CLAUDE.md` · **Blocks:** Phase 6

Three paths, not two — the third only surfaced when the prior art was catalogued:

1. **Donor chip.** Harvest a PRO-CT0 or NEO-ZMC2 from a dead cart. Fastest to
   something that boots; not reproducible at scale, and every unit consumes an
   original cartridge.
2. **Own CPLD implementation.** Derived from FusionConverter and
   NeoGeoFPGA-sim. The most work, and the only path that makes NeoForge's
   serializer a contribution rather than a dependency.
3. **`neogeodev/NeoChips` NEO-ZMC2.** An existing replacement in programmable
   logic, GPL-2.0, buyable assembled or built from published sources.
   `[VERIFIED: repo page, folder list, GPL-2.0 license]`

Path 3 did not exist in the original framing and changes the calculus: it
unblocks Phases 7–9 immediately while path 2 proceeds in parallel, and it makes
path 1 hard to justify. Note the GPL-2.0 licensing implication if its sources
are derived from rather than used as a component.

**Update 2026-09-05:** the serializer's pixel datapath is now simulated and
characterised — see `sim/README.md`. It is a 32-bit shift register and an
output mux, comfortably inside a small CPLD. That does not make path 2 easy
(bus timing, 5V tolerance and the `zmc2_zmc` bankswitching half are all
unaddressed), but it does make it a bounded task rather than an open question,
which weakens the case for path 1.

**Dependent on Q1.** If a fix-only cart needs no serializer, this question stops
blocking the first PCB and becomes a Phase 8 concern instead.

---

## Q3 — Can NeoForge run at zero added wait states?

**Status:** `[UNVERIFIED]` · Opened 2026-09-06 · **Blocks:** Phases 7, 8, 9 ·
**This is an acceptance criterion, not just a question.**

### The question

The AES cartridge does not merely supply data — it tells the console how long
to wait for it. `Cartridge/aes_prog.v` drives four signals back to the
motherboard:

```verilog
assign nROMWAIT = 1'b1;    // Waitstate configuration
assign nPWAIT0  = 1'b1;
assign nPWAIT1  = 1'b1;
assign PDTACK   = 1'b1;
```

NEO-C1 consumes them and inserts wait cycles into 68000 bus accesses
accordingly (`System/c1_wait.v`). `[VERIFIED: aes_prog.v, neo_c1.v, c1_wait.v]`

On this model — a Joy Joy Kid cartridge — all four are tied high: **zero added
wait states.** A cartridge whose memory cannot meet the original access time
must assert them.

### Why it matters more than it looks

A cart running with extra wait states does not crash, corrupt, or glitch. It
runs **slower** — uniformly, on every P ROM read, forever. Animation pacing,
input-to-action latency and physics timing all shift by a small constant.

This is the difference between "the game runs" and "the game runs the way it
did." It is invisible in an emulator, invisible in a screenshot, and invisible
in a feature list. It is exactly the class of difference that people who grew
up with the hardware detect immediately and cannot always articulate.

**Therefore: matching the original cartridge's wait-state configuration is an
acceptance criterion for NeoForge, not an optimisation.** A cart that boots
every game but needs a wait state has not succeeded.

### What is not known

1. **What access time must actually be met.** Original mask ROM timings for AES
   carts are not recorded in this repo, and no measured AES bus timing exists
   publicly at all. This is the same gap roadmap Phase 5 exists to close.
2. **What the wait signals actually encode.** The reference model itself is
   unsure — `c1_wait.v` carries the comments `0~1 or 1~2 wait cycles ?` and
   `Needs checking`. The best open model of this hardware does not know, which
   means a measured answer would be a contribution beyond NeoForge.
3. **Whether real carts vary.** If some titles ship with wait states asserted,
   "zero" is the wrong universal target and the cart may need to reproduce the
   original's configuration per title rather than always driving high.

### Design consequences

- **Parallel NOR flash** is likely fine on raw access time and is the
  conservative choice for early hardware.
- **Anything with a fetch behind it** — SDRAM, an SD-backed cache, an FPGA
  arbitrating shared memory — has to hide that latency completely or assert
  wait states. This is a plausible reason Terraonion's NeoSD carries two FPGAs
  and substantial RAM rather than streaming on demand. `[UNVERIFIED]`
- The decision belongs in Phase 7's memory selection, and it should be made
  against measured numbers from Phase 5 rather than datasheet optimism.

### How to settle it

1. Record mask ROM part numbers and access times from donor cart photographs
   and the arcade-collector board scans. Free, and gives a target.
2. Check whether any documented AES cartridge asserts these signals.
3. Definitive: scope the four signals and the 68k bus on a real AES running an
   original cartridge, and again running NeoForge hardware. Any difference in
   wait behaviour is a defect. Phase 5.

### Test

Once hardware exists, this is directly testable without subjective judgement:
run a known cycle-counted loop from P ROM on an original cartridge and on
NeoForge hardware, and compare elapsed time. Identical means identical feel.

---

## Adding a question

Open one when a decision is being made on an assumption nobody has checked.
State what would settle it and what changes either way — a question with no
resolution path is a note, not an open question, and belongs somewhere else.
