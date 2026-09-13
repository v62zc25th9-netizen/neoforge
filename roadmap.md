# NeoForge Roadmap

> Understand the cartridge. Simulate the cartridge. Build the cartridge.

NeoForge is being developed incrementally, starting with research and
simulation and progressing toward open-source Neo Geo AES cartridge hardware.

This roadmap is iterative. Technical decisions will change as we learn more
about the AES cartridge architecture and test our assumptions against real
hardware.

---

## Why this order

Three constraints shape the sequence, and it is worth stating them before the
milestone list, because they are what makes this roadmap different from the
obvious one.

**1. There is no dumb AES cartridge — that can display sprites.** On AES the
sprite serializer (PRO-CT0 / NEO-ZMC2) lives inside the cartridge, not on the
motherboard. `[VERIFIED: wiki AES cartridge]`

The unqualified version of that claim drove the original ordering, and it is
wrong. `[ANSWERED IN SIMULATION — 2026-09-06]` The serializer's outputs are
gated by DOTA/DOTB, and the line-buffer clearing path ignores them entirely, so
a cartridge that holds DOTA and DOTB low needs no serializer at all — it simply
cannot draw sprites. See `docs/open-questions.md` Q1.

So the constraint is narrower than it looked: **a text-only development
cartridge is a plain EPROM board plus two grounded pins. A cartridge that runs
games needs the serializer.** Those are now two separate milestones rather than
one.

**2. Nobody has published measured AES bus timing.** Everything available is
derived from schematics. Building hardware to a specification nobody has
verified is how projects spend two years failing intermittently. Measurement is
therefore its own milestone, placed as early as physically possible, and it is
the project's highest-value public output regardless of whether the cart ever
ships. See `docs/prior-art.md` §8.

**3. There is one AES and no spare.** Every hardware phase is ordered to keep
original silicon between our work and the console for as long as possible. The
first physical milestone deliberately reuses an original cartridge board rather
than introducing a new one.

The consequence: **the first cart NeoForge boots on real hardware is a modified
original cartridge, not a NeoForge PCB.** The PCB comes after the electrical
behaviour it must reproduce has been measured on a board known to work.

### Revision, 2026-09-06

Q1's answer changes the back half of this roadmap and the phases below have not
been renumbered — renumbering would break every reference in the commit history
and the docs. Read them with these amendments:

- **Phase 7 (first PCB) no longer depends on Phase 6 (serializer).** A fix-only
  board needs P/S/M/V ROMs, address decoding, and DOTA/DOTB tied low. It is
  buildable without a CPLD, a donor chip, or any custom silicon.
- **Phase 6 moves after Phase 7** in practice, and becomes the step that turns a
  development cartridge into one that can run games.
- **Phase 2 is smaller than written.** See its revised goals below.

What did *not* change, and is now the real critical path: measured bus timing
(Phase 5), 5V tolerance across a 200-pin connector, and the wait-state question
in `docs/open-questions.md` Q3. The logic got easier. The electronics did not.

### Revision, 2026-09-09 — checkbox audit

Phases 1 and 3 had drifted out of date. Corrected above: the hello ROM, the
AES/MVS split document and the banking document are done; `docs/serializer.md`
exists in substance under `sim/README.md`; the connector entry's "wiki images
are drawn reversed" claim is retracted to match `docs/aes-connector.md`.

Unrelated to the audit, one dated claim in `docs/open-questions.md` Q4 and
`docs/prior-art.md` had become false: the AES+ release slipped from 12 November
2026 to **16 September 2027**, which PLAION attribute to a component shortage.
`[VERIFIED: PLAION press release, 2026]`

---

## Phase 0 — Project Foundation

**Status: 🟢 In Progress** · Cost: $0 · Skills: none beyond git

Establish the project, documentation structure, and contribution workflow.

- [x] Create the NeoForge repository
- [x] Establish the evidence convention (`CLAUDE.md`)
- [x] Initial cartridge architecture research notes
- [x] Prior art directory (`docs/prior-art.md`)
- [x] Split licensing per directory: CERN-OHL-S-2.0 hardware, GPL-3.0-or-later
      HDL, MIT software, CC-BY-SA-4.0 docs. See `LICENSE.md`. The HDL choice is
      forced by NeoGeoFPGA-sim's GPL-3.0; NeoChips' GPL-2.0-only is
      incompatible with it and must be used as a component, never derived from.
- [x] Write `contributing.md`
- [x] Fix `docs/cartridge architecture` filename → `docs/cartridge-architecture.md`
      (done in 5bf733a; the checkbox was left stale)
- [ ] Establish issue and milestone structure mirroring this roadmap

**Exit:** a repository credible enough that someone who actually knows this
hardware will engage with it.

---

## Phase 1 — Hello World in Emulation

**Status: 🔵 Next** · Cost: $0 · Skills: C, build tooling · ~1–2 weeks

Prove the software half of the chain end to end before spending a dollar.

- [x] Stand up `dciabrin/ngdevkit` and build `ngdevkit-examples` unmodified
      `[MEASURED: 2026-09-05]` macOS 14.1.1 arm64, Homebrew tap, all 18
      examples built clean; `01-helloworld` runs in GnGeo in AES mode
- [x] Write the NeoForge hello ROM (see `hello-world.md`) — `[MEASURED:
      2026-09-08]` It outgrew the name: `rom/` is a fix-layer test with a
      positive control (a framed window that alternates green and red as
      sprites are toggled), not just text on screen. Boots in GnGeo in AES mode.
- [x] Publish it so other people can run it — release `fixtest-v1`, results
      collected in `rom/RESULTS.md`. Anyone with an AES and any flash cart can
      test most of Q1 with no soldering.
- [x] Exercise the V ROM — `[MEASURED: 2026-09-10]` `rom-sound/` plays one
      ADPCM-A sample from the cartridge V ROM every two seconds. The V ROM was
      512 KB of zeroes in everything we had built, which left one of the
      cartridge's five ROMs completely untested. Unlike the fix-layer test, an
      emulator answers a real question here: whether our V ROM is *correctly
      constructed* — ADPCM-A encoding, sample offsets, the map `vromtool`
      generates. The hardware question — can a board serve V ROM reads — waits
      for Phase 7, when the board doing the serving is ours.
      The sample is synthesised by `sample.py`; no audio file is committed.
- [ ] Run it under GnGeo with GDB attached
- [ ] Run it under MAME — the accuracy reference, not the convenient one
- [ ] Run `neogeodev/NGAcidTests` and record which emulator passes what
- [ ] Document the macOS setup as a reproducible script (see notes below)
- [x] Commit a reproducible build (`make` → ROM, no manual steps) —
      `[MEASURED: 2026-09-10]` `rom/sound-driver.s` supplies the Z80 command
      jump table and links against `nullsound-aes.lib`, which ships with
      ngdevkit. No second checkout, no borrowed binary. `make` works from a
      clean clone with ngdevkit on PATH, and the built ROM boots unchanged in
      GnGeo.

**Exit:** a ROM we wrote, booting in two independent emulators, buildable from
a clean checkout by a stranger.

**macOS setup notes** `[MEASURED: 2026-09-05]` — gotchas hit during the first
real install, worth capturing before they are forgotten:

- Homebrew now refuses third-party taps until `brew trust dciabrin/ngdevkit`.
- Bottles exist for `arm64_sonoma` and `arm64_sequoia`; nothing compiles from
  source on those. Older macOS will build GCC and SDCC locally.
- `sdl2` was removed from homebrew-core and is now an alias for `sdl2-compat`.
  This resolves cleanly and is not a problem, but the deletion notice is alarming.
- The examples need build tooling that bottles do not pull in:
  `make autoconf automake autoconf-archive pkg-config rsync zip imagemagick sox`.
  `make` is what provides `gmake`.
- Build with `gmake`, not `make` — Apple ships GNU Make 3.81 and the build needs 4.x.
- Put brew's python ahead of Apple's: `export PATH=$HOMEBREW_PREFIX/opt/python3/bin:$PATH`.

**Note on what this does and does not prove.** An emulator models the cartridge
we describe to it. Passing here proves the ROM is well-formed. It proves
nothing about the cartridge, the bus, or the serializer. Do not let a green
emulator create false confidence about hardware.

---

## Phase 2 — ROM Analysis & Cartridge Description Tooling

**Status: ⚪ Planned** · Cost: $0 · Skills: C or Python · ~2–4 weeks

Software that pays off in every later phase.

**Revised 2026-09-06 — this phase is smaller than originally written.**
ngdevkit's `romtool.py` (609 lines, LGPL) already carries `Cartridge` and `ROM`
data models and emits MAME, GnGeo **and** NeoSD `.neo` output. That is the
*write* direction of most of what was scoped here. The honest remaining work is
the *read* direction against a model that already exists.

- [x] Read `romtool.py` properly — **done 2026-09-10.**
      `docs/rom-format.md` lays out the `.neo` container from two independent
      implementations (`romtool.py` and `city41/neosdconv`) and records where
      they disagree: `neosdconv` swaps the halves of a P region that is exactly
      2 MB, and `romtool.py` does not. If our reading is right, a homebrew ROM
      with a 2 MB P built by `romtool.py` runs with its banks transposed.
      `[UNVERIFIED]` and cheap to test.
- [x] Test the 2 MB P-ROM meg-swap discrepancy — **done 2026-09-12.** Built two
      synthetic sets with a 2 MB P of two distinguishable megabytes and ran both
      converters. **They disagree**: `neosdconv` swaps, `romtool.py` does not,
      in both the single-file and the `p1`+`p2` case. The P regions differ byte
      for byte. At least one is wrong. It also corrected this roadmap's own
      guess — swapping the split case is *consistent* under a banked-first
      convention, not an inversion. Which tool is right still needs a NeoSD.
      See `docs/rom-format.md`.
- [x] Decide: extend `romtool.py` upstream, or build our own reader —
      **decided 2026-09-12: build ours first, offer it upstream after.**
      Proposing an inspect mode to ngdevkit is a much better conversation with
      a working tool behind it than with a design sketch, and it let us move
      without waiting on anyone's review cycle. Ours is MIT and standalone;
      `romtool.py` is LGPL and part of a toolchain with its own release
      cadence.
- [ ] Offer an inspect mode upstream to ngdevkit, now that one exists.
- [x] `neoforge-rominfo`: ROM set → machine-readable cartridge description —
      **done 2026-09-12.** Reads a `.neo`, a directory or a zip; `--json` for
      machine output; exit 1 on error so it can gate a build. 25 self-tests.
      See `tools/README.md`.
- [x] Identify P/C/S/M/V components and sizes — including which board serves
      each, since PROG and CHA are separate memory systems.
- [ ] Identify cartridge configuration and mapper — needs the family/mapper
      inference from `docs/prom-banking.md`; sizes alone do not determine it.
- [x] Validation — C ROM pairing, pair sizes, header consistency, power-of-two
      sizes, region maxima, and the 2 MB P ambiguity.
- [ ] Document ROM formats and assumptions

Also read `neogeodev/NeoADPCMEx` and `city41/neosdconv` — the latter documents
a competitor's on-card format in working code.

**Priority note.** This phase serves loading *commercial* ROM sets, which is a
Phase 9 concern. It does nothing to help build the fix-only board that Q1 just
unblocked. Worth doing, but not next.

**Revised 2026-09-10 — smaller still.** Nothing that exists reads a ROM set or
parses a `.neo`; both implementations go one way only. So the gap is the *read*
direction and verification — do the C ROMs pair evenly, is P a legal size, does
the layout match a known cartridge family — not construction, which is solved
twice over.

**Exit:**

    neoforge-rominfo game.zip

    Game: Example Game        System: AES/MVS
    P-ROM: 1 MB   C-ROM: 4 MB   S-ROM: 128 KB
    M-ROM: 128 KB V-ROM: 2 MB
    Cartridge: Standard   Mapper: ...

---

## Phase 3 — Connector and Serializer, on Paper

**Status: ⚪ Planned** · Cost: $0 · Skills: reading HDL · runs parallel to Phase 2

Everything that can be learned without hardware, learned before buying any.

- [x] `docs/aes-connector.md` — **done 2026-09-07.** All 200 pins with
      authoritative numbering, cross-checked against three independent sources:
      the wiki images, `aes_cart.v`'s port list, and the AES 3.5 motherboard
      schematic (public domain KiCad, nets machine-extracted). An earlier
      version of this line claimed the wiki's top-face images are "drawn
      reversed" and that this is a trap. **Retracted** — the reversal is real
      but is the ordinary per-face viewing convention, which is the natural way
      to draw a connector. See the retraction in `docs/aes-connector.md`.
- [x] Machine-readable pinout — `docs/data/aes-cartridge-pinout.csv`, including
      which pins the AES 3.5 leaves unconnected. No text or CSV version appears
      to exist upstream; the wiki publishes images only.
- [x] `docs/serializer.md` — **done 2026-09-10.** Both halves of NEO-ZMC2,
      from simulation. `zmc2_dot` (the sprite datapath): bitplane layout, `H` as
      shift direction rather than a separate path, `DOTA`/`DOTB` as opacity
      only. `zmc2_zmc` (the Z80 mapper): four bank windows, programmed by an
      I/O *read* rather than a write, no reset on the registers, and an alias at
      `F800`. `[MEASURED: 2026-09-05, 2026-09-10]` 65 checks across two
      testbenches, 0 failures.
- [ ] Report the `BANKSEL` width bug to NeoGeoFPGA-sim — `wire BANKSEL =
      SDA_U[15:8]` is declared as a scalar, so the eight-bit value truncates to
      one bit and every bank register can only hold 0 or 1. One-line fix; they
      should have it back. See `docs/serializer.md`.
- [ ] Read FusionConverter's CPLD sources — **check its licence first**, which
      `LICENSE.md` still records as unverified.
- [x] Document AES vs. MVS cartridge differences — `docs/why-the-split.md`.
      The mechanism is verified (32 lines in, 10 out; a 40-pin connector
      difference of which the serializer accounts for 22). The *motive* is
      explicitly marked inference, with a "what would change our minds" section.
- [x] Document banking, address decoding, and known cartridge configurations —
      `docs/prom-banking.md`. The `$200000`–`$2FFFFF` banking window, PROGBK1's
      implementation in three 74-series parts, the cartridge families, and the
      27C322 V ROM trap.
- [ ] Catalogue AES hardware revisions and identify which one the maintainer
      owns — **unblocking soon.** A Fatal Fury Special AES cart is in transit.
      The wiki's AES entry for that title lists PROG board, CHA board and
      protection chip as **Unknown** (its MVS counterpart is PROGGSC /
      CHA42G-3B / no protection), so photographing the boards and reading the
      chip markings fills three blanks upstream as well as inventorying the
      Phase 4 donor.
- [ ] **Resolve the serializer decision** — donor chip, NeoChips NEO-ZMC2
      replacement, or own CPLD implementation. The GPL-2.0 version question we
      raised upstream was closed without an answer, so NeoChips stays usable as
      a bought-or-built **component** and unusable as a source. See
      `LICENSE.md`. Not blocking: a fix-only cart needs no serializer at all,
      and `docs/serializer.md` characterises both halves from the GPL-3.0
      lineage.

**Exit:** we can explain, from sources, exactly what a cartridge must do
electrically for the AES to boot it.

---

## Phase 4 — First Hardware: Donor Development Cartridge

**Status: ⚪ Planned** · Cost: ~$250–450 · Skills: careful desoldering · the
first real difficulty spike

Get NeoForge code running on the actual AES, using an original cartridge board
so that the serializer, the connector, the level handling and the shell all come
for free.

The technique is established: desolder the mask ROMs from a donor AES cart and
fit EPROMs in their place. Documented with photographs on working NEO-AEG
PROGGS / NEO-AEG CHA42G-4 boards. `[VERIFIED: yAronet dev cart thread]`

- [ ] Acquire tools: fine solder, flux, wick, a decent temperature-controlled
      iron, and hot air or a desoldering gun. **The fat iron will destroy a
      board — replace it before touching a donor cart.**
- [ ] Practice desoldering multi-pin ICs on scrap boards until it is boring
- [ ] Acquire an EPROM programmer with **42-pin** support (M27C800 / M27C160
      class parts) plus adapters
- [ ] Acquire a donor AES cartridge — a common, low-value, ideally already
      damaged title. Fatal Fury Special acquired 2026-09-09, in transit. Open
      and document before deciding whether it becomes the donor; it may be
      worth more as a documented reference than as a sacrifice.
- [ ] **Document the donor board fully before modifying it** — and do this
      first, because it is free and it upgrades evidence elsewhere. Photos, full
      chip list, trace the serializer. **Read the mask ROM part numbers**: the
      speed grade is in the part number, which turns the access-time envelope in
      `docs/hardware-constraints.md` from a simulation model's annotation into a
      verified measurement, with a magnifying glass and no risk. The wiki also
      lists PROG board, CHA board and protection chip as *Unknown* for the AES
      release of Fatal Fury Special, so this fills three blanks upstream.
- [ ] Desolder mask ROMs, fit pin receptacles (lower profile than sockets, so
      the board still fits the shell)
- [ ] Burn the Phase 1 hello ROM and boot it

**Exit: NeoForge code running on the maintainer's AES.** This is the milestone
that converts the project from documentation into engineering.

**Risk management.** Do not power an untested board in the AES. Continuity-check
every reworked pin. The donor board is the safety mechanism — it is a design
SNK already validated, and staying inside it for as long as possible is the
whole reason this phase precedes any PCB work.

---

## Phase 5 — Measure the Bus

**Status: ⚪ Planned** · Cost: ~$100–400 (instrument dependent) · the project's
first original contribution

With a known-good cartridge in hand, capture what the AES actually does.

### Revision, 2026-09-11 — and a same-day correction

**First revision, retained because the reasoning is still half right.** The list
below assumes observing a working cartridge is enough to answer Q3. Watching a
working cart measures *that ROM's* access time; it says nothing about how much
slower a cartridge could be. `docs/measurement-cart.md` designs an instrument
that finds the edge by making the console fail on purpose, and resolves the
bootstrap problem — you cannot read a result from a machine that just crashed —
by splitting the address space so only a probe region is swept.

**Corrected the same day: we do not need the limit.** The ROM models in
NeoGeoFPGA-sim are annotated with the original access times — P at **120 ns**,
C at 250 ns, S at 200 ns, M and V at 100 ns. `[VERIFIED: NeoGeoFPGA-sim
Cartridge/ROMs/*.v, as the model's annotations]` If SNK shipped 120 ns P ROMs
and every cartridge ever made works, 120 ns is **sufficient by demonstration**.
A board designer needs a sufficient condition, not an edge. Design to 100 ns.

So the path is: design inside the envelope, verify the envelope by reading mask
ROM part numbers off a real board, and cross-check in simulation — which is free,
and which `docs/measurement-cart.md` §10 now describes. The measurement cart is
demoted from prerequisite to optional contribution, and becomes the contingency
if a design cannot make 120 ns.

Two findings from this work that stand regardless:

- **`ROMWAIT`, `PWAIT0` and `PWAIT1` are cartridge outputs.** The cart owns the
  coarse knob and can sweep wait states directly.
  `[VERIFIED: docs/data/aes-cartridge-pinout.csv]`
- **No AES interposer appears to exist.** A cart that measures itself needs
  none.

And one risk worth stating in the roadmap rather than only in the design doc:
**a slow read cannot damage anything** — the 68k just reads garbage and hangs.
**Bus contention can**, and that risk comes from building a 200-pin board at
all, not from any experiment run on it.

- [ ] Acquire a logic analyzer with real bandwidth. The 68k runs ~12 MHz and
      the C-ROM side is faster; **$10 24 MHz clones are not adequate** and will
      produce confidently wrong data
- [ ] Instrument the donor cart: address, data, control, and serializer lines
- [ ] Capture reset and boot sequence
- [ ] Capture normal read cycles and measure setup, hold and access times
- [ ] **Measure the console-side input thresholds.** Cheap, and it settles the
      question `docs/hardware-constraints.md` flags as our real 5V unknown:
      driving a 5V system from 3.3V logic works only if every receiver is
      TTL-threshold (2.0 V), and the receivers here are undocumented SNK ASICs.
      Measurable on a working cartridge without building anything. If any input
      is plain-CMOS-threshold (3.7 V), direct 3.3V drive fails on that pin —
      and it will fail marginally, which is the worst way.
- [ ] Capture serializer transactions against LSPC clocking
- [ ] Publish captures and analysis under `docs/measured/` with `[MEASURED]`
      markers and raw files
- [ ] Build a Verilog testbench that reproduces the captured behaviour
- [ ] **Build the whole-console simulation harness** — **lints clean
      2026-09-12**, does not run yet. `sim/harness/` holds the fx68k shim, the
      patch set and a Makefile. The whole system model elaborates under
      Verilator 5 with `--timing` and a cycle-accurate 68000 in place of the
      VHDL core, so no unknown blocker remains. What is left: a top-level
      testbench, ROM data from nullbios and our own ROMs, and — the real risk —
      verifying fx68k's clock-phase alignment against `CLK_68KCLK`, since the
      wait-state logic is keyed to it and wrong alignment yields a machine that
      almost works. See `sim/harness/README.md`.
- [ ] **Build the measurement cartridge** — see `docs/measurement-cart.md`.
      Answers Q3, tests the level-translation approach Phase 7 depends on, and
      settles the ASIC input-threshold question, on a board with no memory, no
      serializer and no audio. Design on paper; nothing built.

**Exit:** published, sourced, measured AES cartridge bus timing — which does not
currently exist publicly, benefits MiSTer and the emulator projects as much as
it benefits NeoForge, and is achievable without designing a single PCB.

If the project stalled permanently after this phase, it would still have been
worth doing.

---

## Phase 6 — Serializer in Programmable Logic

**Status: ⚪ Planned — now follows Phase 7, see Revision above** · Cost: ~$100–200 · Skills: HDL, CPLD toolchain · the
hard problem

Replace the donor cart's SNK serializer with logic we can publish.

- [ ] Select a **5V-tolerant** CPLD. This constraint eliminates most modern
      parts and drives the entire electrical design; settle it early.
      `docs/hardware-constraints.md` has the analysis: the logic is tiny, so
      the part is picked for voltage and availability, and a 5V CPLD stays
      attractive for small boards precisely because it deletes the level
      translation problem entirely.
- [ ] Implement the serializer, derived from the FusionConverter and
      NeoGeoFPGA-sim references, with attribution and license compatibility
      checked
- [ ] Validate in simulation against the Phase 5 captures **before** synthesis
- [ ] Remove the PRO-CT0 / NEO-ZMC2 from the donor cart, socket the CPLD in
- [ ] Boot

**Exit:** an AES cartridge booting with no SNK custom silicon in it. This is the
technical core of the project; everything after it is engineering rather than
research.

**Fallback:** if the CPLD path stalls, `neogeodev/NeoChips` NEO-ZMC2 is a
published replacement that can be bought or built. Using it is not a failure —
it unblocks Phases 7–9 while the serializer work continues in parallel.

---

## Phase 7 — NeoForge Cartridge v0.1

**Status: ⚪ Planned — no longer blocked by Phase 6** · Cost: ~$200–500 per revision · Skills: KiCad, SMD assembly

Only now does a PCB make sense: every function on it has already been proven on
a board that works.

- [ ] Design the edge connector and mechanical fit (verify against a real shell).
      **Started 2026-09-13:** `hardware/lib/neoforge-aes.kicad_sym` has KiCad
      symbols for both connectors, generated from the pinout CSV, with pin
      directions from the cartridge's point of view so ERC can catch bus
      contention. The footprint — pad geometry, pitch, mechanical outline —
      needs measuring off a real cartridge and waits for the teardown.
- [ ] Level translation across 100+ 5V signals — the failure mode that has sunk
      cheap multicarts
- [ ] EPROM/flash footprints, CPLD serializer, address decoding
- [ ] Manufacture, assemble, bring up **outside** the AES first
- [ ] Boot the hello ROM
- [ ] Publish design files under an open hardware license

**Deliverable: NeoForge Cartridge v0.1** — a single-game, reproducible,
open-hardware AES development cartridge.

**Decided 2026-09-12: this is a stepping stone, not a product.** It will be
built, learned from, and published as design files — but it is not going to be
packaged, supported, or maintained as a thing other people are invited to buy or
rely on. The goal is the flash cart, and finishing an intermediate product would
cost months of documentation and support that the actual goal needs more.

Stated because it changes how much polish Phase 7 gets, and because the opposite
choice is defensible: a single-game dev cart is genuinely useful to Neo Geo
homebrew developers, would arrive far sooner than the loader, and might have
brought in the contributors and testers the loader will eventually want. **The
risk we are accepting is arriving at the flash cart with no community around the
project.** If that starts to look like the binding constraint, revisit this.

Budget for three board revisions. First-spin success on a 200-pin 5V edge
connector board would be luck, not skill.

---

## Phase 8 — FPGA Cartridge (v0.2)

**Status: ⚪ Planned**

Replace fixed logic with an FPGA. Now a scale-up of proven work, not a redesign.

- [ ] Select FPGA platform. `docs/hardware-constraints.md` now carries the
      numbers this decision needs: 90 MB worst case, split ~24 MB on PROG and
      ~65 MB on CHA across two physically separate boards with different
      consumers running concurrently — which is very probably why Terraonion
      used two FPGAs. The part is chosen for I/O count, memory interface and
      availability, **not logic capacity**; what we simulated is tiny. The
      binding constraint is 5V.
- [ ] Port the serializer; add programmable address decoding and banking
- [ ] External RAM and flash interfaces
- [ ] Validate against the Phase 3 simulator and Phase 5 captures
- [ ] Boot a full commercial-scale ROM from the maintainer's own dump

---

## Phase 9 — SD Card Loader (v0.3)

**Status: ⚪ Planned**

- [ ] Microcontroller selection, SD and filesystem support
- [ ] ROM transfer into cartridge memory; reset/load sequencing
- [ ] Open, documented on-card ROM format — deliberately specified in public,
      unlike NeoSD's and Darksoft's
- [ ] Basic game selection UI, error handling, loading reliability

**Deliverable: NeoForge Flash Cartridge v0.3.**

---

## Phase 10 — Multi-Game Platform

**Status: ⚪ Planned**

Game database and metadata, improved menu, save RAM, automatic cartridge
configuration, larger ROM support, additional mappers, homebrew support,
firmware update, USB debug interface.

Protection handling decision point: precompute offline (cheaper, needs a
conversion step) versus emulate live (harder, unmodified ROM sets work).

**Corrected 2026-09-12.** This previously said "emulate live *like NeoSD*". That
is wrong: **NeoSD precomputes offline.** The `.neo` header carries no mapper,
family, protection or encryption field, and `bodgit/terraonion`'s reimplementation
of the conversion carries 56 per-game readers plus generic CMC42/CMC50/PVC/PCM2/
K2K2 paths that decrypt and descramble on the PC. The cartridge receives
normalised data. See `docs/rom-format.md`.

The practical consequence is encouraging: the cheaper path is what the market
leader ships, and the cost it carries — a mandatory conversion step, so a plain
MAME zip will not do — is one the market evidently accepts.

Note this covers encryption and scrambling only. **Bank switching is live
cartridge behaviour regardless** and must still be implemented; so, possibly,
are protection chips' read-side registers.

---

## Phase 11 — Compatibility

**Status: ⚪ Planned**

- [ ] Test across AES revisions: Japanese, US, European
- [ ] Publish an open AES compatibility matrix
- [ ] Resolve board-revision-specific timing differences

Justification: a professionally engineered two-FPGA commercial cart still showed
board-revision-specific failures in the field. `[ANECDOTAL: arcade-museum
thread]` One console proves nothing.

---

## Phase 12 — Beta Program

**Status: ⚪ Planned**

Externally testable hardware, structured reporting, documented build process
and BOM, and a firmware update path — so testers can be helped rather than
merely thanked.

---

## Honest timeline

Evenings-and-weekends pace, one maintainer, learning several disciplines:

| Milestone | Realistic |
|---|---|
| Phases 0–3 (all software and documentation) | 1–3 months |
| Phase 4 — code on real AES | ~6 months |
| Phase 5 — published measurements | ~8 months |
| Phase 6 — open serializer booting | ~12–18 months |
| Phase 7 — v0.1 PCB | ~18–24 months |
| Phase 9 — working flash cart | 2–3 years |

This is not discouragement. It is why the roadmap is built so that Phases 1, 2,
3 and 5 each produce something the community can use even if the project never
reaches Phase 9 — and why the highest-value output (measured bus timing) is
reachable in under a year with no PCB design skill required.
