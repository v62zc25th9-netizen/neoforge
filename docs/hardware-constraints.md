# What the hardware actually has to do

Everything a NeoForge board must hold, drive, and survive — with the numbers,
and where each one comes from.

This exists because the project had characterised the *logic* (see
`docs/serializer.md`) without ever writing down the *quantities*. Every board
decision — which FPGA, how much memory, one board or two, what it costs — rests
on numbers nobody here had looked up.

---

## 1. Memory: what a cartridge must hold

### The ceiling

| Region | Largest seen | Which game |
|---|---|---|
| **P** — 68k program | **8 MB** (2 × 4096k) | Metal Slug 3, Metal Slug 5 |
| **C** — sprite graphics | **64 MB** (8 × 8192k) | Metal Slug 3, Metal Slug 5 |
| **V** — ADPCM samples | **16 MB** (4 × 4096k, or 2 × 8192k) | Metal Slug 3, Metal Slug 4/5 |
| **M** — Z80 program | **512 KB** | Metal Slug 3, Metal Slug 5 |
| **S** — fix tiles | **128 KB**, and *none* on late CHAFIO games | — |

`[VERIFIED: wiki Cartridge ROM arrangements]`

Sum of those maxima: **88.6 MB**. But the largest ROM set on record is
**King of Fighters 2003 at 92,160 KB — 90 MB, advertised as 716 MEGS.**
`[VERIFIED: wiki Meg count]`

**Those two numbers disagree, and the disagreement is informative.** The
arrangements table lists `?` for kof2003's split, so at least one region there
exceeds the per-region maxima above. Treat the per-region figures as **lower
bounds on the true maxima**, and the 90 MB total as the number to design to.

Practical targets: **96 MB covers every known set. 128 MB is the next natural
memory size and leaves headroom.**

### But it is not one memory — it is two boards

A Neo Geo cartridge is two PCBs, and the regions are not distributed evenly:

| Board | Holds | Worst case |
|---|---|---|
| **PROG** | P, V | **24 MB** |
| **CHA** | C, S, M | **~65 MB** |

`[VERIFIED: NeoGeoFPGA-sim aes_prog.v instantiates rom_p1/rom_v1/rom_v2;
aes_cha.v instantiates rom_c1/rom_c2/rom_s1/rom_m1]`

This is the fact that shapes the whole design, and it is easy to miss when you
think of "the cartridge" as one thing:

- The two boards are **physically separate**, joined by the cartridge's internal
  connector.
- They face **different consumers**: PROG answers the 68k and the YM2610; CHA
  answers the LSPC's pixel pipeline and the Z80.
- Those consumers run **simultaneously and continuously**. Sprite fetches do not
  pause because the 68k wants an instruction.

So a flash cartridge is not one memory controller with five clients. It is
**two independent memory systems that happen to share a shell** — which is very
probably why Terraonion split the NeoSD across two FPGAs, one per board.
`[UNVERIFIED as to their reasoning — the structural argument is ours]`

### The bandwidth that matters is on the CHA side

From our own simulation: the serializer takes 32 bits of C ROM per `LOAD` and
emits two pixels per 12 MHz clock, four clocks per load.
`[MEASURED: sim/zmc2_dot_tb.v, 2026-09-05]`

    one 32-bit fetch every 4 clocks at 12 MHz
      = one fetch per 333 ns
      = 3 M fetches/s x 4 bytes
      = 12 MB/s sustained, 96 Mbit/s

12 MB/s is unremarkable for SDRAM. **What is demanding is that it is hard
real-time.** There is no handshake, no wait state and no back-pressure on this
path — the LSPC expects pixels on a fixed schedule and a late fetch is a visible
glitch, not a stall. The design constraint is bounded worst-case latency, not
throughput.

`[UNVERIFIED]` — this is the rate during active pixel output. Whether the LSPC
fetches continuously across a whole line, and what blanking and the per-line
sprite limit do to the average, we have not worked out.

### One quirk worth knowing early

Late games (Metal Slug 3, 4, 5) list **no S ROM at all**. On CHAFIO boards the
fix-layer data is drawn from the C ROMs instead. `[VERIFIED: wiki Cartridge ROM
arrangements]` Any cartridge claiming full compatibility has to reproduce that,
and it is not a mode our current documentation covers.

### The clock all of this is measured against

Worth stating plainly, because every access-time number below is relative to it
and this file never said it:

| | Master clock |
|---|---|
| **AES** | **24.167829 MHz** |
| MVS | 24.000 MHz |

`[VERIFIED: wiki Clock]` NEO-D0 divides it by 2, 4 and 8 for the 12 MHz
NEO-ZMC2 clock, the inverted 6 MHz video clock and 3 MHz for NEO-B1; LSPC2-A2
divides by 3 and 6 for the YM2610's 8 MHz and the Z80's 4 MHz.

**The two machines do not share a crystal**, and NeoForge targets the AES one.

Two consequences, both small and both worth having written down:

- `NeoGeoFPGA-sim` oscillates with `always #20.8`, which is 24.04 MHz - the MVS
  figure, driving an AES cartridge. 0.7% fast. It changes no conclusion at a
  120 ns access time, but it is a discrepancy in our own harness rather than in
  the model's documentation, and anyone sweeping timing to the last nanosecond
  should know before they trust the result. `[MEASURED: 2026-09-18]`
- PLAION's AES+ was reported at TGS as clocked at **48.33 MHz**, which several
  people repeated as evidence of inaccuracy. It is 2 x 24.167829 = 48.3357 - the
  AES master clock doubled, the ordinary way to clock a recreation that must
  generate both edges of the original domain. Doubling the *AES* figure rather
  than the MVS one is a point in their favour. See Q4.

### Access time: there is already a known-good envelope

The ROM models in NeoGeoFPGA-sim carry access-time annotations, and `rom_p1.v`
states its part outright in a comment — *"120ns 1024k*16bit (2048kB) ROM"*.

| Region | Modelled access time |
|---|---|
| P | **120 ns** |
| M, V | 100 ns |
| S | 200 ns |
| C | **250 ns** |

`[VERIFIED: NeoGeoFPGA-sim, Cartridge/ROMs/*.v — as the model's annotations.
NOT verified against silicon.]`

**One of these is now known to be wrong.** `[MEASURED: 2026-09-21]` A Fatal Fury
Special cartridge in hand carries a **`TC531001CP-12`** at M1 - the `-12` is a
120 ns speed suffix `[VERIFIED: Toshiba datasheet]` - against the 100 ns this
table claims for M. The model's annotation is optimistic by 20 ns. No conclusion
changes, since 120 ns is what P uses and the budget below has room, but it is
the first of these borrowed numbers checked against a physical part and it did
not survive. Treat the rest as unconfirmed rather than as measurements. See
[`teardown-fatal-fury-special.md`](teardown-fatal-fury-special.md).

**This is the number a board designer actually needs, and it is a sufficient
condition rather than a limit.** If SNK shipped 120 ns P ROMs and every Neo Geo
cartridge ever made works, then 120 ns is demonstrably fast enough. Design to
100 ns and there is margin over what the hardware provably tolerates. Nothing
has to be pushed until it breaks to establish that.

One cross-check that raises confidence: C ROMs at 250 ns against the 333 ns
fetch interval derived above from our own testbench. Those fit, with margin —
two independent things agreeing. And the ordering makes physical sense: the
graphics path is the most relaxed because the serializer pipelines it, while the
CPU path is the tightest.

**How to upgrade this from a model annotation to a measurement:** read the mask
ROM part numbers off a real board. Speed grade is in the part number. That is a
magnifying glass and no risk at all, and it is why the Fatal Fury Special
teardown matters more than it first appeared.

---

### How much of that envelope is actually the ROM's `[MEASURED: 2026-09-20]`

The 120 ns figure above is borrowed - it is what the model's author annotated.
This section derives the budget independently, from the CPU's own datasheet, so
that for the first time a timing number in this repository does not trace back
to somebody else's model.

**The read cycle.** A 68000 read with no wait states occupies four clock periods.
The address is valid `tCLAV` after the clock edge that starts it, and the data
must be valid `tDICL` before the falling edge of S6, when the CPU latches it.
Everything in between is available to the memory system:

    3 x tCYC = tCLAV + tacc + tDICL

`[VERIFIED: standard 68000 read-cycle derivation; the same relation appears in
teaching material with a worked 8 MHz example - 3 x 125 = 70 + 290 + 15 - whose
arithmetic checks and whose values match the datasheet's 8 MHz column.]`

**The numbers, and which of them we actually read.** From Motorola MC68000/D,
*AC Electrical Specifications - Read and Write Cycles*, 12.5 MHz column:

| # | Characteristic | Symbol | 12.5 MHz | Legible? |
|---|---|---|---|---|
| 6 | Clock low to address valid | `tCLAV` | max **50 ns** | yes - and 50 ns in the 10 and 16.67 MHz columns too |
| 11 | Address valid to AS asserted | `tAVSL` | min 10 ns | yes |
| 14 | AS, DS width asserted | `tSL` | min 160 ns | yes |
| 27 | **Data-in valid to clock low (setup)** | `tDICL` | **unread** | **no - OCR artifact** |
| 31 | AS, DS asserted to data-in valid | - | 65 ns | value yes, min/max ambiguous |

**Spec 27 is the one value the calculation needs and the one the scan would not
give up.** Two fetches of the same document returned different nonsense for that
row. It is not recorded here as a number we have.

**The result is robust to it anyway.** The 8 MHz column's 15 ns bounds it from
above - setup times do not grow with frequency - so `tDICL` lies somewhere in
roughly 5 to 15 ns, and at 12.083915 MHz (`tCYC` = 82.755 ns):

| `tDICL` | `tacc` available | Slack over a 120 ns ROM |
|---|---|---|
| 5 ns | 193.3 ns | 73.3 ns |
| 10 ns | 188.3 ns | 68.3 ns |
| 15 ns | 183.3 ns | 63.3 ns |

**So the bus offers roughly 183-193 ns from address valid to data required, and a
120 ns P ROM consumes about two thirds of it.** The remaining **~65-73 ns** is
the entire budget for everything between the CPU's address pins and the ROM's
data pins: the console's decode, the connector, the cartridge's own chip-select
logic, and any buffer or level translator in the path.

### What that answers, and what it now constrains

**It answers the question this file asked.** "Did SNK choose 120 ns because the
bus demanded it or because it was cheap?" Neither, quite: 120 ns plus a realistic
decode path is a comfortable fit inside ~190 ns, which is what a competent
designer picks. It was not arbitrary, and it was not at the edge.

**It makes the slower-is-fine assumption unsafe.** A 150 ns part leaves ~35-43 ns
for the whole decode path. That is not obviously impossible, but it is no longer
a margin anybody should assume without adding up their own delays.

**It gives Phase 7 a number to design against, which is the real prize.** Any
NeoForge board has to fit its decode, translation and chip-select inside that
~65-73 ns alongside a 120 ns memory. A 5V CPLD doing chip-select at ~10 ns
propagation is comfortable. A 3.3V FPGA behind level translators is where this
budget starts to matter, and it can now be checked by addition rather than by
hoping. This is the number [`open-questions.md`](open-questions.md) Q3 said it
needed.

### Two caveats, both real

**The speed grade is assumed, not established.** The 12.5 MHz column is the
conservative choice for a part clocked at 12.084 MHz, but we do not know what
SNK actually fitted. If it is a 16.67 MHz-rated part - plausible, and several
contemporary systems used one - some specs improve. The wiki says only "runs at
12MHz" and does not name the part. **The Fatal Fury Special teardown settles
this by reading the lid.** `[UNVERIFIED]`

**The datasheet carries a date-code condition.** The table footnote reads:
*"These specifications represent an improvement over previously published
specifications for the 8-, 10-, and 12.5-MHz MC68000 and are valid only for
product bearing date codes of 8827 and later."* Neo Geo hardware is comfortably
later than 1988, so the improved specs apply - but it means a pre-8827 part has
*different, worse* timing, and anyone reading an older datasheet scan will get
different numbers and be right about a different chip.

### How to close this properly

1. A clean (non-scanned) MC68000 datasheet for spec 27. `nxp.com` and
   `bitsavers.org` are both unreachable from this environment; a text-layer PDF
   from anywhere else would finish it in one reading.
2. The CPU part number off a real board - Phase 4.
3. Neither is blocking. The bounded result above is good enough to design
   against and is already tighter than anything the project had before.

## 2. Voltage: the constraint that picks the FPGA

The logic we simulated — a shift register, a mux, four 8-bit registers, some
address arithmetic — fits in almost anything. **It is not what constrains the
part choice. 5V is.**

Modern FPGAs are 3.3V-or-lower I/O, and 5V-tolerant FPGAs have essentially
stopped being made. So the choice is between old 5V CPLDs (small, and
increasingly hard to buy) or a modern FPGA behind level translation.

### The two directions are not equally hard

| Direction | Difficulty |
|---|---|
| **Cart → console** (3.3V out into 5V in) | Usually free |
| **Console → cart** (5V out into 3.3V in) | Needs buffers |

For the easy direction, the relevant thresholds are:
`[VERIFIED: NESdev, Implementing Mappers In Hardware]`

| Receiving technology | Input-high threshold |
|---|---|
| TTL (74LS) | **2.0 V** |
| TTL-compatible CMOS (74HCT, 74ACT) | **2.0 V** |
| Plain CMOS (74HC) | **3.7 V** |

A 3.3V output clears 2.0 V comfortably. It does **not** clear 3.7 V. So driving
a 5V system from 3.3V logic works — *provided every receiver is TTL-threshold*.

For the hard direction, the standard answer is the **74LV / 74LVC / 74LVCT**
families: 3.3V rail, 5V-tolerant inputs, 3.3V outputs. Bidirectional buses want
a transceiver such as the **74LVC245**, which needs a direction signal.

### Somebody already did it, and it works `[VERIFIED: FusionConverter BOM]`

`neogeodev/FusionConverter` is a shipping open-hardware MVS-to-AES converter.
Its bill of materials answers the question above empirically, and the answer is
encouraging.

| Board | Parts |
|---|---|
| **CHA** | LDO (1.8 V + 3.3 V), **CPLD Lattice LC4064ZE-7TN100**, voltage detector, LED. **No level shifters.** |
| **PROG** | 2 × 74HC245 octal transceiver, 1 × 74HC08 quad AND |

The LC4064ZE is a **1.8 V core part with 3.3 V I/O**, and its datasheet states
that inputs "can be safely driven up to 5.5 V when an I/O bank is configured for
3.3 V operation." `[VERIFIED: Lattice DS1022, ispMACH 4000ZE family]`

So on the CHA board a 1.8 V/3.3 V CPLD sits directly on the AES bus, with
**nothing between it and the console** — 5 V in on tolerant inputs, 3.3 V out
straight into the console's ASICs. And the device works.

That is not proof that every console input is TTL-threshold, but it is a
shipping counterexample to the fear, on exactly the pins a serializer drives.
It moves "3.3 V drive might not clear the threshold" from an open risk to an
unlikely one.

Two smaller things the same BOM tells us:

- **The CPLD is on CHA, and PROG has none** — which is exactly where our
  architecture says the serializer lives. Independent confirmation of the split.
- **PROG's 74HC08 quad AND** is almost certainly the `/PORTOEL` · `/PORTOEU` →
  `/PORTOE` function [`prom-banking.md`](prom-banking.md) derives from PROGBK1,
  where SNK used a 74LS08. Two independent designs reaching the same gate.

### Where our actual unknown is

Here is the uncomfortable part, and it is worth stating plainly rather than
inheriting the general advice.

The direction that is normally easy is exactly the one **we cannot yet confirm**,
because the things receiving our data are undocumented SNK ASICs — NEO-B1, the
LSPC, and whatever else sits behind the connector. We do not know their input
thresholds. If any of them is plain-CMOS-threshold rather than TTL, direct 3.3V
drive fails on that pin, and it will fail *marginally* — the worst kind.

`[UNVERIFIED]` — and there is a cheap way to settle it that does not need our
own board: measure `VOH` and the switching threshold on a working cartridge's
outputs. That belongs with the Phase 5 measurement work, and it should be added
to it.

### What this implies

- The FPGA is chosen for **I/O count, memory interface and availability**, not
  logic capacity. We need very little logic.
- **Level translation is a first-class part of the design**, not an afterthought
  — on the order of 100+ signals, and the direction control for the bidirectional
  ones is itself logic.
- A 5V CPLD stays attractive for a *small* board (the fix-only development cart,
  the measurement cart) precisely because it deletes the translation problem.
- Two boards means the translation problem exists **twice**, with different
  signal mixes.

---

## 3. What this changes about the plan

**The measurement cart gets easier.** It needs to answer P ROM reads and nothing
else — no C, no V, no serializer, no 64 MB. A small 5V CPLD plus a modest SRAM
sidesteps both the memory and the voltage problem entirely, which makes it
buildable well before Phase 7.

**The full loader is a CHA-side problem.** 65 MB and a hard-real-time 12 MB/s
live on that board; the PROG side is 24 MB with relaxed timing. If effort has to
be sequenced, PROG is the easier half and CHA is where the risk is.

**"Which FPGA" is premature until Q3 is answered.** Access time decides whether a
translated 3.3V design can meet the bus at all. Choosing a part before that
number exists is choosing in the dark.

---

## Open questions this raises

- What are the input thresholds of the console-side ASICs? (Measurable on a
  working cart — see above.)
- Are the modelled ROM access times right? **Partly settled 2026-09-21 by
  reading part numbers off a real board: M is 120 ns, not the 100 ns modelled.**
  The other positions carry no speed suffix in their markings, so photographs
  cannot settle them - that needs the parts in hand or a datasheet cross-check
  against what SNK could buy in 1993.
- ~~How much margin does 120 ns actually represent?~~ **Answered 2026-09-20**,
  to within a bounded range — see "How much of that envelope is actually the
  ROM's" above. The bus offers ~183–193 ns; a 120 ns part leaves ~65–73 ns for
  the whole decode path. What remains open is narrower: spec 27 (`tDICL`) could
  not be read off the available scan, and the CPU's actual speed grade is
  assumed rather than known.
- What is kof2003's actual region split, and does anything exceed 8/64/16 MB?
- What does the LSPC's *average* C ROM fetch rate look like across a frame,
  including blanking and the per-line sprite limit?
- How do CHAFIO-era games source fix data from the C ROMs, and what must a
  cartridge do differently?

---

*Corrections welcome and actively wanted. Open an issue.*
