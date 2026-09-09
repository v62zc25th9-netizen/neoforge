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
- [x] **Test ROM built, running, and validated by a positive control**
      `[MEASURED: GnGeo AES mode, 2026-09-09]` — see `rom/`. An opaque fix field
      with one transparent window onto the sprite line buffer, alternating a
      screen-filling sprite on and off every two seconds. **The window
      alternates green and red as designed**, which is the point: it
      demonstrates the window can register sprite activity, so a green reading
      is evidence rather than an artifact of a test that cannot fail. Without
      that control, "the sprite path is quiet" and "this ROM cannot see the
      sprite path" would have looked identical.
      The emulator models the sprite path correctly and therefore cannot fail
      this test; what it confirms is the instrument. The results that matter are
      on silicon — see the two listed in `rom/README.md`, one of which needs no
      hardware work at all.
- [x] **Font glyph backgrounds are transparent** — found the hard way when the
      first build rendered backdrop green behind every character. Strengthens
      the point above: in a stock text ROM, the inside of every letter is a
      window onto the sprite path, not just the cleared background. Anyone
      testing a serializer-less cart with stock hello world is mostly looking at
      the sprite path while believing they are looking at the fix layer.
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

**Update 2026-09-08 — the licensing picture, and a much better option.**

Both synthesizable references were checked. `FusionConverter` also ships a bare
GPL-2.0 licence, so paths 2 and 3 sit on the same footing, and Q2's original
wording — "derived from FusionConverter *and* NeoGeoFPGA-sim" — was never
possible as written if either is v2-only, because GPL-2.0-only and GPL-3.0
cannot be combined.

Neither project states a version anywhere but the licence file, which under
GPLv2 section 9 arguably lets a recipient choose any version. See `LICENSE.md`.
`[UNVERIFIED]` — **ask Furrtek rather than assume.** This is the single cheapest
action that could unblock the whole serializer path.

**And NeoChips is more complete than we thought.** `NEO-ZMC2/neo-zmc2.v` is the
*whole* chip, not just the pixel datapath:

```verilog
module zmc2(
    input CLK_12M, EVEN, LOAD, H,
    input [31:0] CR,
    output reg [3:0] GAD, GBD,
    output reg DOTA, DOTB,
    input nSDRD0, input [1:0] SDA_L, input [15:8] SDA_U,
    output [21:11] MA,              // <- the ZMC bankswitching half
    input CS, CSDOT
);
```

It includes the M1 bankswitching half (`MA[21:11]`) that this question lists as
unaddressed, it is marked "Tested ok :)", and it ships with a `.jed` — a
working, synthesised, shipped implementation. `NeoGeoFPGA-sim` by contrast
comments its bankswitching half out entirely (`// Not used here //zmc2_zmc`).

So if the licence question resolves favourably, path 2 gets substantially
easier and path 3 becomes buildable from published sources rather than only
purchasable.

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

### Partial answer — the numbers `[VERIFIED: wiki 68k memory map, 2026-09-08]`

The wiki's 68k memory map states the wait-cycle ranges per address region:

| Range | Wait cycles | Controlled by |
|---|---|---|
| `$000000`–`$0FFFFF` (P1) | **0 or 1** (4 or 5 clocks) | `ROMWAIT` |
| `$200000`–`$2FFFFF` (P2 / PORT) | **0 to 3** (4 to 7 clocks) | `PWAIT0`/`PWAIT1` |
| Memory card | 2 (6 clocks) | fixed |
| Everything else | 0 (4 clocks) | fixed |

So the baseline is **four clocks per access with zero added wait states**, and a
cartridge can request up to +1 on the fixed P1 range and up to +3 on the banked
P2 range.

This resolves an uncertainty in the best open model of the hardware.
`System/c1_wait.v` in NeoGeoFPGA-sim carries the comments `0~1 or 1~2 wait
cycles ?` and `Needs checking` against exactly these signals. The answer for
`ROMWAIT` is **0 or 1**, and `PWAIT0`/`PWAIT1` together select 0–3 — which is
what two bits should do. Worth reporting upstream.

**What is still unknown** is the part that actually gates the design: the
*access time* a cartridge must meet to be read at zero added wait states. That
is a nanosecond figure nobody has published, and it stays `[UNVERIFIED]` until
Phase 5 measures it.

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

## Q4 — What is inside a NEOGEO AES+ cartridge?

**Status:** `[ANSWERED — 2026-09-08]` · **The new cartridges run on original AES
hardware, so they must contain a serializer.** Affects Phases 2, 6, 7, 11.

> The ten re-released games "are confirmed to be compatible with original Neo
> Geo AES systems, too." `[VERIFIED: Time Extension, 2026]`

Compatibility runs both ways. PLAION describes the console as using "legacy
ASIC chips, re-engineered by modern standards" — and the same must be true of
the cartridges, because original AES hardware has no serializer and cannot
supply one.

**SNK has re-manufactured a sprite serializer and is shipping it in volume from
12 November 2026.**

### What this changes

**Q2 needs revisiting.** The donor-chip path was discounted partly because every
unit consumes an original cartridge. A new AES+ cartridge at $90 is a *newly
manufactured* board containing a modern serializer — in production, purchasable,
and destroying nothing vintage. That is a materially better donor than a
harvested 1990 cart, and it did not exist as an option a week ago.

**Phase 6 has a commercial existence proof.** Whatever the serializer costs to
reimplement, it is evidently cheap enough to put in a $90 cartridge in 2026.

**A teardown is now high-value to this project specifically.** The first
photographs of a new AES+ cartridge PCB show how someone solved, in production,
the exact problem roadmap Phase 6 describes.

**Prediction logged and wrong.** This file guessed the opposite — that the
console ASIC would serialize board-side and the carts would be dumb ROM boards,
by analogy with MVS and with the cost argument in `why-the-split.md`. That
reasoning ignored the obvious commercial point: compatibility with thirty years
of installed hardware is worth more than a chip per cartridge. Recorded rather
than deleted.

### Original framing, retained for the record

Answerable at retail on 12 November 2026.

### Context

SNK and PLAION announced the **NEOGEO AES+**, shipping 12 November 2026. $249
console, ten launch cartridges at $90, a $1000 ultimate edition. It uses
**custom ASICs rather than software emulation**, and is stated to be
**backward-compatible with original AES cartridges**.
`[VERIFIED: PLAION/SNK announcement as reported by multiple outlets, 2026]`

### The question

**Do the new AES+ cartridges also run on original 1990 AES hardware?** Nobody
has said, and the answer determines what is inside them.

**If yes** — every new cartridge must contain a sprite serializer, because
original AES hardware has none. PRO-CT0 and NEO-ZMC2 have not been manufactured
in decades, so SNK would need a modern reimplementation in CPLD, FPGA or their
own silicon. That is roadmap Phase 6, solved commercially and shipped in volume.

**If no** — the console ASIC can serialize on the board side exactly as an MVS
motherboard does, and the cartridges can be plain ROM boards. Cheaper per
cartridge, and the same cost logic SNK applied in 1990, running the other way.
See `why-the-split.md`.

**Current guess: the second.** `[UNVERIFIED]` One chip in the console beats one
in every cartridge when you expect to sell many cartridges — which is the whole
argument in `why-the-split.md`, applied to a company that now sells the console
at $249 and the software at $90.

### Why NeoForge cares

1. **A second target platform.** If the AES+ genuinely accepts original
   cartridges, NeoForge hardware should run on it. That is a second test
   machine, and a new one rather than a 36-year-old one.
2. **The compatibility matrix gains a row.** Phase 11 now has a modern ASIC
   reimplementation to test against, not only original board revisions.
3. **Connectors and shells are being manufactured again.** Somebody is making
   200-pin AES edge connectors and cartridge shells in 2026 for the first time
   in thirty years. That may matter to NeoForge's BOM and sourcing.
4. **`Q3` gains a live example.** The AES+ advertises overclocking, which by
   definition departs from original bus timing. How it handles cartridge
   wait-state signalling is worth measuring.
5. **If new carts are serializer-less**, they are mass-produced modern
   AES-form-factor cartridge PCBs — potentially the cheapest donor boards that
   have ever existed for this platform.

### The licensing question

Press coverage reports that the AES+ ASICs are "based on existing code from FPGA
developers like Furrtek and Jotego", with one developer quoted describing the
result as a fragmented version of open FPGA designs.
`[ANECDOTAL: press reporting of third-party comment, 2026]`

**This is an allegation, not a finding.** NeoForge has not examined the silicon
and has no evidence about its provenance. Recorded because if it holds up it is
directly relevant: `neogeodev/NeoGeoFPGA-sim` is Furrtek's and is GPL-3.0, and
it is the source NeoForge derives from. This project did its licensing work
specifically so it could build on that lineage properly — see `LICENSE.md`.

Do not repeat the allegation as fact. Do watch how it resolves.

### How to settle it

1. Wait for launch and for the first teardown. Somebody will open a cartridge
   within days.
2. Photographs of the new cartridge PCBs answer the chip question directly.
3. Anyone with both an AES+ and an original AES can test cross-compatibility in
   both directions in about a minute.

---

## Adding a question

Open one when a decision is being made on an assumption nobody has checked.
State what would settle it and what changes either way — a question with no
resolution path is a note, not an open question, and belongs somewhere else.
