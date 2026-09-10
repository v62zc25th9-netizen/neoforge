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

The reason is banking, and it connects directly to
[`prom-banking.md`](prom-banking.md): the 68k sees the first megabyte at
`$000000`–`$0FFFFF` and reaches the rest through the bank window at
`$200000`–`$2FFFFF`. The two halves are not interchangeable, and the container
has to state which is which — by position, since there is no field for it.

**Consequence, if this reading is right:** a homebrew ROM with exactly 2 MB of
P data, converted by `romtool.py`, would produce a `.neo` that runs with its
halves transposed. **`[UNVERIFIED]`** — we have not built such a ROM or run one.
It is cheap to test and worth testing, because if it holds it is a real bug
worth reporting upstream, and if it does not, our reading of the format is
wrong and we should know that too.

Note also that the rule keys on *exactly* 2 MB. What a 3 MB or 5 MB P region
does is not covered by either implementation, and Metal Slug X ships
`1024k + 4096k`. `[VERIFIED: wiki Cartridge ROM arrangements]`

## What this means for Phase 2

The phase was scoped as "build cartridge description tooling." Most of that
exists. The honest remaining work is narrower:

- **The read direction.** Nothing parses a `.neo` or inspects a ROM set. That is
  the actual gap, and it is what `neoforge-rominfo` should be.
- **Verification, not construction.** Given a ROM set: do the C ROMs pair up
  evenly? Is P a legal size? Does the region layout match a known cartridge
  family? Those are the questions that catch problems before an EPROM is burned.
- **Upstreaming beats forking.** An inspect mode in `romtool.py` serves ngdevkit
  users too and costs us less than a parallel implementation. Decide before
  writing code, not after.

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
