# The whole-console harness

Running a NeoForge ROM through a full Verilog model of the Neo Geo, so the
cartridge's access time can be swept with no hardware and no risk.

```sh
make lint     # fetch, patch, and lint the whole system
```

Requires **Verilator 5**. Version 4 ignores `#delay` entirely, which would make
a timing study silently meaningless.

---

## Status, plainly

**It lints. It does not run.** `[MEASURED: 2026-09-12]`

That is real progress and it is not a simulation. The whole system model —
including a cycle-accurate 68000 in place of the VHDL core — elaborates cleanly
under Verilator 5 with `--timing`, which means the pieces fit and no unknown
blocker remains. Bring-up is next, and section *What remains* is honest about
what that involves.

## Why fx68k instead of the model's own CPU

`CPUs/cpu_68k.v` instantiates `tg68`, which is **VHDL**. Icarus Verilog cannot
touch it, so the system as shipped cannot be simulated by anyone without a
mixed-language tool.

`tg68.sv` here has the same module name and the same port list, so
`cpu_68k.v` needs no changes — but inside it is **fx68k**, Jorge Cwik's
cycle-accurate 68000 in SystemVerilog (GPL-3.0).

This is an upgrade rather than a workaround. TG68K is not cycle-exact; fx68k is
microcode-accurate. For a study whose entire subject is bus timing, that
difference is the point, and it removes a caveat we had been carrying.

## What we patch, and why

Neither reference is vendored — both are GPL-3.0 and are cloned into
`.reference/` at the repository root. `patch-reference.sh` modifies that working
copy, so our changes stay visible and easy to send upstream. It is idempotent.

| # | Change | Kind |
|---|---|---|
| 1 | `System/neo_c1.v` declares `nPORT_ZONE` twice — once as an `output`, once as a `wire` | **upstream bug** |
| 2 | `neogeo.v` declares `SDRAD`/`SDPAD` as `input` while `ym2610` declares them `inout` and the cartridge drives them | **upstream bug** |
| 3 | Route `CLK_24M` to the CPU, which fx68k needs and `tg68` did not | ours |
| 4 | `Cartridge/zmc.v` truncates its bank value to one bit | **upstream bug** |

Three genuine bugs. **Number 1 means the model as shipped does not compile with
Icarus Verilog at all**, and number 4 means its M1 bankswitcher can only ever
select bank 0 or 1 — see [`../../docs/serializer.md`](../../docs/serializer.md).
All three are one-liners and all three should go upstream.

`logger_stub.v` is a fourth accommodation but not a patch. `neogeo.v`
instantiates `logger`, and the upstream logger reads `testbench_1.MC` by
hierarchical name — so the system model cannot elaborate under any top but that
one testbench. We substitute an empty module with the same interface.

## What remains

In rough order:

- [ ] **A top-level testbench.** `neogeo` has input ports; something has to
      drive the clocks and reset and hold the ROM contents.
- [ ] **Verify the clock phase alignment.** This is the real risk. fx68k does
      not take a bare 68000 clock — it runs from a 2× clock with `enPhi1` and
      `enPhi2` marking each half of the cycle. `tg68.sv` derives them from
      `CLK_24M`, re-synchronised to `CLK_68KCLK`'s rising edge so they cannot
      drift. **Getting the rate right is easy; getting the alignment right is
      not**, and the cartridge's wait-state logic is keyed to that clock. Wrong
      alignment produces a machine that almost works, which is the worst
      possible failure.
- [ ] **ROM data.** The model reads 24 `$readmemh` text files. Every one has an
      open equivalent — `nullbios` supplies `rom_sp-s2`, `rom_sfix` and
      `rom_l0` (the last via its `zoom-rom.py`), the cartridge side comes from
      [`../../rom/`](../../rom/) and [`../../rom-sound/`](../../rom-sound/), and
      the `raminit_*` files can be zero-filled.
- [ ] **Boot it.** Confirm the model reaches the same screen GnGeo does.
- [ ] **Then sweep** `rom_p1.v`'s `#120` and find where it breaks.

## What it will and will not prove

**Will:** whether our reading of the read cycle is right, whether 120 ns has
margin, where the *model* puts the edge, and whether the cartridge-side decode
and wait-state logic behaves as we think — which is the part NeoForge has to
reproduce.

**Will not:** the real limit. The model is schematic-derived and encodes its
author's understanding, which is part of what we would be testing. Two models
agreeing is not silicon.

And `nullbios` is not the real BIOS: no cartridge probe, no eye-catcher, no full
Z80 handshake. The harness speaks to steady-state bus timing, not to whether a
marginal cartridge survives startup.

## Every input is open, deliberately

No BIOS dump, no commercial ROM. Not only because of
[`contributing.md`](../../contributing.md), but because **a harness that needs
them produces a number nobody can check.** One that runs on `nullbios` and a ROM
in this repository produces one anyone can rerun. Reproducibility is most of the
value of a published measurement.

See [`../../docs/simulation-harness.md`](../../docs/simulation-harness.md) for
the full scoping write-up.
