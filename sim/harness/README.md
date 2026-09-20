# The whole-console harness

Running a NeoForge ROM through a full Verilog model of the Neo Geo, so the
cartridge's access time can be swept with no hardware and no risk.

```sh
make lint     # fetch, patch, and lint the whole system
```

---

## Status: blocked, and we know exactly where `[MEASURED: 2026-09-15]`

Everything assembles. **Neither available simulator can run it**, for two
unrelated reasons, and the combination is what blocks.

| | Compiles fx68k | Handles the model's tri-state buses | Honours `#delay` |
|---|---|---|---|
| **Verilator 5** | yes | **no** | yes |
| **Icarus Verilog** | **no** | yes | yes |

**Verilator** builds the whole thing — console, AES cartridge, cycle-accurate
68000 — into a working binary, and it starts. But the model drives real
tri-state buses (`16'bzzzzzzzzzzzzzzzz`) throughout, and Verilator resolves
those through generated enable logic that oscillates here. The observable
symptom is memory climbing at **~110 MB/s while simulated time barely advances**
— events piling up at a single timestamp — until the process is killed. That is
a zero-delay loop, not a leak, and no flag tunes it away.

**Icarus** is the simulator this model was written for and handles tri-state and
delays natively. It cannot compile fx68k. Making the three `typedef struct`
declarations `packed` clears the original "unpacked structs not supported"
blocker, and then **85 errors** remain, mostly *"Unable to member-select
unresolved wires"* where struct members cross module boundaries. Fundamental,
not cosmetic.

And the model's own CPU, `tg68`, is VHDL, which is where this started.

### One incidental note for anyone building this

Verilator's `--binary` main places the model on the **stack**, and this model is
large. With the usual 8 MB limit the binary dies instantly with no output.
`ulimit -s 262144` before running. Worth knowing before concluding your build is
broken.

## What did get finished, and is reusable

**`mkdata.py`** — builds the 24 `$readmemh` files the model reads, from nullbios
and our own ROMs. The byte-order question in it was settled by **evidence, not
convention**, and that reasoning is the valuable part:

Both `aes-bios.bin` and our own `p1` begin `10 00 00 f3 c0 00 …`. Read as-is
that is SSP `0x100000f3` — a stack pointer that masks to `0x0000f3`, which is
nonsense. Read byte-swapped it is **SSP `0x0010f300`** (the top of the 64 KB
work RAM at `$100000`) and **PC `0x00c04300`** (inside the BIOS at `$C00000`).
Only one of those is a machine that boots.

Both files are therefore stored byte-swapped, and the two ROM models disagree
about whose job it is to undo that — `rom_p1.v` swaps on output, `rom_sp.v` does
not — so the same input bytes need opposite treatment. This is the class of
error that produces a plausible-looking simulation of nothing.

**`neoforge_tb.sv`** — wires `neogeo` to `aes_cart` and watches the 68000 bus.
The model's own `testbench_1` drives an **MVS** cart and leaves the AES one
commented out; this is the AES equivalent, and it did not previously exist.

Its first milestone is deliberately small: catch the reset vector fetch. If SSP
and PC come back as `0010f300` / `00c04300`, then clocks, reset, bus arbitration
and BIOS loading are all confirmed at once, from one result.

### That milestone has now been met - by a different route `[MEASURED: 2026-09-20]`

The harness still does not run. But GnGeo's own 68k monitor, stopped at the
first instruction of our ROM's boot, prints this:

    d3=00000000   d7=00000000   a3=00000000   a7=0010f300   usp=00000000
    c04300 : 46fc 2700  : MOVETSR.W  #$2700

**`a7 = 0010f300`. `PC = c04300`.** The two values `neoforge_tb.sv` was written
to check for, from an independent implementation of the machine, on the first
instruction executed.

That matters for the byte-order work above more than for the harness. The
argument in `mkdata.py` was made from first principles - read as-is the vector
gives SSP `0x100000f3`, which masks to nonsense; read byte-swapped it gives the
top of work RAM and an address inside the BIOS, and only one of those is a
machine that boots. **That reasoning is now corroborated by something that
actually executes.** It was inference; it is now inference plus a witness.

The first instruction is `MOVE #$2700,SR` - supervisor, interrupts masked -
which is what a BIOS reset entry should be, and `R` from there prints
"Selecting Game Vector" and hands off to the cartridge. So the boot path is
sound end to end.

**It does not rescue the harness.** What is confirmed is that our *expectation*
was right, not that our model reaches it. The reason to keep wanting the harness
is timing, which GnGeo does not model.

## A bug we wrote, worth recording

`tg68.sv` asserted fx68k's `pwrUp` from `~pwr_seen & extReset`, with `pwr_seen`
latching whenever *not* in reset — which is already true at time zero, before
the reset button is pressed. So `pwrUp` never fired, fx68k never initialised,
and the 68000 never asserted `/AS`.

**The symptom was a simulation that ran happily and did nothing.** Fixed to
assert during the first reset only. Recorded because "it runs and produces no
output" is indistinguishable from a dozen other faults.

## What we patch, and why

Neither reference is vendored — both are GPL-3.0 and are cloned into
`.reference/` at the repository root. `patch-reference.sh` modifies that working
copy so our changes stay visible and easy to send upstream. It is idempotent.

| # | Change | Kind |
|---|---|---|
| 1 | `System/neo_c1.v` declares `nPORT_ZONE` twice | **upstream bug** |
| 2 | `neogeo.v` declares `SDRAD`/`SDPAD` as `input` while `ym2610` declares them `inout` | **upstream bug** |
| 3 | Route `CLK_24M` to the CPU, which fx68k needs and `tg68` did not | ours |
| 4 | `Cartridge/zmc.v` truncates its bank value to one bit | **upstream bug** |
| 5 | Export `nRESET`, `nROMOEL/U`, `CLK_24M`, `SDRD0/1` from `neogeo` | ours |

Number 1 means the model as shipped **does not compile with Icarus at all**.
Number 5 is not a bug: `neogeo.v`'s port list was written for the MVS testbench
and never exposed the six signals an AES cartridge needs, though all six exist
inside as implicit wires.

`logger_stub.v` is a sixth accommodation. `neogeo.v` instantiates `logger`, and
the upstream logger reads `testbench_1.MC` by hierarchical name — so the system
model cannot elaborate under any top but that one testbench.

## Four ways forward

Roughly in order of how much they cost against how much they buy:

1. **Find a Verilog-2001 68000 core Icarus can compile.** Then Icarus runs
   everything, natively, with correct tri-state and delays. This is the most
   promising and the least invasive, and it is where the next attempt should
   start.
2. **Scope down: drop the console.** Drive the cartridge's P-ROM path from a
   behavioural bus master instead of a real 68000 and a real BIOS. Loses the
   "does it actually boot" fidelity, but it still exercises the cartridge-side
   decode and wait-state logic — which is the part NeoForge has to reproduce,
   and the part Q3 is about. Much the cheapest option.
3. **A mixed-language simulator.** Questa Intel Starter Edition is free and
   handles VHDL, SystemVerilog and timing together, which would run the model
   with its own `tg68` and no shim at all. Probably the shortest path to a
   working simulation, at the cost of a proprietary tool.
4. **Rewrite the model's tri-state buses** as explicit driver/enable logic so
   Verilator can cope. Invasive, touches many files, and makes our patch set
   something nobody would accept upstream.

## What it will and will not prove, when it runs

**Will:** whether our reading of the read cycle is right, whether 120 ns has
margin, where the *model* puts the edge, and whether cartridge-side decode and
wait-state logic behaves as we think.

**Will not:** the real limit. The model is schematic-derived and encodes its
author's understanding, which is part of what we would be testing.

And `nullbios` is not the real BIOS: no cartridge probe, no eye-catcher, no full
Z80 handshake.

## Every input is open, deliberately

No BIOS dump, no commercial ROM — `nullbios` and our own ROMs only. Not just
because of [`contributing.md`](../../contributing.md), but because **a harness
that needs them produces a number nobody can check.**

See [`../../docs/simulation-harness.md`](../../docs/simulation-harness.md).
