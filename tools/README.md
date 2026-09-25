# Tools

MIT licensed. Python 3, standard library only — no dependencies to install.

## `neoforge-rominfo`

Inspects a Neo Geo ROM set or a `.neo` cartridge image and checks it against
what the hardware accepts.

```sh
tools/neoforge-rominfo game.neo
tools/neoforge-rominfo ./romfiles/
tools/neoforge-rominfo game.zip
tools/neoforge-rominfo game.neo --json
```

Exit status is **1 if any error was found**, 0 otherwise, so it can gate a
build.

### Why it exists

Everything that already existed goes one way. ngdevkit's `romtool.py` and
city41's `neosdconv` both take ROM files and produce a container; **neither
reads one back.** This is the read direction, and it was the honest gap in
roadmap Phase 2 once we had read both tools properly.

### What it reports

```
  region        size          megs  board  files
  ------    --------      --------  -----  -----
  P             1 MB        8 MEGS  PROG   neoforge-fixtest-p1.p1
  S           128 KB        1 MEGS  CHA    neoforge-fixtest-s1.s1
  M           128 KB        1 MEGS  CHA    neoforge-fixtest-m1.m1
  V           512 KB        4 MEGS  PROG   neoforge-fixtest-v1.v1
  C             4 MB       32 MEGS  CHA    ...-c1.c1, ...-c2.c2
  ------    --------
  total      5888 KB       46 MEGS

  PROG board    1536 KB      CHA board    4352 KB
```

The **board column is not decoration.** P and V are served by the PROG board,
C, S and M by CHA, and those are two separate memory systems with different
consumers running concurrently — which is the fact that shapes any cartridge
design. See [`../docs/hardware-constraints.md`](../docs/hardware-constraints.md).

`MEGS` is the Neo Geo's own marketing unit: 1 MEG is 1 megabit, 128 KB.

### What it checks

| Check | Level |
|---|---|
| `.neo` magic and version | error |
| Header sizes add up to the file length | error |
| C ROMs come in pairs | error |
| Paired C ROMs are the same size | error |
| Region exceeds the largest seen in the wild | warning |
| ROM file size is not a power of two (`romtool.py` rejects these) | warning |
| **P region is exactly 2 MB** — see below | warning |
| Missing S, M, P or C | warning |

### What the shape implies

Beyond listing regions, it reports what a ROM set's *dimensions* constrain about
the board it came from — and, as importantly, what they do not.

```
  what the shape implies
  ----------------------
  banking        required - 7 MB sits beyond the fixed window
  bank window    7 x 1 MB at $200000-$2FFFFF, needs 3 bits
  PROGBK1        NOT enough - it provides 2 bits, up to 5 MB of P
  fix source     C ROMs (no S ROM)
  protection     not inferable from a ROM set
```

The reasoning, all from [`../docs/prom-banking.md`](../docs/prom-banking.md):

- `$000000`–`$0FFFFF` is fixed and **never banked**, so a P that fits there
  needs no mapper at all — which is why our own test ROM has no bank latch.
- Anything above it is reached through the 1 MiB window at `$200000`–`$2FFFFF`,
  so the bank count is `ceil((P − 1 MiB) / 1 MiB)` and the bit count follows.
- **PROGBK1 holds its bank number in a 74LS74 — two bits, four banks, so at
  most 5 MB of P.** PROGBK1 is NeoForge's target because it is the only
  non-protected banking board, so "could a PROGBK1 copy run this?" is a
  question worth answering automatically.
- **No S ROM means the fix layer comes from the C ROMs**, which is what late
  CHAFIO boards do. `[VERIFIED: wiki Cartridge ROM arrangements — Metal Slug 3,
  4, 5]` A compatible cartridge has to reproduce that, and NeoForge does not yet
  document it.

Checked against real games: Metal Slug X (1024k + 4096k) comes out as four
banks and two bits, within PROGBK1's capacity; Metal Slug 3 (2 × 4096k) as seven
banks and three bits, beyond it — and Metal Slug 3 does in fact use PROGLBA.

**It will not name a board, and that is deliberate.** Protection and encryption
— NEO-SMA, NEO-PVC, the CMC families — are properties of a *game*, not of a ROM
set's dimensions. Identifying them needs a database keyed by game, which is
precisely what TerraOnion's NeoBuilder has and `neosdconv` does not. See
[`../docs/rom-format.md`](../docs/rom-format.md). Sizes constrain the board;
they do not name it, and guessing would be wrong often enough to be worse than
useless.

Note the distinction the tool is careful about: Metal Slug X is PROGBK1-capable
*for banking* and still ships on PROGEOP, because it needs protection. The tool
answers only the question it can.

### The 2 MB P warning

At exactly 2 MB of P, **`romtool.py` and `neosdconv` produce different `.neo`
files from identical input** — `neosdconv` swaps the two megabytes and
`romtool.py` does not. Verified by experiment, not by reading.
`[MEASURED: 2026-09-12]`

2 MB is not an arbitrary size: it is the largest P a game can have while never
needing a bank switch, so it is the one case where the container must say which
megabyte is the fixed half and which is banked — and it can only say so by
position. The full write-up, including which tool is probably right, is in
[`../docs/rom-format.md`](../docs/rom-format.md).

The tool warns rather than errors, because we do not yet know which convention
is correct.

## `gen-kicad-symbol.py`

Generates KiCad symbols for the two AES cartridge connectors from the pinout
CSV.

```sh
python3 tools/gen-kicad-symbol.py \
    docs/data/aes-cartridge-pinout.csv \
    hardware/lib/neoforge-aes.kicad_sym
```

The CSV is the single source of truth; the symbol is generated and must not be
hand-edited. Pin electrical types are assigned from the cartridge's point of
view, so KiCad's ERC can catch a cartridge driving a line the console already
drives. It prints a summary of how every pin was classified, and lists anything
its direction table did not match — so unclassified pins are visible rather than
quietly defaulted.

See [`../hardware/README.md`](../hardware/README.md).

## `neoforge-evidence`

```sh
tools/neoforge-evidence            # regenerate docs/evidence-index.md
tools/neoforge-evidence --stdout   # print instead
tools/neoforge-evidence --check    # exit 1 if the committed index is stale
```

Walks the tree and collects every `[VERIFIED]` / `[MEASURED]` / `[ANECDOTAL]` /
`[UNVERIFIED]` tag into [`../docs/evidence-index.md`](../docs/evidence-index.md),
weakest first.

**Why it exists.** The convention was applied carefully in every file and
indexed nowhere, so a soft claim was visible only to whoever happened to be
reading the file that carried it. The C1/C2 byte-order note in
[`../sim/harness/mkdata.py`](../sim/harness/mkdata.py) says *"revisit before
trusting sprite output"* and nothing outside that file knew it existed. Now the
list of everything we are unsure about is one page.

`claude.md` and `contributing.md` are skipped deliberately: they *define* the
convention, and indexing "`[UNVERIFIED]` — inference not yet confirmed" as an
unverified claim is a category error that buries the real ones.

`--check` is the useful mode for CI. The index is generated, so it can drift
from the claims it indexes, and drift here is exactly the failure the tool is
meant to prevent. **Do not hand-edit the output** - fix the tag at its source
and re-run.

### The refusal to name a board was right `[ANECDOTAL: 2026-09-23]`

`analyse_cartridge()` deliberately reports `protection: not inferable`, on the
grounds that protection and encryption are properties of a *game*, not of a ROM
set's dimensions. Community tooling for the 161-in-1 confirms the shape of that:
its converter fails per-game with errors naming **numbered modes** -

    bankswitching mode 2 in svc / kof2003 / mslug5
    bankswitching mode 3 in kof99
    bankswitching mode 4 in garou
    bankswitching mode 6 in mslug3
    bankswitching mode 7 in kof2000
    graphics mode 5 in mslug4
    graphics mode 6 in matrim

Two independent axes - bankswitching and graphics - each with a small integer
per title, and no way to derive either from region sizes. Exactly the database
keyed by game that `rominfo` says it would need and does not have. The honest
refusal holds.

## `neoforge-netcheck`

```sh
tools/neoforge-netcheck board.net              # check every connector found
tools/neoforge-netcheck board.net --ref J1     # just this designator
tools/neoforge-netcheck board.net --json
```

Reads a KiCad netlist and asserts every cartridge-connector pin carries the net
[`../docs/data/aes-cartridge-pinout.csv`](../docs/data/aes-cartridge-pinout.csv)
says it should. Exit 1 on any mismatch, with "Do not fabricate."

**Why it exists.** The CSV generates the KiCad symbol and is now verified pin
for pin against two independent sources. None of that protects a *schematic*
from wiring the right pin to the wrong net - one transposition out of 200 on a
5V edge connector, which is the error that costs a board spin and possibly a
console. This closes the loop: CSV → symbol → schematic → netlist → back to the
CSV.

It checks for missing pins, pins the pinout does not contain, wrong nets, and
**NC pins that are quietly connected** - that last being the kind of thing that
only shows up as smoke.

Net names are compared leniently, because schematics legitimately decorate them.
Case is ignored; a leading `/` or `Net-` is stripped; `nAS`, `/AS`, `AS_N` and
`~AS` all equal `AS`; and power nets match as families, so `VCC`/`+5V`/`VDD` are
one net and `GND`/`VSS` another.

## `test_netcheck.py`

```sh
python3 tools/test_netcheck.py
```

27 checks, 0 failures. `[MEASURED: 2026-09-25]`

Builds synthetic netlists from the real CSV, **damages them in specific ways**,
and asserts the checker notices: two pins transposed, a pin missing, a pin that
should not exist, an NC pin wired to something. A checker that only passes good
input is worth nothing, so most of these tests are failures it must catch.

## `test_rominfo.py`

```sh
python3 tools/test_rominfo.py
```

37 checks, 0 failures. `[MEASURED: 2026-09-15]`

Same convention as the testbenches in [`../sim/`](../sim/): build known inputs,
assert known outputs, print a count. No framework, no dependencies.

Test 7 exists because the first version of the tool **crashed** on a file that
was not a `.neo` — the header was rejected before the metadata was populated and
the renderer assumed it was there. Writing the failure tests found it
immediately, which is the argument for writing them.
