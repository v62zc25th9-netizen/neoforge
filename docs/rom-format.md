# ROM sets and the `.neo` format

How a Neo Geo game is stored as files, how Terraonion's `.neo` container is laid
out, and what NeoForge would need beyond it.

Roadmap Phase 2 scoped "cartridge description tooling" before we had read what
already exists. Having read it: **most of the write direction is solved twice
over**, and the useful work is smaller and different from what was planned.

---

## A ROM set is five regions

| Region | Contents | Board |
|---|---|---|
| `P` | 68k program | PROG |
| `V` | ADPCM samples | PROG |
| `C` | sprite graphics, in pairs | CHA |
| `S` | fix-layer tiles | CHA |
| `M` | Z80 program | CHA |

Sizes and the physical split are in
[`hardware-constraints.md`](hardware-constraints.md). The C ROMs come in
**pairs**: odd files carry bitplanes 0 and 1, even files carry 2 and 3, which is
what the serializer expects. See [`serializer.md`](serializer.md).

## Two existing implementations, and they mostly agree

| | |
|---|---|
| `dciabrin/ngdevkit` — `tools/romtool.py` | 609 lines, Python, LGPL. Builds zip, MAME, GnGeo **and** `.neo`. |
| `city41/neosdconv` | TypeScript, MIT. Builds `.neo` only, for homebrew. |

Neither reads a `.neo` back. Both go one way: ROM files in, container out.

### The `.neo` container `[VERIFIED: both implementations independently]`

A **4096-byte header**, then the regions concatenated in a fixed order.

```
offset  size  field
------  ----  -----------------------------------------------
0x000      3  "NEO"
0x003      1  version = 1
0x004      4  P size          little-endian uint32
0x008      4  S size
0x00c      4  M size
0x010      4  V1 size
0x014      4  V2 size
0x018      4  C size
0x01c      4  year
0x020      4  genre
0x024      4  screenshot      (Terraonion-proprietary; 0 for homebrew)
0x028      4  NGH number      (game id, parsed as hex: NGH-041 -> 0x041)
0x02c     33  name            null-padded
0x04d     17  manufacturer    null-padded
0x05e   ...   zero fill to 0x1000
0x1000  ...   P, then S, then M, then V1, then V2, then C
```

**Padding:** P, S, M and V are padded to a 64 KB multiple; C is padded to
256 KB. Both implementations pad with `0xFF`.

**C interleaving:** each `(c1, c2)` pair is byte-interleaved into one block —
`c1[0], c2[0], c1[1], c2[1], …` — and the interleaved pairs are then
concatenated. This stores the data the way the hardware consumes it rather than
the way the ROM chips are organised.

**V1 / V2:** some games split samples across two regions; ngdevkit always emits
one, leaving V2 empty.

## Where they disagree — and it matters

`neosdconv` contains this, and `romtool.py` has no equivalent:

> Takes an array that is 2 megabytes in size and swaps the megabytes. This is
> required for large P ROMs, such as in King of Fighters 94.

So when the total P data is **exactly 2 MB**, `neosdconv` writes the second
megabyte first; `romtool.py` concatenates in order.

**The 2 MB threshold is not arbitrary — it is exactly the point where banking
stops being needed.** From [`prom-banking.md`](prom-banking.md):

- `$000000`–`$0FFFFF` — 1 MiB, fixed, never banked. Holds the 68k vector table.
- `$200000`–`$2FFFFF` — 1 MiB, the banked window. **Reset clears the bank
  latches, so bank 0 is mapped at power-on.**

So a game with 2 MB of P has one megabyte fixed at `$000000` and the other
sitting in the window as bank 0 — both visible simultaneously, with no bank
switch ever executed. **2 MB is the largest P a game can have while remaining
an unbanked game.**

Which is precisely why the container has to say which megabyte is which, and
why it can only say it by position: there is no field for it, and above 2 MB the
question is settled by the file split instead (`p1` fixed, `p2` banked).

**Consequence, if this reading is right:** a homebrew ROM with exactly 2 MB of
P data, converted by `romtool.py`, would produce a `.neo` that runs with its
halves transposed. **`[UNVERIFIED]`** — we have not built such a ROM or run one.
It is cheap to test and worth testing, because if it holds it is a real bug
worth reporting upstream, and if it does not, our reading of the format is
wrong and we should know that too.

### We ran the experiment `[MEASURED: 2026-09-12]`

Built two synthetic ROM sets with a 2 MB P made of two distinguishable
megabytes — one marked `MEG0`, one `MEG1` — and converted each with both tools.
Case A had P as a single 2 MB `p1`; case B split it as `p1` + `p2`, 1 MB each.

| Converter | Input | First meg in the `.neo` | Second |
|---|---|---|---|
| `romtool.py` | single 2 MB `p1` | `MEG0` | `MEG1` |
| `neosdconv` | single 2 MB `p1` | **`MEG1`** | **`MEG0`** |
| `romtool.py` | `p1` + `p2` | `MEG0` | `MEG1` |
| `neosdconv` | `p1` + `p2` | **`MEG1`** | **`MEG0`** |

**The two tools produce different `.neo` files from identical input.** The P
regions differ byte for byte, in both cases. At least one of them is wrong, and
anybody who builds a homebrew ROM with a 2 MB P using ngdevkit and runs it on a
NeoSD will find out which.

**A correction to what this document said before.** It argued that swapping the
two-file case would "invert a mapping that was not ambiguous," since `p1` and
`p2` name their own roles. That was wrong. If the container's convention is
*banked half first, fixed half second* — which is what `neosdconv`'s comment,
citing a Terraonion forum post, says it is — then swapping `[p1][p2]` into
`[p2][p1]` is the **consistent** thing to do, not an inversion. `neosdconv` is
self-consistent at 2 MB; the disagreement with `romtool.py` is the finding, not
the split case specifically.

**Still open: which one is right.** The experiment shows they differ; it cannot
show whose convention matches Terraonion's loader. `neosdconv` cites a primary-
ish source and `romtool.py` cites none, which is weak evidence for `neosdconv`
and against `romtool.py` — but only weak. Settling it needs a NeoSD and a 2 MB
homebrew ROM.

**And it still does not generalise.** The rule fires at exactly 2 MB and says
nothing about any other size. Metal Slug X ships `1024k + 4096k` — 5 MB across
two files — where `neosdconv` does not swap at all.
`[VERIFIED: wiki Cartridge ROM arrangements]` If the convention really is
banked-first, that ordering looks inconsistent across sizes, and we cannot
explain it.

`tools/neoforge-rominfo` warns on any ROM set or `.neo` with a 2 MB P region, so
nobody hits this silently.

## What this means for Phase 2

The phase was scoped as "build cartridge description tooling." Most of that
exists. The honest remaining work is narrower:

- **The read direction.** Nothing parses a `.neo` or inspects a ROM set. That was
  the actual gap, and `tools/neoforge-rominfo` now fills it — see
  [`../tools/README.md`](../tools/README.md). `[MEASURED: 2026-09-12]`
- **Verification, not construction.** Given a ROM set: do the C ROMs pair up
  evenly? Is P a legal size? Does the region layout match a known cartridge
  family? Those are the questions that catch problems before an EPROM is burned.
- **Upstreaming beats forking.** An inspect mode in `romtool.py` serves ngdevkit
  users too and costs us less than a parallel implementation. Decide before
  writing code, not after.

## What the format's *silence* tells us

The `.neo` header carries sizes, year, genre, screenshot and NGH number. It does
**not** carry a mapper, a cartridge family, a protection type, or an encryption
flag. `[VERIFIED: both implementations]`

That absence is informative. A cartridge that had to reproduce each game's
original mapping and protection would need to be told which — and the container
never says. So either the loader identifies games some other way, or it does not
need to know.

It does not need to know. `bodgit/terraonion` is a third-party Go
reimplementation of the conversion (BSD-3-Clause), and its README states the
mechanism plainly: *"the ROM images will be unscrambled and processed based on
the same logic MAME uses."* Its source carries **56 per-game reader functions**
alongside generic paths named `commonCMC42Reader`, `commonCMC50Reader`,
`commonPVCReader`, `commonPCM2Reader` and `commonK2K2Reader` — the Neo Geo's
encryption and protection families. Those functions do XOR key application and
bit-swapping over the ROM data at **conversion time**.

**So the cartridge is handed already-decrypted, already-descrambled, normalised
data.** The work happens on the PC, once, before the file ever reaches the card.

This explains a detail that looked odd earlier: `neosdconv`'s README says it is
homebrew-only and directs commercial games to TerraOnion's own NeoBuilder. Of
course it does — `neosdconv` implements none of that per-game work. Homebrew has
nothing to decrypt.

### A correction to our roadmap

Phase 10 described the choice as *"precompute offline (cheaper, incompatible ROM
format) versus emulate live like NeoSD (harder, unpatched games work)"*.

**NeoSD does not emulate live. It precomputes offline.** The evidence above is
against our own framing, and the framing was making the cheaper option look like
the compromise when it is what the market leader actually ships.

The trade named in that sentence is still real — a normalised `.neo` is not the
same bytes as a MAME set, so you cannot drop a plain zip onto the card and the
conversion step is mandatory. That cost is apparently one the market accepts.

### What this does *not* settle

Two things worth keeping separate, because "the NeoSD precomputes" is easy to
over-read:

- **Bank switching is not encryption.** PROGBK1-style banking is live address
  decoding the cartridge must implement — a write selects a bank, a read uses
  it. No amount of offline processing removes that. See
  [`prom-banking.md`](prom-banking.md).
- **Live protection registers are a separate question.** Chips like PVC and
  NEO-SMA both scramble data *and* answer reads at protection addresses.
  Precomputing handles the scrambling. Whether the remaining live behaviour is
  emulated on the card or patched out of the ROM is not something this evidence
  answers.

`[UNVERIFIED]` as to TerraOnion's own implementation — `bodgit/terraonion` is a
reimplementation by a third party, not vendor documentation. It is strong
evidence about what the format requires, since the files it produces reportedly
work, but it is not authoritative.

## `.neo` is a transfer format, not a memory layout

Worth separating, because Phase 9 conflates them.

`.neo` describes **a file that carries a game**. What a cartridge needs is a
**memory layout** — where each region sits in physical memory so that five
consumers can read it concurrently across two boards. Those are different
problems and the answer to one does not give you the other.

So NeoForge should probably:

- **Read `.neo`**, because tooling and converted libraries already exist and
  MiSTer uses it. Compatibility is free reach.
- **Define its own on-card layout**, and publish it — which is Phase 9's actual
  intent.

One correction to the roadmap's framing while we are here: it says the on-card
format should be "deliberately specified in public, unlike NeoSD's and
Darksoft's." `.neo` is in fact publicly documented — in working, MIT-licensed
code, by `neosdconv`. Documented by a third party through reverse engineering
rather than by its vendor, which is a meaningful difference, but not the same as
undocumented. We should say the true thing.

---

## Sources

- `dciabrin/ngdevkit`, `tools/romtool.py` — LGPL
- `city41/neosdconv`, `src/buildNeoFile.ts` — MIT
- [Cartridge ROM arrangements](https://wiki.neogeodev.org/index.php?title=Cartridge_ROM_arrangements) — NeoGeo Development Wiki
- [Meg count](https://wiki.neogeodev.org/index.php?title=Meg_count) — NeoGeo Development Wiki

*Corrections welcome and actively wanted. Open an issue.*
