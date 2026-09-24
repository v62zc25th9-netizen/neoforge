# AES cartridge connector

The Neo Geo AES cartridge edge connector: every pin, with authoritative pin
numbers, cross-checked against three independent sources.

- Machine-readable: [`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv)
- Pin pitch 0.1 in (2.54 mm) · board thickness 1.6 mm
- 50 pins per face, 100 per board, **200 per cartridge**

A cartridge is two boards — **PROG** (68000 bus, P ROM, V ROMs) and **CHA**
(graphics, fix layer, Z80 M ROM) — each with contacts on both faces.

---

## VERIFIED END TO END: all 200 pins, against the wiki's own images `[VERIFIED: wiki AES cartridge pinout, 2026-09-24]`

The "second human reading of the wiki images" that the open list at the bottom
of this file has been asking for since it was written. Done, and **every one of
the 200 pins in
[`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv) matches.**

Four faces, compared signal by signal:

| Face | Result |
|---|---|
| PROG bottom | 50/50 match |
| PROG top | 50/50 match, image drawn in the opposite direction |
| CHA bottom | 50/50 match |
| CHA top | 50/50 match, image drawn in the opposite direction |

**Two faces are drawn one way and two the other**, which is exactly the quirk
this file documents below under "the top-face images run the other way". Seeing
it reproduce independently is a small confirmation that the orientation handling
was right too.

### Three open items retired by this

**1. The wait-state pins are ours as written.** `b25`-`b27` VCC, `b28` ROMWAIT,
`b29` PDTACK, `b30` PWAIT0, `b31` PWAIT1. The order that looked wrong next to
the MVS connector - PDTACK second rather than fourth - **is real.** AES and MVS
genuinely differ there. The residual oddity logged yesterday is closed, not
explained away.

**2. The four "inverter-shadowed" pins are real signals, not no-connects.**
This file recorded `PCK1B`, `PCK2B` (CHA top) and `8M`, `4MB` (CHA/PROG bottom)
as *"almost certainly a limitation of the extraction"* rather than genuine
no-connects, and warned against treating them as NC. All four appear on the
wiki's images as named signals. The inference was right.

**3. The only real no-connects are CHA bottom 28 and 29**, and the images show
`NC`, `NC` in precisely that position.

### What this means for the board

`hardware/lib/neoforge-aes.kicad_sym` is generated from this CSV. Until today
that CSV rested on one machine-extracted schematic plus a transcription of wiki
images by one reader. **It now rests on two independent readings that agree on
every pin.** That is the difference between a pinout we believe and a pinout we
can build from.

## Also resolved: the MVS numbering `[VERIFIED: wiki MVS cartridge pinout, 2026-09-24]`

**No conflict. Our AES data stands.** Recorded in full because the alarm was
loud for a day and the resolution is worth more than the alarm.

The NeoGeo Development Wiki's **MVS cartridge pinout** gives the PROG B row as:

| MVS pin | Signal |
|---|---|
| B24 | `68KCLKB` |
| **B25** | **`ROMWAIT`** |
| **B26** | **`PWAIT0`** |
| **B27** | **`PWAIT1`** |
| **B28** | **`PDTACK`** |
| B29-B32 | **`VCC`** x4 |
| B33 | `ROMOE` |

That is character for character what the field reports said - because **they were
quoting MVS pin numbers.** Our CSV describes the AES connector, which is a
different connector with different numbering:

| | MVS cartridge | AES cartridge |
|---|---|---|
| Connectors | 2 (PROG, CHA) | 2 (CN5 PROG, CN4 CHA) |
| Pins per row | **60** | **50** |
| Rows | A and B | a and b |
| Total | **240** | **200** |
| `ROMWAIT` on PROG | **B25** | **b28** |
| VCC block on PROG | **B29-B32** | **b25-b27** |

Both sources were right about their own machine. The vocabulary - "B25" - is
shared across two incompatible numbering schemes, which is how a day got spent.

**One residual oddity, not a problem.** The *order* within the group differs:
MVS runs ROMWAIT, PWAIT0, PWAIT1, PDTACK; ours runs ROMWAIT, PDTACK, PWAIT0,
PWAIT1. Different connectors may simply be laid out differently, and our AES
data comes from a machine-extracted AES 3.5 schematic. Worth a glance if anyone
is ever checking the AES pinout for other reasons, but nothing here contradicts
it. `[UNVERIFIED]`

**The meter check is no longer needed for this question.** It remains a cheap
sanity check before fabricating, but it is not the blocker it was yesterday.

## Superseded: the downgrade `[MEASURED: 2026-09-24]`

**Read this before the alarm below it.** Yesterday's conflict was recorded as
"our CSV may have the wait-state pins wrong." One evening of checking makes that
much less likely, for a reason neither of us considered.

**The MVS and AES cartridge connectors are not the same connector.**

`pluger/NeoGeo-161-in-1-v3-MVS-PCB-inverse-ingenering` publishes MIT-licensed
4103x3184 scans of a 161-in-1 v3 board. Its PROG edge is silkscreened **`J5`**
and numbered **60, 55, 50 ... 10, 5**, running right to left: **sixty pins per
row, one connector.** `[MEASURED: read off the scan, 2026-09-24]`

The AES cartridge has **two** connectors of **fifty** pins per row - CN4 and
CN5, `a1`-`a50` and `b1`-`b50` - which is what this file and the CSV describe.
The NeoGeo Development Wiki maintains **separate pages** for "AES cartridge
pinout" and "MVS cartridge pinout"; they are not one document.

**And the field reports were largely about MVS carts.** The clearest of them
opens *"just check a real MVS cart (Bubble Bobble)"*, and the same B-numbers
then get applied to AES carts in the same breath. Two machines, two connectors,
one numbering vocabulary borrowed across both.

**So the likeliest reading is that both sources are right about their own
machine**, and our AES data is untouched. That is a very different situation
from "do not fabricate anything."

### What would close it properly

Read the wiki's **MVS cartridge pinout** page and confirm it puts ROMWAIT on
B25, PWAIT0 on B26, PWAIT1 on B27 and PDTACK on B28. If it does, the conflict
dissolves entirely and the table below becomes a note about vocabulary rather
than a warning. The page was unreachable from here tonight - robots and a
permission prompt - so **this is downgraded, not closed.** `[UNVERIFIED]`

**Interim status:** the wait-state pins in the CSV are no longer flagged as
probably wrong, but they are not confirmed either. The cheap physical check -
a meter from the Fatal Fury Special cartridge's edge fingers to a known VCC pin -
still settles the VCC block in minutes and is worth doing before any board.

## Superseded alarm, retained for the record `[MEASURED: 2026-09-23]`

**Read this before generating anything from
[`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv).**

Community members reading **real cartridges with a meter** report the PROG-side
wait-state pins in a different place, and a different order, from ours:

| Pin | This file / our CSV | Reported from real carts |
|---|---|---|
| b25 | **VCC** | **ROMWAIT** |
| b26 | **VCC** | **PWAIT0** |
| b27 | **VCC** | **PWAIT1** |
| b28 | **ROMWAIT** | **PDTACK** |
| b29 | **PDTACK** | 5V |
| b30 | **PWAIT0** | 5V |
| b31 | **PWAIT1** | 5V |

Two separate disagreements, and only one has an easy explanation:

1. **The blocks are swapped.** Ours puts three VCC pins before the wait group;
   theirs puts the wait group first and 5V after. That is what you would see if
   the two sources number from opposite ends - and **this file already records
   that it does not know which physical end SNK calls pin 1**, using
   Board-Folk's convention because it is internally consistent. See below.
2. **The order inside the group differs, and reversal does not explain it.**
   Ours runs ROMWAIT, PDTACK, PWAIT0, PWAIT1. Theirs runs ROMWAIT, PWAIT0,
   PWAIT1, PDTACK. Reversing ours does not produce theirs. One of us has
   `PDTACK` in the wrong place.

**Why this is urgent rather than interesting.** `hardware/lib/neoforge-aes.kicad_sym`
is *generated from this CSV*. A board built from those symbols would wire the
cartridge's four wait-state outputs to the wrong pins - and those are outputs,
so wrong pins mean the cartridge driving lines the console also drives. That is
the bus-contention failure the direction classification exists to prevent,
arriving through the data rather than the tool.

**Their evidence is not weak.** The reports are consistent across several
cartridges - Bubble Bobble, KOF98, KOF2003, Pulsar - with a coherent story
about which are tied high and which low, and a repair that reportedly works. We
have a machine-extracted schematic and an acknowledged uncertainty about pin-1
origin. **Do not assume we are right.**

### How to settle it

1. **`pluger/NeoGeo-161-in-1-v3-MVS-PCB-inverse-ingenering`** publishes TIF scans
   of a 161-in-1 v3 PROG and CHA board, front and rear, under **MIT**. Legally
   usable, and good enough to trace edge fingers back to their pads.
2. **`mvs-scans.com`** carries board scans the community uses for exactly this.
3. **The Fatal Fury Special cartridge already on the bench.** A meter from each
   edge finger to a known VCC pin settles the VCC block in minutes, and that
   alone resolves disagreement 1.

**Until then, treat the wait-state pins in the CSV as `[UNVERIFIED]` and do not
fabricate anything that depends on them.**

## Which board goes where, physically `[VERIFIED: wiki Cartridge orientation]`

Stated first because it is the thing somebody with two loose boards in their
hands needs, and this file previously discussed orientation only in the
transcription sense.

**Counting from the joypad ports at the front, towards the back:**

    CHA bottom → CHA top → PROG bottom → PROG top

So the **CHA board sits in the front slot** (nearer the controllers) and the
**PROG board in the rear**. Viewed from the label side of an assembled
cartridge, the CHA board's bottom face is the one you see first.

On the cartridge in [`teardown-fatal-fury-special.md`](teardown-fatal-fury-special.md)
that makes `NEO-AEG CHA42G-4` the front board and `NEO-AEG PROGGS` the rear one.
The silkscreen names them, so there is no need to infer it from chip content:
the CHA board is the one carrying NEO-ZMC2, NEO-273 and the C ROMs; PROG carries
the P and V ROMs and the NEO-PCM.

## Orientation: the top-face images run the other way

The wiki publishes four images, one per board face. Transcribe them top to
bottom and compare against the AES 3.5 schematic's pin numbering:

| Face | Wiki image order vs. schematic pin order |
|---|---|
| PROG top (`a1`–`a50`) | **opposite** |
| PROG bottom (`b1`–`b50`) | same |
| CHA top (`a1`–`a50`) | **opposite** |
| CHA bottom (`b1`–`b50`) | same |

Detected by scoring both directions against machine-extracted schematic nets:
PROG top matched 6 signals forward and 24 reversed; CHA top 6 and 18; both
bottom faces matched forward (20 and 17) against 6 reversed. Not ambiguous.
`[VERIFIED: cross-check, 2026-09-07]`

The comparison is fair, because rows `a` and `b` are numbered from the same
physical end. From Board-Folk's footprint: `[VERIFIED: NeoGeoAES3_5.kicad_pcb, 2026-09-08]`

```
a1  x=-62.65  y=-11.94       b1  x=-62.65  y=-6.48
a50 x=+61.81  y=-11.94       b50 x=+61.81  y=-6.48
```

Same x positions, different y — the two faces of one slot — both running in the
same direction.

### This is almost certainly not an error upstream

**Correction, 2026-09-08.** An earlier revision of this document called the wiki
images "drawn reversed" and described it as a trap "not stated upstream". That
framing was wrong and is retracted.

Draw each face of a board as you would see it while looking at that face, and
left and right swap when you turn the board over. Per-face viewing orientation
is the natural convention for a reader holding a cartridge, and it is very
likely what the wiki images use. Nothing is broken.

The trap is real but it belongs to the *transcriber*, not the source: flattening
four per-face drawings into one linear numbering without noticing the viewpoint
change silently mirrors half the connector. That is exactly what happened here,
and it is why this document numbers from the schematic rather than from reading
order.

**What is still not established** is which physical end SNK's own numbering
calls pin 1. This document uses Board-Folk's, which is internally consistent and
tied to a real footprint, but that is a reproduction's convention and not
necessarily SNK's. `[UNVERIFIED]` It does not affect wiring — the signal at each
physical position is what matters — but do not assume our `a1` is SNK's `a1`.

---

## Sources and confidence

**A — wiki AES cartridge pinout images.** Four PNGs, read visually 2026-09-07.
The only upstream form; no text or machine-readable version exists.

**B — `Cartridge/aes_cart.v`** (`neogeodev/NeoGeoFPGA-sim`, GPL-3.0). Module
port list, grouped into the same four faces. Gives signal membership and
active-low polarity (overbars are invisible in A's images).

**C — `sheets/cartridge_slots.kicad_sch`** (`Board-Folk/NeoGeoAES-3.5`, public
domain). The console side. Two connector instances, CN4 (CHA) and CN5 (PROG),
each 2×50 with pins numbered `a1`–`a50` and `b1`–`b50`. Nets extracted
programmatically by tracing wires and bus entries from each pin to its label —
no human transcription in this path.

| Claim | Confidence |
|---|---|
| Signal → board face | `[VERIFIED]` — A, B and C agree |
| Signal names | `[VERIFIED]` — all three agree |
| Active-low polarity | `[VERIFIED]` — from B |
| **Pin numbers and ordering** | `[VERIFIED]` — from C, machine-extracted, and A agrees once orientation is corrected |
| **Which end is pin 1** | `[VERIFIED]` — C's numbering is authoritative |
| Row `a` = top face, `b` = bottom | `[UNVERIFIED]` — inferred from signal content matching A's face labels. Consistent across all four faces, but not independently stated |

The remaining uncertainty is only in the *naming* of faces, not in which signals
sit at which numbered pin.

## Two questions this closed

**The audio-loop duplication was real, not a misreading.** A shows `L in`/`L out`
on both top faces and `R out`/`R in` on both bottom faces. C shows all four pairs
**unconnected** on the AES 3.5 — corroborating the wiki's note that these loops
are "only used on the NEO-AES board revision." Two sources, agreeing, on a detail
that looked like a transcription error. `[VERIFIED]`

**`NC` really is not connected.** A marks CHA bottom `b28`/`b29` as `NC`; C leaves
exactly those two pins unconnected.

---

## Pinout

`•` = connected on the AES 3.5 motherboard · `—` = unconnected there ·
`/` = active low

### PROG top — connector CN5, row `a`

| Pin | Signal | AES 3.5 | Pin | Signal | AES 3.5 |
|--:|---|:-:|--:|---|:-:|
| `a1` | `GND` | • | `a26` | `VCC` | • |
| `a2` | `GND` | • | `a27` | `VCC` | • |
| `a3` | `D0` | • | `a28` | `/PORTOEU` | • |
| `a4` | `D1` | • | `a29` | `/PORTOEL` | • |
| `a5` | `D2` | • | `a30` | `/PORTWEU` | • |
| `a6` | `D3` | • | `a31` | `/PORTWEL` | • |
| `a7` | `D4` | • | `a32` | `68KCLKB` | • |
| `a8` | `D5` | • | `a33` | `/RESET` | • |
| `a9` | `D6` | • | `a34` | `SDPAD0` | • |
| `a10` | `D7` | • | `a35` | `SDPAD1` | • |
| `a11` | `D8` | • | `a36` | `SDPAD2` | • |
| `a12` | `D9` | • | `a37` | `SDPAD3` | • |
| `a13` | `D10` | • | `a38` | `SDPAD4` | • |
| `a14` | `D11` | • | `a39` | `SDPAD5` | • |
| `a15` | `D12` | • | `a40` | `SDPAD6` | • |
| `a16` | `D13` | • | `a41` | `SDPAD7` | • |
| `a17` | `D14` | • | `a42` | `SDPA8` | • |
| `a18` | `D15` | • | `a43` | `SDPA9` | • |
| `a19` | `R/W` | • | `a44` | `SDPA10` | • |
| `a20` | `/AS` | • | `a45` | `SDPA11` | • |
| `a21` | `/ROMOEU` | • | `a46` | `SDPMPX` | • |
| `a22` | `/ROMOEL` | • | `a47` | `/SDPOE` | • |
| `a23` | `L out` | — | `a48` | `/PORTADRS` | • |
| `a24` | `L in` | — | `a49` | `GND` | • |
| `a25` | `VCC` | • | `a50` | `GND` | • |

### PROG bottom — connector CN5, row `b`

| Pin | Signal | AES 3.5 | Pin | Signal | AES 3.5 |
|--:|---|:-:|--:|---|:-:|
| `b1` | `GND` | • | `b26` | `VCC` | • |
| `b2` | `GND` | • | `b27` | `VCC` | • |
| `b3` | `A1` | • | `b28` | `/ROMWAIT` | • |
| `b4` | `A2` | • | `b29` | `PDTACK` | • |
| `b5` | `A3` | • | `b30` | `/PWAIT0` | • |
| `b6` | `A4` | • | `b31` | `/PWAIT1` | • |
| `b7` | `A5` | • | `b32` | `SDRAD0` | • |
| `b8` | `A6` | • | `b33` | `SDRAD1` | • |
| `b9` | `A7` | • | `b34` | `SDRAD2` | • |
| `b10` | `A8` | • | `b35` | `SDRAD3` | • |
| `b11` | `A9` | • | `b36` | `SDRAD4` | • |
| `b12` | `A10` | • | `b37` | `SDRAD5` | • |
| `b13` | `A11` | • | `b38` | `SDRAD6` | • |
| `b14` | `A12` | • | `b39` | `SDRAD7` | • |
| `b15` | `A13` | • | `b40` | `SDRA8` | • |
| `b16` | `A14` | • | `b41` | `SDRA9` | • |
| `b17` | `A15` | • | `b42` | `SDRA20` | • |
| `b18` | `A16` | • | `b43` | `SDRA21` | • |
| `b19` | `A17` | • | `b44` | `SDRA22` | • |
| `b20` | `A18` | • | `b45` | `SDRA23` | • |
| `b21` | `A19` | • | `b46` | `SDRMPX` | • |
| `b22` | `/ROMOE` | • | `b47` | `/SDROE` | • |
| `b23` | `R out` | — | `b48` | `4MB` | — |
| `b24` | `R in` | — | `b49` | `GND` | • |
| `b25` | `VCC` | • | `b50` | `GND` | • |

### CHA top — connector CN4, row `a`

| Pin | Signal | AES 3.5 | Pin | Signal | AES 3.5 |
|--:|---|:-:|--:|---|:-:|
| `a1` | `GND` | • | `a26` | `VCC` | • |
| `a2` | `GND` | • | `a27` | `VCC` | • |
| `a3` | `PCK1B` | — | `a28` | `SDRD0` | • |
| `a4` | `PCK2B` | — | `a29` | `SDRD1` | • |
| `a5` | `12M` | • | `a30` | `SDA0` | • |
| `a6` | `2H1` | • | `a31` | `SDA1` | • |
| `a7` | `EVEN` | • | `a32` | `SDA2` | • |
| `a8` | `H` | • | `a33` | `SDA3` | • |
| `a9` | `LOAD` | • | `a34` | `SDA4` | • |
| `a10` | `CA4` | • | `a35` | `SDA5` | • |
| `a11` | `P0` | • | `a36` | `SDA6` | • |
| `a12` | `P2` | • | `a37` | `SDA7` | • |
| `a13` | `P4` | • | `a38` | `SDA8` | • |
| `a14` | `P6` | • | `a39` | `SDA9` | • |
| `a15` | `P8` | • | `a40` | `SDA10` | • |
| `a16` | `P10` | • | `a41` | `SDA11` | • |
| `a17` | `P12` | • | `a42` | `SDA12` | • |
| `a18` | `P14` | • | `a43` | `SDA13` | • |
| `a19` | `P16` | • | `a44` | `SDA14` | • |
| `a20` | `P18` | • | `a45` | `SDA15` | • |
| `a21` | `P20` | • | `a46` | `/SDMRD` | • |
| `a22` | `P22` | • | `a47` | `/SDROM` | • |
| `a23` | `L out` | — | `a48` | `24M` | • |
| `a24` | `L in` | — | `a49` | `GND` | • |
| `a25` | `VCC` | • | `a50` | `GND` | • |

### CHA bottom — connector CN4, row `b`

| Pin | Signal | AES 3.5 | Pin | Signal | AES 3.5 |
|--:|---|:-:|--:|---|:-:|
| `b1` | `GND` | • | `b26` | `VCC` | • |
| `b2` | `GND` | • | `b27` | `VCC` | • |
| `b3` | `FIXD0` | • | `b28` | `NC` | — |
| `b4` | `FIXD1` | • | `b29` | `NC` | — |
| `b5` | `FIXD2` | • | `b30` | `DOTA` | • |
| `b6` | `FIXD3` | • | `b31` | `DOTB` | • |
| `b7` | `FIXD4` | • | `b32` | `GAD0` | • |
| `b8` | `FIXD5` | • | `b33` | `GAD1` | • |
| `b9` | `FIXD6` | • | `b34` | `GAD2` | • |
| `b10` | `FIXD7` | • | `b35` | `GAD3` | • |
| `b11` | `P1` | • | `b36` | `GBD0` | • |
| `b12` | `P3` | • | `b37` | `GBD1` | • |
| `b13` | `P5` | • | `b38` | `GBD2` | • |
| `b14` | `P7` | • | `b39` | `GBD3` | • |
| `b15` | `P9` | • | `b40` | `SDD0` | • |
| `b16` | `P11` | • | `b41` | `SDD1` | • |
| `b17` | `P13` | • | `b42` | `SDD2` | • |
| `b18` | `P15` | • | `b43` | `SDD3` | • |
| `b19` | `P17` | • | `b44` | `SDD4` | • |
| `b20` | `P19` | • | `b45` | `SDD5` | • |
| `b21` | `P21` | • | `b46` | `SDD6` | • |
| `b22` | `P23` | • | `b47` | `SDD7` | • |
| `b23` | `R out` | — | `b48` | `8M` | — |
| `b24` | `R in` | — | `b49` | `GND` | • |
| `b25` | `VCC` | • | `b50` | `GND` | • |

### Note on the `—` marks

Fourteen pins show unconnected. Ten are explained: eight audio-loop pins used
only on the NEO-AES revision, and the two `NC` pins.

The other four — `PCK1B`, `PCK2B` (CHA top) and `8M`, `4MB` (CHA/PROG bottom) —
are almost certainly a limitation of the extraction, not real. The sheet carries
74LS04 and 74HC04 inverters, and those four are inverted or buffered clocks whose
labels sit on the far side of an IC the wire-tracer does not cross.
`[UNVERIFIED]` Do not treat them as no-connects.

---

## Structure worth knowing

**The P bus is split by parity across the CHA faces.** CHA top carries even lines
P0, P2 … P22; CHA bottom the odd P1, P3 … P23. Together `PBUS[23:0]`.

**No C ROM lines cross the connector.** The C ROMs sit on the CHA board and feed
the serializer there; only serialized pixels (`GAD0-3`, `GBD0-3`, `DOTA`, `DOTB`)
leave. This is the mechanism behind [Q1](open-questions.md#q1) and the pin saving
argued in [why-the-split.md](why-the-split.md).

**Wait-state control is on PROG bottom** — `/ROMWAIT`, `PDTACK`, `/PWAIT0`,
`/PWAIT1`, at pins `b28`–`b31`. Cartridge *outputs* telling NEO-C1 how many wait
cycles to insert. See [Q3](open-questions.md#q3).

**Power and ground are the orientation landmarks.** Every face opens with two
`GND` (pins 1, 2), closes with two `GND` (49, 50), and carries three `VCC` at
25–27.

---

## Still to do

- [ ] Confirm the row `a` = top / row `b` = bottom naming against a physical
      cartridge or the arcade-collector board scans.
- [ ] Resolve the four inverter-shadowed pins by tracing through the 74xx04s.
- [x] ~~Second human reading of the wiki images, now that orientation is known.~~ **Done 2026-09-24 — all 200 pins match. See the top of this file.**
- [ ] Compare against the MVS pinout to document what the AES connector drops.

## Sources

- NeoGeo Development Wiki, *AES cartridge pinout*. Wiki content marked public
  domain. Read 2026-09-07.
- `neogeodev/NeoGeoFPGA-sim`, `Cartridge/aes_cart.v`, GPL-3.0.
- `Board-Folk/NeoGeoAES-3.5`, `sheets/cartridge_slots.kicad_sch`. The author
  "makes no claim of copyright … releases these into the public domain."

Corrections welcome. This is the highest-consequence document in the repository.
