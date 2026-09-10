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

---

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
- What is kof2003's actual region split, and does anything exceed 8/64/16 MB?
- What does the LSPC's *average* C ROM fetch rate look like across a frame,
  including blanking and the per-line sprite limit?
- How do CHAFIO-era games source fix data from the C ROMs, and what must a
  cartridge do differently?

---

*Corrections welcome and actively wanted. Open an issue.*
