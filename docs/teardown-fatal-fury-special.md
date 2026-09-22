# Teardown: Fatal Fury Special (AES)

First real cartridge this project has had in hand. `[MEASURED: 2026-09-21]`
Photographs only so far - nothing desoldered, nothing measured electrically.

**NGH 058.** Every mask ROM is marked `058-xx`, which is how the boards confirm
their own identity.

## The two boards

| | Silkscreen |
|---|---|
| PROG | `SNK NEO-AEG PROGGS` · `HCMK-C2X` · MADE IN JAPAN |
| CHA | `SNK NEO-AEG CHA42G-4` · `HCMK-C2X` · MADE IN JAPAN |

The PROG/CHA split that [`why-the-split.md`](why-the-split.md) describes from
documentation is exactly what the physical cartridge is: two separate boards,
two edge connectors.

## PROG board

| Position | Part | Marking |
|---|---|---|
| P1 | Toshiba **TC538200AP** | `058-PG1` R762, date 9339 |
| SP2 | Toshiba **TC534200P** | `058-P2` R756, date 9339 |
| V1 | Toshiba **TC5316200BP** | `058-V1` R746, date 9344 |
| V2 | Toshiba **TC5316200BP** | `058-V2` R747, date 9344 |
| V3 | Toshiba **TC538200AP** | `058-V3` R754, date 9344 |
| PCM | **SNK CORP PCM** | 9309 W20 |
| - | 74LS08, 74LS32, 74LS139 | |
| EP1, EP2 | **empty** | silkscreened `TC574096` |

`TC538200` is 8 Mbit (1 MB); `TC534200` is 4 Mbit (512 KB). So P is **1 MB +
512 KB = 1.5 MB**, which is 512 KB past the fixed window and therefore needs
one bank - the smallest banking case `neoforge-rominfo` describes, and well
inside PROGBK1's two bits.

**`EP1`/`EP2` are unpopulated EPROM footprints**, silkscreened with a part
number. The board was laid out to accept either mask ROMs or EPROMs in the P
positions. Worth knowing for anyone building a compatible board.

## CHA board

| Position | Part | Marking |
|---|---|---|
| C1-C6 | Toshiba **TC5316200BP** x6 | `058-C1` .. `058-C6`, R748-R753, date 9344 |
| C8 | **empty** | silkscreened `TC5316200` |
| M1 | Toshiba **TC531001CP-12** | `058-M1` R758, date 9344 |
| S1 | Toshiba **TC5310000CP** | `058-S1` R757, date 9344 |
| - | **SNK CORP NEO-ZMC2** | 9310 W70 |
| - | **SNK CORP NEO-273** | 9332 B98 |
| - | 74LS74, 74LS139, 74LS32 | |

**Both custom chips are present and on the CHA board**, where
[`serializer.md`](serializer.md) and [`cartridge-architecture.md`](cartridge-architecture.md)
said they would be. NEO-ZMC2 is the sprite serializer; NEO-273 latches the C and
S addresses off PBUS. A NeoForge CHA-side board has to replace both.

## The first correction from silicon `[MEASURED: 2026-09-21]`

**M1 is a `TC531001CP-12`. The `-12` is a speed suffix: 120 ns.**
`[VERIFIED: Toshiba TC531001CP datasheet - "120ns; 1M bit (128K word x 8 bit)
CMOS MASK ROM"]`

[`hardware-constraints.md`](hardware-constraints.md) records M at **100 ns**,
taken from NeoGeoFPGA-sim's ROM model annotations. **A real cartridge in hand
uses a 120 ns part.** The model's annotation is optimistic for M by 20 ns.

This does not change any conclusion - 120 ns is what P uses too, and the budget
work shows the bus has room - but it is the first time this project has checked
one of its borrowed numbers against a physical part, and the borrowed number was
wrong. The other positions carry no speed suffix in their markings, so their
access times remain unknown from photographs alone.

## Still unknown from photographs

- Access times for the `TC538200AP`, `TC534200P`, `TC5316200BP` and
  `TC5310000CP` positions. No speed suffix is marked. Datasheets would give the
  range available, not which grade SNK bought.
- The **connector footprint** - pad geometry, pitch, mechanical outline - which
  is what [`../hardware/README.md`](../hardware/README.md) says the KiCad symbol
  is still waiting on. That needs measurement, not pictures.
- Whether this particular board has been reworked. Some joints near one edge
  look hand-finished rather than machine-soldered, and there is discolouration
  that could be flux residue or could be heat damage. **Not determinable from a
  photograph.**

## A diagnostic ladder, learned by accident `[MEASURED: 2026-09-21]`

This cartridge has a warped board and would not boot, which turned out to be
more instructive than a working one.

| Symptom | What the console managed |
|---|---|
| **Blue screen / grid** | Read nothing. The BIOS runs and finds no cartridge. |
| **Repeating click, ~3.7 Hz** | Read *some*. The 68000 executes, crashes, and the watchdog resets it before it can be kicked - the "click of death". See [`open-questions.md`](open-questions.md) Q3 for the ~128 ms timeout. |
| **Boots** | Read enough. |

Moving from the first to the second by reseating the boards is a contact
problem, not a logic one. **This is how a NeoForge board's first power-on gets
triaged without a scope**, and it is worth knowing before that evening rather
than during it.

**Do not run bare boards outside the shell.** Nothing holds them square, so
which fingers connect changes every insertion, and a 5V bus is being powered
through a partly-made connection. The shell is the alignment fixture. The
console's slot is harder to replace than anything on the cartridge.
