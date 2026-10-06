# What to buy, and in what order

**Status:** decision record · 2026-10-06 · budget available **~$380**

The question: with money in hand, is it better to buy a flash cartridge or to
start buying components for our own board?

**Answer: build. A flash cartridge for an AES cannot be bought for this budget,
and the money buys a working NeoForge board instead, with change left over for
the second revision.**

---

## 1. Why not a flash cart: the prices settle it

`[VERIFIED: vendor and market listings read 2026-10-06]`

| | Price | Note |
|---|---|---|
| NeoSD Pro AES, new | **$699.99** | Stone Age Gamer, in stock |
| NeoSD AES, used | **~$664 loose**, ~$852 CIB | PriceCharting; recent sales $700–$1,000 |
| NeoSD AES, original retail | €349 | **discontinued**, superseded by the Pro |
| BackBit Neo Geo cart | $400 pre-order / $500 after | **MVS only — no AES version exists** |
| Darksoft Multi AES | listed, price not read | |

**The cheapest route to running our own code on an AES via a bought cartridge is
roughly $660**, and the one product in budget is for the wrong machine. This is
not a close call, and it is the opposite of what the reasoning looked like
before the prices were checked — *"a flash cart is the positive control for
board zero"* was a good argument that the market does not permit.

## 2. Why not the 161-in-1 either, but for a different reason

Cancelling it was right, and not only because the price gap to a full cart is
small. **A 161-in-1 has a fixed ROM set. It cannot run our code**, so it can
never be the positive control that made a flash cart attractive. As a reference
*object* — something to measure and photograph — we already have a cartridge.

## 3. The BIOS: blocked, and worth saying so plainly

`[VERIFIED: AES UniBIOS install writeups, 2026-10-06]` **The AES BIOS is
soldered to the motherboard**, unlike MVS units where it is socketed. Reading it
means desoldering a mask ROM from a working console.

So all three routes to a BIOS dump are closed for now:

| Route | Blocked by |
|---|---|
| flash cart running a dumper | $660 |
| desolder the BIOS and read it | beginner solderer, irreplaceable console |
| buy a UniBIOS chip | still needs desoldering, and it is not the stock BIOS |

**We do not get a BIOS this round.** The real-BIOS emulator test in
[`board-zero.md`](board-zero.md) §8 stays unavailable, and
[`rom-format.md`](rom-format.md)'s open question about which `.neo` P-ordering
convention is correct stays open, because only a NeoSD settles it. Both are real
costs of this decision and neither is fatal. §5 below recovers most of what the
BIOS test would have given us, for nothing.

## 4. What the money should buy

| | Approx | Why |
|---|---|---|
| **EPROM/flash programmer** (XGecu T48 or TL866II+) **+ PLCC32→DIP32 adapter** | $60–90 | **Needed on every path.** Without it the flash chips are paperweights. Also reads the *cartridge's* mask ROMs, which closes several `[UNVERIFIED]` access-time entries |
| **Multimeter** | $25–40 | Continuity-check a fabricated board **before** it goes into a console that cannot be replaced. This is experimental design, not just a tool — see §5 |
| **PCB fab**, 5 boards, gold fingers | $50–80 | Gold fingers are a paid option; confirm at order time |
| **Parts** — 2 × SST39SF040, 2 × PLCC32 socket, 4 × 220 Ω, decoupling | $20 | [`board-zero.md`](board-zero.md) §6 |
| Soldering iron, if there isn't one | $40–60 | |
| **Total** | **~$200–290** | |

Prices are indicative and should be re-checked at purchase. **Leave the
remainder unspent.** There will be a second revision — there always is — and a
budget that assumes otherwise is a budget that stops the project at the first
mistake.

**Buy the programmer and the multimeter first**, before the PCB. They are useful
the day they arrive: the programmer can read the Fatal Fury Special cartridge's
mask ROMs, and the multimeter finishes the card-edge work that
[`card-edge.md`](card-edge.md) §1 wanted it for.

## 5. What replaces the positive control, for free

Losing the flash cart loses the ability to prove our ROM runs on real hardware
*before* trusting a board. Without that, a clicking board zero is ambiguous:
wiring, ROM, BIOS handoff, or timing?

**The fix is in the ROM, not the budget** — see [`board-zero.md`](board-zero.md)
§8a. Instead of kicking the watchdog and stopping, the ROM kicks it for a
*different measured duration depending on how far it got*, so **the length of
the silence before the clicking starts is a diagnostic code you can hear.**

That converts board zero from pass/fail into a staged result, with no
oscilloscope, no flash cart and no BIOS. It does not recover everything — a
board that clicks immediately is still ambiguous between "BIOS refused to hand
over" and "board is dead" — which is exactly why the multimeter is listed above
as part of the experiment: a board whose continuity has been verified makes
"dead" the unlikely branch.

## 6. The order

1. **Free, and still blocking:** the remaining card-edge numbers —
   [`card-edge.md`](card-edge.md) §2 and
   [`teardown-aes-console.md`](teardown-aes-console.md) §4. No PCB can be drawn
   without them.
2. **Free:** write the staged diagnostic ROM (§5).
3. **~$100:** programmer and multimeter.
4. **~$100:** PCB and parts, once 1 is done.
5. **Unspent:** revision two.

## 7. What we are giving up, stated once

- No proof our ROM runs on hardware until board zero itself runs it.
- No BIOS, so no real-BIOS emulator test.
- The `.neo` P-ordering question stays open.
- No reference flash cartridge to measure or compare against.

All four are recoverable later by buying a cart, and none of them blocks
building the board. **The project's purpose is a cartridge of our own, and
$380 is enough to make one — which is not something that has been true before
now.**
