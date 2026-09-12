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

## `test_rominfo.py`

```sh
python3 tools/test_rominfo.py
```

25 checks, 0 failures. `[MEASURED: 2026-09-12]`

Same convention as the testbenches in [`../sim/`](../sim/): build known inputs,
assert known outputs, print a count. No framework, no dependencies.

Test 7 exists because the first version of the tool **crashed** on a file that
was not a `.neo` — the header was rejected before the metadata was populated and
the renderer assumed it was there. Writing the failure tests found it
immediately, which is the argument for writing them.
