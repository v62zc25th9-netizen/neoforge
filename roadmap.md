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
- [ ] Write the NeoForge hello ROM (see `hello-world.md`)
- [ ] Run it under GnGeo with GDB attached
- [ ] Run it under MAME — the accuracy reference, not the convenient one
- [ ] Run `neogeodev/NGAcidTests` and record which emulator passes what
- [ ] Document the macOS setup as a reproducible script (see notes below)
- [ ] Commit a reproducible build (`make` → ROM, no manual steps)

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

- [ ] Read `romtool.py` properly and decide: extend it upstream with an inspect
      mode, or build a reader that reuses its model. Upstreaming is probably
      better for everyone and costs us less.
- [ ] `neoforge-rominfo`: ROM set → machine-readable cartridge description
- [ ] Identify P/C/S/M/V components and sizes
- [ ] Identify cartridge configuration and mapper
- [ ] Validation and test-ROM support
- [ ] Document ROM formats and assumptions

Also read `neogeodev/NeoADPCMEx` and `city41/neosdconv` — the latter documents
a competitor's on-card format in working code.

**Priority note.** This phase serves loading *commercial* ROM sets, which is a
Phase 9 concern. It does nothing to help build the fix-only board that Q1 just
unblocked. Worth doing, but not next.

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
      schematic (public domain KiCad, nets machine-extracted). Found that the
      wiki's *top-face* images are drawn reversed relative to real pin
      numbering — a trap for anyone transcribing them, and not stated upstream.
- [x] Machine-readable pinout — `docs/data/aes-cartridge-pinout.csv`, including
      which pins the AES 3.5 leaves unconnected. No text or CSV version appears
      to exist upstream; the wiki publishes images only.
- [ ] `docs/serializer.md`: how the serializer actually works, derived from
      `neo_zmc2.v` / `zmc2_dot.v` and the FusionConverter CPLD sources
- [ ] Document AES vs. MVS cartridge differences (started)
- [ ] Document banking, address decoding, and known cartridge configurations
- [ ] Catalogue AES hardware revisions and identify which one the maintainer owns
- [ ] **Resolve the serializer decision** — donor chip, NeoChips NEO-ZMC2
      replacement, or own CPLD implementation

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
      damaged title
- [ ] Document the donor board fully before modifying it: photos, chip list,
      trace the serializer
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

- [ ] Acquire a logic analyzer with real bandwidth. The 68k runs ~12 MHz and
      the C-ROM side is faster; **$10 24 MHz clones are not adequate** and will
      produce confidently wrong data
- [ ] Instrument the donor cart: address, data, control, and serializer lines
- [ ] Capture reset and boot sequence
- [ ] Capture normal read cycles and measure setup, hold and access times
- [ ] Capture serializer transactions against LSPC clocking
- [ ] Publish captures and analysis under `docs/measured/` with `[MEASURED]`
      markers and raw files
- [ ] Build a Verilog testbench that reproduces the captured behaviour

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
      parts and drives the entire electrical design; settle it early
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

- [ ] Design the edge connector and mechanical fit (verify against a real shell)
- [ ] Level translation across 100+ 5V signals — the failure mode that has sunk
      cheap multicarts
- [ ] EPROM/flash footprints, CPLD serializer, address decoding
- [ ] Manufacture, assemble, bring up **outside** the AES first
- [ ] Boot the hello ROM
- [ ] Publish design files under an open hardware license

**Deliverable: NeoForge Cartridge v0.1** — a single-game, reproducible,
open-hardware AES development cartridge. Useful to homebrew developers on its
own, independent of the flash cart goal.

Budget for three board revisions. First-spin success on a 200-pin 5V edge
connector board would be luck, not skill.

---

## Phase 8 — FPGA Cartridge (v0.2)

**Status: ⚪ Planned**

Replace fixed logic with an FPGA. Now a scale-up of proven work, not a redesign.

- [ ] Select FPGA platform (study Terraonion's two-FPGA PROG/CHA split)
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

Protection handling decision point: precompute offline (cheaper, incompatible
ROM format) versus emulate live like NeoSD (harder, unpatched games work).

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
