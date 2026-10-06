# Board zero: the smallest cartridge that can fail informatively

**Status:** specification, not yet fabricated · Opened 2026-09-27

Board zero is the first physical NeoForge PCB. Its only job is to answer one
question — *does a board we designed satisfy the AES 68000 bus?* — and to answer
it audibly, with no oscilloscope, no video output, and no second board.

The test itself is described in
[`open-questions.md`](open-questions.md) Q1: the console's watchdog resets the
machine at ~3.7 Hz unless software kicks it, our P code kicks it, so **silence
is a pass and the click of death is a fail.** This file is the board that runs
that test.

---

## 1. The finding that reshaped it: every part can run at 5V

The plan of record assumed board zero would need level translation — 3.3V flash
behind `SN74LVC4245A` transceivers, as [`prior-art.md`](prior-art.md) records
both Darksoft and the FusionConverter doing.
[`hardware-constraints.md`](hardware-constraints.md) §2 calls that translation
path *"the failure mode that has sunk cheap multicarts"*.

**Board zero does not need it, because 5V parallel flash of the right size is
still in production.** `[MEASURED: 2026-09-27 — distributor listings and
manufacturer datasheet]`

| | SST39SF040 |
|---|---|
| Supply | **single 4.5–5.5V**, read and write |
| Density | 4 Mbit, **organized 512K × 8** |
| Address lines | **19** (A0–A18) |
| Speed grades | 45 / 55 / 70 ns; **the -70 is the stocked one** |
| Packages | 32-lead PLCC, 32-lead TSOP, **32-pin PDIP** |
| Active current | 10 mA typ |
| Standby current | 30 µA typ |
| Availability | in stock, multiple distributors, 2026-09-27 |

`[VERIFIED: Microchip SST39SF010A/020A/040 data sheet DS20005022, headline
specifications]` · `[UNVERIFIED: the per-speed-grade read-cycle table — tCE,
tOE, tOH, float delays — has not been read. Only the headline 70 ns access time
is relied on below, and §4 shows the margin is large enough that the rest
cannot change the conclusion.]`

## 2. Two of them are exactly the P region

`rom/Makefile` sets `P_SIZE := 1048576` — 1 MiB. The AES PROG connector carries
**A1–A19**: nineteen address lines, addressing words, which is
`$000000`–`$0FFFFE`. Exactly 1 MiB, exactly the unbanked window that
[`prom-banking.md`](prom-banking.md) §3 records as *never* bankswitched.

So:

- the connector offers **19** address lines
- the part accepts **19** address lines
- two parts on the two byte lanes give **1 MiB of 16-bit P**
- which is **exactly** the size of the fixed window, and exactly `P_SIZE`

There is no address line left over to decode, and none missing to synthesise.
That is the whole reason this board has no logic on it.

## 3. Why there is no decode logic at all

**The console does the decoding.** `/ROMOE`, `/ROMOEU` and `/ROMOEL` are real
pins on the PROG edge — `[VERIFIED: docs/data/aes-cartridge-pinout.csv, b22,
a21, a22, both sources]` — generated inside the machine for the
`$000000`–`$0FFFFF` region. A cartridge that only wants the fixed window is
handed a chip select and two byte enables and has nothing left to work out.

Everything that makes a real PROG board complicated belongs to features board
zero deliberately does not have:

| Part on a real PROGBK1 | What it is for | Board zero |
|---|---|---|
| 74LS74 | bank register for `$200000` | **absent** — no banked window |
| 74LS08 | ANDs `/PORTOEL` + `/PORTOEU`, because there is no `/PORTOE` pin | **absent** — follows from the above |
| 74LS139 | V ROM chip select | **absent** — no V ROM |
| `SN74LVC4245A` ×n | 3.3V ↔ 5V translation | **absent** — the whole board is 5V |
| FPGA / CPLD | loader, mapper, serializer | **absent** |
| latches on `SDRAD*` | de-multiplex the YM2610 address bus | **absent** — see §5 |

**Board zero is a card edge, two flash chips, four resistors and some
decoupling.** It is not a simplified cartridge; it is the complete set of parts
required to present 1 MiB of program ROM to a 68000.

## 4. The timing check, which is now not close

From [`hardware-constraints.md`](hardware-constraints.md) §1, budgeting against
the worst of the four CPU/clock combinations — **a Hitachi `HD68HC000PS12` in an
AES**:

| | ns |
|---|---|
| Available `tacc`, address valid to data required | **176–186** |
| SST39SF040-70 address access time | **70** |
| Left for console decode + card edge + our board | **106–116** |

Compare an original cartridge: a 120 ns mask ROM leaves **56–66 ns** for that
same path, and that is the number the project has been treating as the design
constraint.

**Board zero has roughly 50 ns more margin than the cartridges SNK shipped.**
That matters for what a failure would *mean*: if board zero clicks, the cause is
almost certainly a wiring or assembly error, not a timing error. It is a test of
our pinout and our process, and the 70 ns part is what makes it a clean test of
those rather than a confounded one.

Wait states, therefore: **tie all four high** — `/ROMWAIT`, `/PWAIT0`,
`/PWAIT1`, `PDTACK`, each through **220 Ω to VCC**, which is what the reference
cartridge in [`open-questions.md`](open-questions.md) Q3 does and what the
budget above says we are entitled to. Lay out the four resistors so the pad for
each can be moved to GND instead; that converts "no wait states" into "one wait
state on the P1 range" with a soldering iron and no new board, which is a
diagnostic worth having even though we do not expect to need it.

## 5. There is no V ROM, and that is a saving, not a compromise

The obvious next thought is to fit a third SST39SF040 as V ROM, since PROG
carries V as well as P. Do not, for board zero:

1. **The Z80 cannot run.** The M ROM is on **CHA**
   `[VERIFIED: aes_cha.v instantiates rom_m1; confirmed on the Fatal Fury
   Special teardown]`. With no CHA board there is no Z80 program, so V ROM data
   could not be played by anything.
2. **V would reintroduce logic.** The YM2610's address bus arrives
   multiplexed — `SDRAD0`–`SDRAD7`, `SDRA8`, `SDRA9`, `SDRA20`–`SDRA23`,
   `SDRMPX`, `/SDROE` — and reconstructing a flat address needs latches plus the
   74LS139 select. That is the first real logic on the board, added for a
   function that cannot be exercised.

Fitting V is the right move on board **one**, alongside CHA. On board zero it
buys nothing and costs the property that makes the board valuable: that there is
almost nothing on it to get wrong.

## 6. Parts list

| Ref | Part | Notes |
|---|---|---|
| U1 | SST39SF040-70, 32-lead PLCC | **low** byte lane, `D0`–`D7` |
| U2 | SST39SF040-70, 32-lead PLCC | **high** byte lane, `D8`–`D15` |
| — | 2 × 32-pin PLCC through-hole socket | see below |
| R1–R4 | 220 Ω, 0805 | wait-state network, §4 |
| C1, C2 | 100 nF, 0805 | one per flash, at the device |
| C3 | 10 µF | bulk, at the card edge |
| — | PCB with a 2 × 50 gold-finger edge | **the blocking unknown, §9** |

**Sockets, deliberately.** PLCC-32 through-hole sockets are hand-solderable, and
they mean the flash can be pulled and reprogrammed in a TL866/T48 without
touching the board again. Given that reflashing is the inner loop of every
hardware test in this project, and that the person assembling it has said he is
a beginner at soldering, that is worth the ~15 ns of added socket capacitance
many times over. PDIP-32 is the fallback if PLCC sockets prove awkward — same
die, same specs, a bigger footprint.

**Programmed out of circuit, so `/WE` ties to VCC.** Directly, not through a
pull-up. Board zero physically cannot write its own flash. That removes any
question about `R/W` on `a19`, about write-cycle timing, and about the console
corrupting the ROM if our decode is wrong.

## 7. Wiring

Signal-level, not pin-numbered: the SST39SF040 pin numbers come off the
datasheet's package drawing when the footprint is drawn, and are not guessed
here.

| Edge | Goes to |
|---|---|
| `A1`–`A19` (b3–b21) | `A0`–`A18` of **both** U1 and U2, in order |
| `D0`–`D7` (a3–a10) | `DQ0`–`DQ7` of U1 |
| `D8`–`D15` (a11–a18) | `DQ0`–`DQ7` of U2 |
| `/ROMOE` (b22) | `/CE` of both |
| `/ROMOEL` (a22) | `/OE` of U1 |
| `/ROMOEU` (a21) | `/OE` of U2 |
| — | `/WE` of both → VCC |
| `VCC` (a25–a27, b25–b27) | VCC, all six |
| `GND` (a1, a2, a49, a50, b1, b2, b49, b50) | GND, all eight |
| `/ROMWAIT`, `/PWAIT0`, `/PWAIT1`, `PDTACK` | 220 Ω to VCC each |
| everything else | no connect |

**"Everything else" is most of the connector**, and that is intentional: the
whole V ROM bus, the PORT strobes, `68KCLKB`, `/RESET`, `R/W`, `/AS`, `L/R
in/out` and the `4MB` pin are all left unconnected. `/RESET` in particular is
worth noting as absent — with no bank register there is nothing to reset.

**One choice to confirm before fabrication.** The `/CE` ← `/ROMOE`, `/OE` ←
`/ROMOEU`/`/ROMOEL` assignment above is the conventional one, and the reverse
also works electrically. PROGBK1's jumper matrix *selects* which signal drives
`/CE` and `/OE` `[VERIFIED: wiki PROGBK1]`, which tells us SNK treated it as a
configuration choice rather than a fixed requirement — so both are probably
fine, but the PROGBK1 schematic should settle which one the original boards
actually strap. `[UNVERIFIED]`

## 8. The risk that is not about timing

Board zero's timing is comfortable and its wiring is nearly trivial. The real
risk is upstream of both: **does the AES BIOS hand control to cartridge code
when the CHA side is empty?** The BIOS runs first, from the system ROM, and
performs its own checks before swapping the cartridge in at `$000000`. If any of
those checks inspect the fix layer, a game header, or a checksum that board zero
cannot satisfy, the board fails the watchdog test for a reason that has nothing
to do with the hardware being wrong.

**Part of this is answerable in software, right now, and part of it is not — and
the distinction matters because we have already conflated them once.**

- **Answerable:** *will a real AES BIOS jump to our P code when S, M and C are
  empty?* That is a ROM-image question. Build the board-zero image with empty
  S/M/C — the `boardzero` target in `rom/Makefile` already does — and run it
  under an emulator with a real AES BIOS rather than nullbios. If the BIOS
  refuses, we learn it costs nothing.
- **Not answerable:** *will the console behave the same with the CHA board
  physically absent?* An empty region is not a missing board. A missing board
  leaves the CHA connector's inputs floating, and no emulator models a floating
  connector. This is the correction recorded in
  [`open-questions.md`](open-questions.md) Q1 and it still stands.

**`[2026-09-28]` The second one is now reachable.** There is an AES in the
house. That does not make board zero testable today — it still needs a
fabricated board, and dumping this console's BIOS for the first test needs a
flash cart or a desoldering iron, neither of which is here yet. But the whole
question stops being hypothetical, and **which 68000 this particular console
contains decides how much a board-zero pass is worth**: a pass on a Hitachi
machine, the one reportedly glitchy with multicarts, is far stronger evidence
than a pass on a Toshiba. That is a screwdriver and a photograph away — see
[`teardown-aes-console.md`](teardown-aes-console.md).

If the answerable half comes back "the BIOS refuses", board zero grows a CHA
board and stops being board zero. That is the single finding most likely to
invalidate this file, which is a good reason to go looking for it before
spending money on a PCB.

## 8a. Make the silence say how far it got `[2026-10-06]`

**We are not getting a BIOS this round** — the AES BIOS is soldered to the
motherboard and the cheapest flash cartridge that could dump it is about $660.
See [`what-to-buy.md`](what-to-buy.md).

That removes the cheap test above, and it leaves board zero's result ambiguous
in a way the whole design was meant to avoid: if it clicks, is that wiring, the
ROM, the BIOS handoff, or timing? Four suspects and one bit of output.

**The fix costs nothing and lives in the ROM.** §0 of this file says the test is
audible because the watchdog is. Extend that: instead of kicking the watchdog
for a fixed interval and stopping, kick it for a *different* interval depending
on how far the code got, and **the length of the silence before the clicking
starts becomes a diagnostic code.**

| Silence | Reached |
|---|---|
| **none** — clicks from power-on | the BIOS never handed over, or the board is dead |
| **2 s** | our entry point is executing |
| **4 s** | work RAM reads back what was written |
| **6 s** | a known signature at the **last** word of P, `$0FFFFE`, reads correctly — `A19` and the top of the map are good |
| **8 s** | a walking-ones pass over all 19 address lines reads the right signature at every `2^n` offset |
| **10 s** | a checksum of the whole 1 MiB matches |

Then it clicks. Count the seconds on a phone.

**Why these stages and not others.** They are ordered by what actually goes
wrong on a hand-assembled board: a swapped or open address line is the most
likely single fault, and the walking-ones stage is the test that finds it and
*names which line*. A swapped data line shows up one stage earlier, in the
signature compare. Nothing here needs an instrument, because each stage's
failure is distinguishable by ear.

**One deliberate elegance:** the intervals are counted by the kick loop itself,
so they are derived from the console's own clock. A board that runs but runs at
the wrong rate produces silences of the wrong length, and that is a timing
result arriving for free out of a test built for continuity.

**It does not recover everything.** The top row stays ambiguous — "BIOS refused"
and "board dead" both click immediately. **That is why the multimeter in
[`what-to-buy.md`](what-to-buy.md) §4 is part of the experiment rather than part
of the toolbox:** a board whose continuity has been checked against
[`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv) before it is
ever inserted makes "dead" the unlikely branch, and leaves the BIOS as the
named suspect.

## 9. What actually blocks this

Not the parts. Not the logic. Not the timing. Not the ROM.

**The footprint.** [`aes-connector.md`](aes-connector.md) has all 200 pins
verified end to end against two independent sources, and the schematic sheets
are generated and netlist-checked 100/100 — but a schematic has no dimensions.
Board zero needs the physical card edge: finger pitch, finger width and length,
board thickness, the bevel, and how far the fingers sit from the board edge.
None of that is in any pinout table, and the project has no measured source for
it.

That is one evening with a pair of calipers and the one cartridge in the house,
and it is the only thing standing between this specification and a board file.
**The protocol is [`card-edge.md`](card-edge.md)** and the numbers go in
[`data/aes-card-edge-dimensions.csv`](data/aes-card-edge-dimensions.csv).

Secondary, and cheaper to close:

- ~~Gold-finger constraints unknown~~ **closed** `[VERIFIED: 2026-10-06]` —
  ENIG required, bevel 30° or 45°, no copper in the bevel region, solder mask
  fully opened over the fingers, and chamfering needs a board at least 50 mm on
  a side. See [`fabrication.md`](fabrication.md) §4, which also covers how a
  design becomes boards and why board zero should be hand-assembled.
- The `-70` speed grade's full read-cycle table, per §1.
- The `/CE`/`/OE` strap, per §7.

## 9a. Why not RAM, asked and answered `[2026-10-06]`

**Proposed: make board zero a RAM board instead — one slot, no flash.** It is a
reasonable-sounding simplification and it is the wrong way round, so it is
recorded here rather than re-litigated later.

**A RAM cartridge is empty at power-on, and on an AES nothing can fill it.**
There is no host, no loader, no storage. Something on the cartridge has to hold
the console off, read a program in from somewhere, write it into the RAM, and
only then let the 68000 see it. That is a microcontroller or an FPGA, a storage
medium, and a reset or bus-arbitration scheme — and it is **the hardest
subsystem in the entire project**, which is why it sits in Phase 9.

Flash avoids all of it with one trick: **the chips are programmed offline in a
$70 programmer**, so the board itself does nothing but present them to the bus.
That is the only reason board zero is two chips and four resistors.

| | flash | RAM |
|---|---|---|
| Content at power-on | **there** | empty |
| Needs a loader | no | **yes** |
| Needs bus arbitration | no | **yes** |
| Survives a power cycle | **yes** | no |
| Failure modes added to board zero | 0 | **3** |

That last row is the argument. **Board zero's value is not capability, it is
diagnostic isolation** — it exists so that a failure has one plausible cause.
A loader adds three new ones, to the board whose entire purpose is to have none.

### But the instinct is correct about where this goes

Loading into RAM is not a bad idea, it is **the** idea:

- **The Neo Geo CD is SNK's own proof it works** — slow media, shadowed into
  RAM, feeding the same 68000 at the same clock, shipping in 1994.
- **NeoSD Pro advertises "one RAM slot for instant game loading."**
- [`open-questions.md`](open-questions.md) Q4 argues a 2026 commercial AES cart
  must be doing it, because serial NOR cannot feed a 68000 bus.

So it is the right architecture, arriving in the wrong order. Board zero first,
because a RAM loader that fails tells you nothing until you already know the
bus side works.

### What the proposal is actually asking for, and a cheaper way to get it

The real appeal is **iteration speed** — pulling a PLCC chip, programming it,
reseating it, every time the ROM changes. That is a genuine irritation and it
does not need RAM to fix.

**Board one: board zero, plus `/WE` brought out to a header.** §6 ties `/WE`
directly to VCC so the board physically cannot write its own flash. Bring it to
a jumper instead, add the few control lines, and a **$4 Raspberry Pi Pico can
reprogram the flash in place on the bench** — non-volatile, no loader at boot,
no arbitration, and the console side is byte-for-byte identical to board zero,
so it does not invalidate the result board zero just produced.

That is the upgrade worth making. RAM is the one after it.

### One reading of the proposal that is already true

If "one slot only" meant *one memory region, no banking* rather than *RAM*,
then **that is board zero exactly as specified** — the fixed 1 MiB window, no
bank register, no second P ROM. §3 is that argument.

## 10. Why this is worth writing down before it is worth building

Board zero as specified is **two chips and four resistors**. No programmable
logic, no translators, no serializer, no banking, no V ROM, no CHA board, and
about 50 ns more timing margin than a 1993 cartridge had.

The project's standing assumption was that a first board meant an FPGA behind
level translators and that voltage was the constraint that picked the FPGA.
For the board that answers the first question, neither is true — and the reason
is not cleverness, it is that somebody still sells 5V parallel flash in a
socketable package, and that 19 address lines is 19 address lines.

---

Sources: Microchip SST39SF010A/SST39SF020A/SST39SF040 data sheet DS20005022
(headline specifications, read 2026-09-27); distributor stock listings
2026-09-27; NeoGeo Development Wiki *PROGBK1*, *Bankswitching*, *68k memory map*
(public domain); this repository's own
[`aes-connector.md`](aes-connector.md), [`hardware-constraints.md`](hardware-constraints.md),
[`prom-banking.md`](prom-banking.md) and [`open-questions.md`](open-questions.md).
