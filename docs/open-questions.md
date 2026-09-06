# Open Questions

Unresolved technical questions that materially affect NeoForge's design.

Each question states what we think, why we think it, what would settle it, and
what changes if the answer goes either way. Entries follow the evidence
convention in `CLAUDE.md`. A question leaves this file only when something
external answers it — reasoning our way to a conclusion is not an answer.

---

## Q1 — Does a fix-layer-only ROM require a working sprite serializer?

**Status:** `[PARTIALLY ANSWERED — 2026-09-05]` · **No, structurally** — with one
specific remaining risk. Blocks roadmap Phases 4, 6, 7.

### The question

On AES the sprite serializer (PRO-CT0 / NEO-ZMC2) lives in the cartridge, which
is why there is no such thing as a dumb EPROM-only AES cart.
`[VERIFIED: wiki AES cartridge]` Would a cartridge that only draws to the fix
layer boot and display correctly with no serializer present?

### What the HDL says

Read from `neogeodev/NeoGeoFPGA-sim` on 2026-09-05.

**1. On the cartridge, the fix path never touches the serializer.**
`Cartridge/aes_cha.v` wires the AES CHA board as:

```verilog
rom_s1   S1   (S_ADDR[16:0], FIXD);                              // fix -> edge
neo_zmc2 ZMC2 (CLK_12M, EVEN, LOAD, H, CR, GAD, GBD, DOTA, DOTB); // sprites
```

`FIXD` goes from the S ROM straight to the edge connector. The serializer's
only inputs are `CR` (the C ROMs) and its only outputs are `GAD`/`GBD` plus the
opacity flags. The two paths do not meet on the cart.
`[VERIFIED: aes_cha.v]`

**2. In NEO-B1, an opaque fix pixel beats sprites outright.**

```verilog
assign FIX_OPAQUE = |{FIX_COLOR};
assign PA_MUX_A   = FIX_OPAQUE ? {4'b0000, FIX_PAL_REG, FIX_COLOR} : RAM_MUX_OUT;
```

Where the fix pixel is non-zero, the sprite line-buffer output is not consulted
at all. `[VERIFIED: neo_b1.v]`

**3. `DOTA`/`DOTB` are not even inputs to NEO-B1.** They return to the LSPC, and
`neogeo.v:165` recomputes them locally as `{|GAD, |GBD}` rather than using the
cartridge's, with a testbench comment noting they are redundant "(saves 2
lines)". `[VERIFIED: neogeo.v, Testbench/testbench_1.v]`

**Conclusion so far:** wherever a fix pixel is opaque, an absent serializer
cannot affect what is displayed. The fix layer does not depend on it.

### The remaining risk, now stated precisely

Where a fix pixel is **transparent**, NEO-B1 falls through to `RAM_MUX_OUT` —
the sprite line buffers, written from `GAD`/`GBD`. With no serializer fitted,
those lines float at the connector. Whether that produces garbage depends on
whether the LSPC clocks line-buffer writes (`WE1`–`WE4`) when the sprite list
is empty, or whether the clearing path (`SS1`/`SS2`) holds them at zero.

**This is the whole remaining question.** It is narrower and more testable than
the original framing.

### Consequence for the test ROM — actionable now

ngdevkit's `01-helloworld` calls `ng_cls()`, which fills the fix map with tile
255, the **transparent** tile. Almost the entire screen is therefore the exact
case that is still at risk.

So the ROM that would test the no-serializer hypothesis on real hardware is
**not** stock hello world. It needs the fix layer filled with an *opaque* tile
edge to edge, so that no pixel falls through to the sprite path. That is a
small change to the example and it is worth making deliberately rather than
discovering the distinction on the bench.

### How to finish answering it

1. Read the LSPC sprite pipeline in `lspc2_a2.v` and determine whether `WE1`–
   `WE4` are asserted when no sprites are active. Free, and closes the question
   in simulation.
2. Bring up `Cartridge/aes_cha.v` with `neo_zmc2` removed and the `GAD`/`GBD`
   inputs driven to `x`, running a fix-only ROM. If the palette address bus
   stays clean, that is a strong simulated answer.
3. Definitive: measure it on hardware once a donor dev cart exists (Phase 5).

### What changes on each answer

**If confirmed:** the first NeoForge cartridge can be a plain EPROM board — no
CPLD, no donor chip. Text-only until the serializer lands, which is fine for a
development cartridge and useless for games. Phase 7 would move ahead of
Phase 6.

**If not:** the roadmap stands, and this file records why the obvious shortcut
does not exist — worth having in writing, because someone will suggest it again.

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

## Adding a question

Open one when a decision is being made on an assumption nobody has checked.
State what would settle it and what changes either way — a question with no
resolution path is a note, not an open question, and belongs somewhere else.
