# AES cartridge connector

The Neo Geo AES cartridge edge connector: every pin, with authoritative pin
numbers, cross-checked against three independent sources.

- Machine-readable: [`data/aes-cartridge-pinout.csv`](data/aes-cartridge-pinout.csv)
- Pin pitch 0.1 in (2.54 mm) · board thickness 1.6 mm
- 50 pins per face, 100 per board, **200 per cartridge**

A cartridge is two boards — **PROG** (68000 bus, P ROM, V ROMs) and **CHA**
(graphics, fix layer, Z80 M ROM) — each with contacts on both faces.

---

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
- [ ] Second human reading of the wiki images, now that orientation is known.
- [ ] Compare against the MVS pinout to document what the AES connector drops.

## Sources

- NeoGeo Development Wiki, *AES cartridge pinout*. Wiki content marked public
  domain. Read 2026-09-07.
- `neogeodev/NeoGeoFPGA-sim`, `Cartridge/aes_cart.v`, GPL-3.0.
- `Board-Folk/NeoGeoAES-3.5`, `sheets/cartridge_slots.kicad_sch`. The author
  "makes no claim of copyright … releases these into the public domain."

Corrections welcome. This is the highest-consequence document in the repository.
