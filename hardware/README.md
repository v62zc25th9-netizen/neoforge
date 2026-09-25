# Hardware

Design files. Licensed **CERN-OHL-S-2.0** — see [`../LICENSE.md`](../LICENSE.md).

Nothing here has been manufactured. This is the first PCB artifact the project
has produced.

## `lib/neoforge-aes.kicad_sym`

KiCad symbols for the two AES cartridge connectors: **CN4** on the CHA board and
**CN5** on the PROG board, 100 pins each. `[MEASURED: 2026-09-13]`

**Generated. Do not hand-edit.**

```sh
python3 tools/gen-kicad-symbol.py \
    docs/data/aes-cartridge-pinout.csv \
    hardware/lib/neoforge-aes.kicad_sym
```

[`docs/data/aes-cartridge-pinout.csv`](../docs/data/aes-cartridge-pinout.csv) is
the single source of truth, built by cross-checking three independent sources —
see [`docs/aes-connector.md`](../docs/aes-connector.md). If a pin is wrong, fix
the CSV and regenerate. Editing the symbol directly makes the two disagree
silently, which is the failure this arrangement exists to prevent.

As far as we can tell no AES connector symbol has been published before; the
wiki carries images only.

### Pin directions are from the cartridge's point of view

`input` means the console drives it and the cartridge listens. This is not
cosmetic — it is what lets KiCad's ERC catch a cartridge trying to drive a line
the console already drives, and **bus contention on a 200-pin 5V connector is
the mistake that costs somebody an AES.** See
[`docs/measurement-cart.md`](../docs/measurement-cart.md) §8.

| | CN4 (CHA) | CN5 (PROG) |
|---|---|---|
| input | 54 | 46 |
| output | 18 | 4 |
| bidirectional | 8 | 32 |
| power_in | 14 | 14 |
| passive | 4 | 4 |
| no_connect | 2 | 0 |

Every pin is classified; nothing fell through to a default.

Those counts are worth reading, because they say what a cartridge actually does:

- **CHA's 18 outputs** are `FIXD0-7` (fix tiles straight to the console),
  `GAD0-3` + `GBD0-3` (the serializer's packed pixels) and `DOTA`/`DOTB`
  (opacity). That is the entire video contribution of a cartridge — and Q1 is
  the observation that the first eight of those never touch the serializer.
- **PROG's 4 outputs** are `ROMWAIT`, `PWAIT0`, `PWAIT1` and `PDTACK`. Three of
  them are wait states: **the cartridge tells the console how long to wait for
  it.** That is why our timing work can sweep wait states directly.
- **PROG's 32 bidirectional** pins are the 68k data bus (16) plus the two ADPCM
  data buses (8 each).

### A detail worth knowing before routing anything

`L in`, `L out`, `R in`, `R out` appear at pins **a23, a24, b23, b24 on both
connectors** — cartridge audio pass-through. On the AES 3.5 motherboard our
source data records all eight as **unconnected**.
`[VERIFIED: AES 3.5 KiCad schematic, nets machine-extracted]`

So the pins exist on the edge and go nowhere on at least that revision. Do not
plan to use them, and do not be surprised to find them dead.

## The minimum viable cartridge

Costed 2026-09-13. **Every part is a commodity 5V device still in production**,
which is the practical consequence of Q1 that we had not spelled out: a
fix-layer-only cartridge needs no serializer, no mapper, no CPLD — and because
everything on it runs at 5V, **no level translation either.** The whole
electrical difficulty of Phase 7 is absent from a first board.

| Function | Part | Why |
|---|---|---|
| P ROM | 27C800 (8 Mbit) | our test P is 1 MB; `$000000`–`$0FFFFF` is never banked, so **no bank latch is needed at all** |
| S ROM | 27C010 (1 Mbit) | 128 KB of fix tiles |
| M ROM | 27C010 (1 Mbit) | 128 KB; the BIOS wants a valid Z80 program even for a silent cart |
| V ROM | 27C400 (4 Mbit) | 512 KB. **Not a 27C322** — see the byte-mode trap in [`../docs/prom-banking.md`](../docs/prom-banking.md) |
| Fix address latch | 2 × 74HCT374 | NEO-273's S half — 16 bits on `PCK2B`. See [`../docs/serializer.md`](../docs/serializer.md) |
| `DOTA` / `DOTB` | 2 resistors to GND | tells the console nothing here is opaque; this is what makes the serializer unnecessary |
| Decoupling | 0.1 µF per IC | |

Not on the list, and worth noticing: **no C ROMs, no NEO-ZMC2, no 74LS74 bank
latch, no 74LS08, no level shifters.** Banking is absent because a 1 MB P fits
entirely in the fixed window; add banking only when P exceeds 1 MB.

**HCT, not HC.** 74HCT has TTL input thresholds (2.0 V) where plain 74HC needs
3.7 V. On a bus shared with 1990 TTL parts that distinction is the difference
between working and intermittent.

### On 5V programmable logic — corrected 2026-09-14

An earlier version of this note urged buying ATF150x parts ahead of need,
because they are among the last 5 V programmable logic still in production and
are not being replaced. `[VERIFIED: peterzieba/5Vpld]` **That advice assumed a
serializer needs a 5 V part. It does not.**

`FusionConverter`, a shipping open-hardware AES device, runs its CPLD at
**1.8 V core with 3.3 V I/O** — a Lattice LC4064ZE, whose inputs tolerate 5.5 V
when the bank is set to 3.3 V — sitting directly on the AES bus with no level
shifters at all on the CHA side. `[VERIFIED: FusionConverter BOM; Lattice
DS1022]`

So the scarcity is real and mostly irrelevant to us. A modern low-voltage CPLD
with 5 V-tolerant inputs is available, cheaper, and demonstrably works in this
exact application. Buy ATF150x parts if you want them for their own sake, not
as insurance.

Nothing in the BOM above needs a CPLD at all — a fix-only cartridge has no
serializer to implement.

## `neoforge-prog-connector.kicad_sch` / `neoforge-cha-connector.kicad_sch`

The connector sheets. **Generated. Do not hand-edit — and do not save them from
KiCad**, which will rewrite the format and leave the file disagreeing with the
generator. Changes go in the CSV.

```sh
python3 tools/gen-kicad-sch.py PROG hardware/neoforge-prog-connector.kicad_sch
python3 tools/gen-kicad-sch.py CHA  hardware/neoforge-cha-connector.kicad_sch
python3 tools/test_gen_sch.py          # 20 checks
```

**Opened and verified in KiCad 2026-09-25.** `[MEASURED]` All 100 pins per
connector render with the correct net on the correct pin, checked by eye against
[`../docs/data/aes-cartridge-pinout.csv`](../docs/data/aes-cartridge-pinout.csv)
— including `b25`-`b27` VCC and `b28`-`b31` ROMWAIT/PDTACK/PWAIT0/PWAIT1, the
ordering that [`../docs/aes-connector.md`](../docs/aes-connector.md) spent three
days confirming.

**Netlist verified 2026-09-25** `[MEASURED]` — exported from KiCad and checked
back against the CSV:

```
J1  ->  PROG CN5
  identified from the symbol's Value
  100/100 pins match the pinout
  no issues
```

**Nobody transcribed anything.** The CSV was verified pin for pin against two
independent sources; the symbol is generated from it; the sheet is generated from
it; and `tools/neoforge-netcheck` will assert the exported netlist still agrees.
The one place a human hand enters is the logic sheet, which is where judgement
belongs.

Two things learned getting here, both recorded in the generator:

- **Symbol libraries measure Y upwards, schematic sheets measure Y downwards.**
  Get it backwards and the connector mirrors top to bottom, every label lands on
  the wrong pin, and it looks entirely plausible.
- **A sheet must embed the symbols it uses.** The first version emitted an empty
  `lib_symbols` and KiCad drew a `??` placeholder. Embedding also makes the sheet
  self-contained, so it opens with no library configuration.
- **A global label connects at its anchor.** The first version offset each label
  2.54 mm from its pin so the text would clear it. The sheet rendered perfectly
  and KiCad named every net `unconnected-(J1-D0-Pada3)`, because nothing
  touched. Text clearance is what `justify` is for. **This is the one that
  matters**: a schematic that looks right and connects nothing is precisely what
  `neoforge-netcheck` exists to catch, and it caught it on first contact with a
  real netlist.

## What is not here yet

- **The footprint.** Pad geometry, pitch and mechanical outline need measuring
  off a real cartridge — waiting on the Fatal Fury Special teardown. The symbol
  is fully determined by the pinout; the footprint is not determined by anything
  we have.
- **Any schematic or board.** Phase 7, and still gated on the 5V strategy. See
  [`docs/hardware-constraints.md`](../docs/hardware-constraints.md).
