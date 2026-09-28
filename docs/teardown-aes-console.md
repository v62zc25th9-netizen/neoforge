# Opening the AES: four numbers our timing budget rests on

**Status:** protocol written, not yet performed · Opened 2026-09-28

[`hardware-constraints.md`](hardware-constraints.md) §1 contains the most
load-bearing arithmetic in this project — the read-cycle budget that every part
choice is checked against. Three of its inputs have never been seen by anyone
here. They are all printed on chips inside an AES, in letters large enough to
photograph.

**No multimeter needed. No soldering. A screwdriver and a phone.**

---

## 0. Before opening it

- **Unplug it.** The AES takes 9V DC from an external brick, so there is no mains
  voltage inside — but unplug it anyway and let it sit.
- Work on a hard surface, touch something grounded first, hold boards by the
  edges. These parts are thirty years old and irreplaceable.
- **Photograph before touching anything**, then after each screw set. Reassembly
  is the step people get wrong.
- Do not remove or reseat any socketed chip. Everything below is read by looking.

## 1. The 68000 — the one that matters most

`hardware-constraints.md` §1 budgets against a **Hitachi `HD68HC000PS12`**
because community reporting says AES consoles shipped with one of three CPUs and
the Hitachi is the slow one — `tCLAV` 57 ns against 50 — and that this is
reportedly the difference between a multicart working and glitching. Our entire
"design to ~56 ns of decode" rule comes from that.

**It is `[ANECDOTAL]`. We are relaying a forum comparison of three datasheets we
have not read, about three parts we have not seen.**

| Read off the chip | Why |
|---|---|
| **Manufacturer** | Toshiba, Hitachi or Motorola — decides which column of the budget applies |
| **Full part number** | e.g. `TMP68HC000N-12`, `HD68HC000PS12`, `MC68HC000FN12` |
| **Speed suffix** | `-12` vs `-16`. §1 assumes 12.5 MHz as the conservative choice and says plainly that a 16.67 MHz part would improve some specs |
| **Date code** | the Motorola AC specs improve for date codes 8827 and later; §1 flags this and we have never checked a real one |

**And it tells you something about your own console specifically.** If this AES
has the Hitachi, it is the machine that reportedly glitches with multicarts —
which is exactly the machine board zero should be tested on, because a pass
there is worth far more than a pass on a forgiving one. If it has the Toshiba, a
board-zero pass is weaker evidence than it looks.

## 2. The crystal — the clock every timing number is derived from

Every figure in §1 comes from **24.167829 MHz**: `tCYC` of 82.755 ns, the
248.26 ns three-cycle window, the 8.7 ns by which an AES is tighter than an MVS.
All of it. The source is the development wiki, and **the crystal is marked with
its own frequency.**

Read it off. It is a one-second check on a number that multiplies through
everything.

While there: note whether it is a bare crystal or a can oscillator, and
photograph anything else marked in MHz.

## 3. The BIOS ROM — which region, and the handoff question

[`board-zero.md`](board-zero.md) §8 says the most likely way board zero dies is
the BIOS refusing to hand control to cartridge code with the CHA side empty, and
that the cheap version of that test is running our ROM under an emulator with a
**real** AES BIOS rather than nullbios.

Reading the BIOS chip's part number says **which** BIOS this console has —
Japanese, US or European AES — and therefore which one the emulator test would
have to use to say anything about *this* machine.

It does not produce a dump. Dumping needs either a flash cart running a dumper
or desoldering, and neither is available yet. **That is a second reason the flash
cart purchase matters**: it is the BIOS dumping tool as well as the reference
cartridge.

## 4. The slot — a dimension we have no source for at all

[`card-edge.md`](card-edge.md) has the pitch, thickness and finger geometry of
*one board's* edge. A cartridge is **two** boards, and nothing anywhere in this
repository records **how far apart the two connectors sit, or how deep they
are.** A footprint pair drawn without it can be perfectly correct twice over and
still not go into the machine.

With the console open and the slot visible:

| | |
|---|---|
| Centre-to-centre spacing of the CHA and PROG connectors | |
| Are they parallel, and in the same plane? | |
| Slot depth — how far a board inserts | |
| Contact count per connector, counted | confirms 50 per face independently of the silkscreen |
| Any key, rib or asymmetry that prevents a board going in backwards | |

**And it cross-checks the pitch.** The connector's contacts are on the same
pitch as the fingers. Measuring across sixteen of *them* is an independent
confirmation of the 2.54 mm result from a different physical object.

### First attempt, and the validity check that catches it `[2026-09-28]`

Reported: **8 mm** between the slots at the near edge of the casing separator,
**10 mm** far edge to far edge. Read the obvious way — 8 is the separator and 10
spans both slots — those two numbers say each slot opening is
`(10 − 8) / 2 = ` **1.00 mm wide**, and the board that has to go into it is
**1.65 mm** thick. That cannot be right, so at least one endpoint is not where I
think it is.

**The free check, and it is the same shape as `width + gap = pitch`:**

> outer-to-outer **minus** inner-to-inner **must equal two board thicknesses**,
> which is **3.30 mm**. And a slot opening can never measure less than 1.65.

Run that on any pair of readings before reporting them and a mis-set jaw shows
up immediately.

| If | then | and centre-to-centre is |
|---|---|---|
| inner-face gap is **8.0** | outer-to-outer is **11.30** | 9.65 |
| outer-to-outer is **10.0** | inner-face gap is **6.70** | 8.35 |

### Three numbers, defined so there is nothing to interpret

- **C9a** — inner face of one board's slot to the inner face of the other's.
  The thickness of the plastic between them.
- **C9b** — outer face to outer face, across everything. **This is the one the
  footprint pair needs.**
- **C9c** — the width of a single slot opening, on its own. Sanity only; it must
  be ≥ 1.65.

### Easier: measure the cartridge, not the console

The spacing is fixed by the cartridge as much as by the console, and a cartridge
sits on the bench where calipers can reach it. **Put the two boards back in the
shell and measure across the two protruding edges, outer face to outer face.**
That is `C9b` directly, without reaching into a slot at an angle, and it is
recorded as `C9d` so the two routes can be compared rather than conflated.

## 5. The board revision

The AES motherboard is marked with a revision. Console revisions differ in
timing-relevant ways and it is the label under which every other number here
should be filed. `prior-art.md` records that NeoSD needed revision-specific
handling; ours may too.

---

## Worksheet

Numbers go in [`data/aes-console.csv`](data/aes-console.csv). Nothing here is
`[MEASURED]` until that file has values.

## What this closes

| Currently | After |
|---|---|
| `[ANECDOTAL]` — three 68000s, relayed from a forum | `[MEASURED]` for the one console we can test on |
| `[UNVERIFIED]` — 12.5 MHz speed grade assumed | settled by a suffix |
| wiki-sourced 24.167829 MHz | confirmed against a marked part |
| no record of connector spacing at all | a dimension the board pair cannot be drawn without |

Four of the weakest entries in [`evidence-index.md`](evidence-index.md), closed
in one evening with a screwdriver.
