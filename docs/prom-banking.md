# P ROM banking and cartridge families

How the 68000 sees cartridge program ROM, how banking works, and why a
NeoForge board must reproduce a specific original board's behaviour rather
than invent its own.

Sources: NeoGeo Development Wiki — *Bankswitching*, *PROGBK1*, *68k memory
map*, *NEO-SMA*, *NEO-PVC*. Read 2026-09-08. Wiki content is public domain.

---

## 1. The console has no banking hardware at all

**All banking logic lives on the cartridge's PROG board.**
`[VERIFIED: wiki Bankswitching]` The 68000 issues a write, then reads an
address. It has no bank register, no mapper, and no idea that banking exists.

That is the useful half of the intuition "the AES doesn't care about banking,
it just wants the data." Correct — the console genuinely does not care.

## 2. But the *game* cares enormously

Banking is not transparent. The game's own code contains the bank writes:

```asm
move.w #3,$200000    ; bank 3: ROM $300000-$3FFFFF appears at $200000-$2FFFFF
move.b #1,$2B92F1    ; bank 1: ROM $100000-$1FFFFF appears at $200000-$2FFFFF
```

`[VERIFIED: wiki Bankswitching]`

The ROM is compiled against one specific mapping from *written value* to
*which megabyte appears in the window*. A cartridge that decodes those writes
differently — more bits, different bit order, a different trigger address —
maps the wrong megabyte, and the 68000's next instruction fetch lands in
unrelated code.

**This does not produce artifacts. It produces an immediate crash.** The
program counter is executing whatever bytes happen to be at that offset in
another bank. There is no graceful degradation, and no visual tell that the
banking was the cause.

**Consequence for NeoForge: banking must be bug-compatible with the original
board the game shipped on, per game.** This is not a place to improve on the
design.

## 3. The memory map

`[VERIFIED: wiki 68k memory map]`

| Range | Size | Wait cycles | What |
|---|---|---|---|
| `$000000`–`$0FFFFF` | 1 MiB | **0 or 1** (4/5 clks), per `ROMWAIT` | Vector table + first **fixed** bank of P ROM |
| `$100000`–`$10F2FF` | 64 KiB | 0 (4 clks) | Work RAM |
| `$10F300`–`$10FFFF` | | | System-ROM-reserved RAM |
| `$110000`–`$1FFFFF` | | 0 (4 clks) | Work RAM mirror |
| `$200000`–`$2FFFFF` | 1 MiB | **0 to 3** (4/7 clks), per `PWAIT` | Second, **banked** P ROM window; also bank writes and special chips |
| `$300000`–`$3FFFFF` | | 0 (4 clks) | I/O registers |
| `$400000`–`$401FFF` | 8 KiB | 0 (4 clks) | Palette RAM |
| `$800000`–`$BFFFFF` | 8 MiB max | 2 (6 clks) | Memory card |
| `$C00000`–`$C1FFFF` | 128 KiB | 0 (4 clks) | System ROM |
| `$D00000`–`$D0FFFF` | 64 KiB | 0 (4 clks) | Backup RAM (MVS only) |

Two things to take from this:

- **`$000000`–`$1FFFFF` is never banked.** The wiki notes no game bankswitches
  the ROM range. Only the PORT range at `$200000` moves.
- **A bank switch is a write into `$200000`–`$2FFFFF`** — the same window the
  banked ROM is read from. Write to select, read to use.

## 4. The mechanism, concretely

Taking PROGBK1 as the worked example `[VERIFIED: wiki Bankswitching, PROGBK1]`:

- A **74LS74 dual D-latch** holds the bank number.
- **Any write to an odd address** in `$200000`–`$2FFFFF` pulls `/PORTWEL` low,
  latching data bits `D0` and `D1`.
- Those two latch outputs drive the P2 ROM's **`A20` and `A21`**.
- Two bits → four 1 MiB banks of a 4 MiB P2 ROM.
- **Reset clears both latches**, so bank 0 is mapped at power-on.

Wider ROMs use more bits; the principle does not change.

### The `/PORTOE` gotcha

**There is no `/PORTOE` signal on the cartridge edge connector** — unlike
`/ROMOE`, which is a real pin. `/PORTOEL` and `/PORTOEU` must be **ANDed on the
cartridge** to produce P2's `/OE`. PROGBK1 uses a **74LS08** for exactly this.
`[VERIFIED: wiki Bankswitching, PROGBK1]`

Confirmed independently by our own connector work: `docs/aes-connector.md` lists
`/PORTOEL` and `/PORTOEU` on PROG top and no `/PORTOE` anywhere.

## 5. Cartridge families

Games are grouped by PROG board type, and the board determines both banking and
protection. The families that matter:

| Board / chip | Banking | Protected | Notes |
|---|---|---|---|
| **PROGBK1** | 74LS74, 2 bits | **No** | *"The only non-protected board that can bankswitch and use all V ROM space. Really common and very useful for homebrew stuff or converts."* `[VERIFIED: wiki PROGBK1]` |
| **NEO-SMA** | Scrambled | Yes | Bankswitches `$200000`–`$2FFFFF` and provides a 16-bit PRNG for protection `[VERIFIED: wiki NEO-SMA]` |
| **NEO-PVC** | Yes | Yes | Bankswitching *and* security, on ROM-only boards and late carts — SVC Chaos, Metal Slug titles `[VERIFIED: wiki NEO-PVC]` |
| **PROGEOP**, **PROGSF1** | Yes | Yes (Altera MAX CPLD) | Metal Slug X, KOF '98 — see `cartridge-architecture.md` §5 |

**PROGBK1 is NeoForge's target.** It is the only non-protected banking board,
it is explicitly recommended for homebrew and conversions, and its entire logic
is three 74-series parts: **LS74** (bank latch), **LS08** (`/PORTOE`), **LS139**
(V ROM chip select).

That is worth restating plainly: **a non-protected, banking AES PROG board needs
no custom silicon and no programmable logic — three TTL chips and some EPROMs.**
Combined with `open-questions.md` Q1, which removes the serializer requirement
for a fix-only cartridge, the first NeoForge board is looking distinctly
buildable.

## 6. PROGBK1 configuration, for reference

`[VERIFIED: wiki PROGBK1]`

- **P1**: 4, 8 or 16 Mbit (27C400 / 27C800 / 27C160), appears at `$000000`.
- **P2**: same types plus 27C322, banked into `$200000`.
- **V ROM**: up to four, 8/16/32 Mbit, 16 MiB total.
- Extensive jumper matrix (J1–J13, JB1–JB6, JV1–JV14) selects ROM sizes and
  which signals drive `/CE` and `/OE`. The wiki page has the full table.

### The 27C322 V ROM trap

**A 27C322 cannot be used as a V ROM.** The V ROM data bus is 8-bit — byte mode
— and the 27C322 only operates in word mode. Original mask ROMs could output in
byte mode; programmable 42-pin EPROMs physically lack a `/BYTE` pin. Replacing a
32 Mbit V ROM needs a different memory IC on an adapter board.
`[VERIFIED: wiki PROGBK1]`

This is exactly the class of gotcha that makes a donor-cart conversion fail
confusingly, and it is worth knowing before ordering parts.

---

## What this changes for NeoForge

1. **A first board is three TTL chips plus EPROMs**, if it targets PROGBK1
   semantics and forgoes sprites (Q1).
2. **Banking must be per-family, not general.** Any future flash cart needs to
   know which board each game shipped on and reproduce that board's decode. This
   is what roadmap Phase 2's ROM analysis tooling is actually for — and what
   `romtool.py` does not do.
3. **Protection is a separate axis from banking.** PROGBK1 gives banking with no
   protection; SMA and PVC entangle the two deliberately.
4. **Do not invent a mapper.** Reproducing SNK's is the requirement.

## Still to do

- [ ] Enumerate which games ship on which PROG board — MAME's `neogeo.cpp` slot
      definitions are the machine-readable source.
- [ ] Read the PROGBK1 schematic and record the exact jumper settings NeoForge
      would hard-wire.
- [ ] Document the CHA-side equivalent (S/M/C ROM decode and NEO-273 latching).
- [ ] Confirm `/PORTWEL`-only latching (odd-address writes) against a second
      source — it determines whether byte writes to even addresses are ignored.
