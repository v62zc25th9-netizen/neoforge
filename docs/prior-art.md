# Prior Art Directory

A catalogue of existing work NeoForge should read, credit, and avoid
duplicating — plus an explicit list of what does *not* exist, which is where
this project's contribution has to come from.

Entries follow the evidence convention in `CLAUDE.md`. A `[VERIFIED]` marker
here means the listing itself was confirmed (repo exists, license read,
description read), not that every claim the project makes about itself is true.

**Standing rule:** before starting any milestone, re-read the relevant section
of this file. The most common failure mode for a project like this one is
spending three months rebuilding something that was published in 2016.

---

## 1. Primary documentation

| Source | What it is | Why it matters |
|---|---|---|
| [NeoGeo Development Wiki](https://wiki.neogeodev.org) | The authoritative technical reference, hosted by Furrtek. Pinouts, chip descriptions, memory maps, cartridge architecture. | The single most important source for this project. Treat any conflicting third-party document as wrong until proven otherwise. `[VERIFIED: used throughout docs/cartridge architecture]` |
| [arcade-collector.com AES PCB scans](http://www.arcade-collector.com/neogeo.php) | Photographic database of AES PROG and CHA boards. | Shows how real AES carts are actually populated — which serializer, which ROM footprints, which board revisions. Ground truth for the donor-cart path. `[VERIFIED: index page reachable]` |
| [Board-Folk/NeoGeoAES-3.5](https://github.com/Board-Folk/NeoGeoAES-3.5) | Schematics and PCB for the AES 3.5 motherboard. | The console side of the connector. Needed to understand what the cart is actually being driven by, including loading and termination. `[UNVERIFIED: repo listed in search results, contents not yet reviewed]` |
| [NeoGeo AES 3-5 reproduction main PCB (PCBWay)](https://www.pcbway.com/project/shareproject/NeoGeo_AES_3_5_reproduction_main_PCB_179da741.html) | A shared reproduction of the AES mainboard. | Secondary cross-check on the above. `[UNVERIFIED]` |

**Documentation trap already identified:** published pinouts have /ROMOE and
4MB swapped, an error originating in SNK's official schematics. See
`docs/cartridge-architecture.md` §3.

---

## 2. Open-source HDL and chip implementations

This is the section that matters most. The sprite serializer is NeoForge's
first hard requirement, and it has already been implemented openly more than
once.

| Project | What it is | Relevance |
|---|---|---|
| [neogeodev/NeoChips](https://github.com/neogeodev/NeoChips) | "Replacement chips for NeoGeo systems." Contains folders for NEO-244, NEO-257, NEO-273, NEO-BUF, NEO-G0, **NEO-ZMC2**, PCM, UNI64. GPL-2.0. Sold assembled and documented for DIY with schematics and CPLD programming instructions. | **Highest-value single entry in this file.** A NEO-ZMC2 replacement in programmable logic is precisely the part NeoForge needs and does not have. Buying or building one converts the project's hardest open question into a purchase order. `[VERIFIED: repo page, folder list, GPL-2.0 license]` |
| [neogeodev/FusionConverter](https://github.com/neogeodev/FusionConverter) | Design files for the open-hardware MVS→AES converter. Verilog. | A working serializer implementation in exactly NeoForge's context: taking a cartridge that lacks a serializer and making an AES accept it. Read before writing any HDL. `[VERIFIED: repo exists, Verilog, description]` |
| [neogeodev/NeoGeoFPGA-sim](https://github.com/neogeodev/NeoGeoFPGA-sim) | Simulation-only NeoGeo hardware definition in Verilog. `neo_zmc2.v` (largely by Kyuusaku) and `zmc2_dot.v` are the serializer core. | The reference model to validate our own implementation against. Simulation-only means it is a specification, not a synthesizable design — that gap is work NeoForge can do. `[VERIFIED: repo exists, Verilog]` |
| [neogeodev/SNKVerilog](https://github.com/neogeodev/SNKVerilog) | Verilog definitions of custom SNK chips, for repairs and preservation. | Overlaps NeoChips and NeoGeoFPGA-sim; worth diffing all three before trusting any one. `[VERIFIED: repo listing]` |
| [furrtek/Neogeo_MiSTer](https://github.com/MiSTer-devel/NeoGeo_MiSTer) | Full FPGA core for the whole system. | Not a cartridge project, but the most complete open model of NeoGeo behaviour in existence. Where the wiki is silent, the core is the answer. `[UNVERIFIED: URL not re-checked this pass]` |
| [neogeodev/YM2610](https://github.com/neogeodev/YM2610) | Sound chip reverse-engineering effort, Verilog. | Not on the cartridge. Listed so nobody wastes time on it thinking it is. `[VERIFIED: repo listing]` |
| [neogeodev/SVGPinout](https://github.com/neogeodev/SVGPinout) | SVG pinout generator and pinout definitions for SNK chips. Python. | Free, correct pinout diagrams for our own documentation. Use it rather than drawing pinouts by hand. `[VERIFIED: repo listing]` |

---

## 3. Open hardware

| Project | What it is | Relevance |
|---|---|---|
| [neogeodev/NeoMemCard2](https://github.com/neogeodev/NeoMemCard2) | Open-hardware NeoGeo memory card. GPL-3.0. | Closest existing example of open NeoGeo-bus hardware done properly. Study its licensing, its build documentation and its level-shifting approach before designing anything. `[VERIFIED: repo listing, GPL-3.0]` |
| [NEO-JAMMA/Neo-Geo_MVS_Projects](https://github.com/NEO-JAMMA/Neo-Geo_MVS_Projects) | Cyril Venditti's collection: battery holder, SNES→NeoGeo controller adapter, supergun, GBS-Control design. GPL-3.0. | Peripheral rather than cartridge work, but an example of a maintained open NeoGeo hardware collection. `[VERIFIED: via RetroRGB article]` |
| [fliperama86/neopico-hd](https://github.com/fliperama86/neopico-hd) | Digital video and audio capture with HDMI output for NeoGeo MVS, using a Raspberry Pi Pico 2. | Not a cartridge, but direct evidence that an RP2350-class microcontroller can be clocked onto NeoGeo digital buses in real time. Relevant to any future "cheap MCU instead of FPGA" argument. `[VERIFIED: repo exists, described in RetroRGB coverage]` |
| `fliperama86/neopico-cart` | Appears in search indexes; the repository currently returns 404. | Possibly renamed, made private, or withdrawn. Worth asking the author about — a Pico-based NeoGeo cart is squarely NeoForge's problem space. `[UNVERIFIED: 404 as of 2026-09-05]` |

---

## 4. Homebrew toolchains and test software

Everything NeoForge needs for its "hello world" milestone already exists. We
should write a ROM with these tools, not write tools.

| Project | What it is | Relevance |
|---|---|---|
| [dciabrin/ngdevkit](https://github.com/dciabrin/ngdevkit) | Open-source NeoGeo dev kit: m68k toolchain (GCC 15.3 + newlib 4.0), SDCC 4.4 for the Z80, C headers, ROM helpers, graphics tools, an open BIOS replacement, GDB source-level debugging, and a modified GnGeo with remote debugging. LGPL-3.0+. Targets **AES or MVS**. | The default answer for the hello-world ROM. Actively maintained — presented at FOSDEM 2026. `[VERIFIED: repo README]` |
| [dciabrin/ngdevkit-examples](https://github.com/dciabrin/ngdevkit-examples) | Homebrew ROMs built with ngdevkit. | Working code to build and boot on day one, before writing anything original. `[VERIFIED: repo listing]` |
| [dciabrin/ngdevkit-toolchain](https://github.com/dciabrin/ngdevkit-toolchain) | The prebuilt toolchain component. | Saves a source build of GCC. `[VERIFIED: repo listing]` |
| [neogeodev/NGAcidTests](https://github.com/neogeodev/NGAcidTests) | NeoGeo accuracy tests, assembly. Folders: LagTest, MemEdit, SpriteTest, VideoDump. **Unlicense** (public domain). | The emulator-validation milestone in one repo. Establishes which emulator we can trust before we trust it about hardware. Public domain means we can vendor and extend freely. `[VERIFIED: repo listing, license]` |
| [neogeodev/neopenbios](https://github.com/neogeodev/neopenbios) | Open-source BIOS for the NeoGeo, assembly. | Matters more than it looks: a cart that boots depends on BIOS behaviour, and an open BIOS is a readable specification of what the BIOS expects a cart to provide. `[VERIFIED: repo listing]` |
| [neogeodev/GFXCodec](https://github.com/neogeodev/GFXCodec) | Tile and pixel conversion for NeoGeo graphics. C. | Needed to produce C-ROM data, which is what the serializer serializes. `[VERIFIED: repo listing]` |
| [neogeodev/NeoADPCMEx](https://github.com/neogeodev/NeoADPCMEx) | GUI tool for extracting ADPCM samples from V ROMs. Python. | Prior art for the ROM-analysis tooling in roadmap Phase 2. `[VERIFIED: repo listing]` |
| [neogeodev/IDANeoGeo](https://github.com/neogeodev/IDANeoGeo) | NeoGeo binary loader and helper for IDA. Python. | Useful if we ever need to read a commercial cart's behaviour to understand a mapper. `[VERIFIED: repo listing]` |
| [neogeodev/mslug-disasm](https://github.com/neogeodev/mslug-disasm) | Metal Slug disassembly. | A worked example of what a real cart's software expects from its hardware. `[VERIFIED: repo listing]` |
| [city41/neosdconv](https://github.com/city41/neosdconv) | Converts homebrew NeoGeo ROMs into TerraOnion's NeoSD `.neo` format. | Documents a competitor's cartridge file format in working code. Directly informative for NeoForge's own on-card format decision. `[UNVERIFIED: found via search, contents not reviewed]` |

---

## 5. Emulators as reference implementations

| Emulator | Relevance |
|---|---|
| **MAME** (`neogeo.cpp` / `neogeo.c` driver) | The accuracy reference. Its chip notes encode protection and decryption algorithms that exist nowhere else in readable form. When the wiki and a forum disagree, MAME's source is the tiebreaker. `[VERIFIED: cited in docs/cartridge architecture]` |
| **GnGeo (ngdevkit fork)** | Fast iteration with GDB remote debugging attached. The development loop, not the accuracy authority. `[VERIFIED: ngdevkit README]` |
| **NeoGeo MiSTer core** | An FPGA implementation, so it models timing in a way software emulators do not. The closest thing to hardware that is not hardware. `[UNVERIFIED]` |

The distinction matters: **an emulator agreeing with us proves the ROM is
valid, not that the cartridge is.** Emulators model the cartridge we tell them
about. They cannot validate bus timing, drive strength, or the serializer.

---

## 6. Commercial flash cartridges

These are the benchmark. NeoForge is not first; it is open.

| Product | What is known | Relevance |
|---|---|---|
| **Terraonion NeoSD / NeoSD Pro** (MVS and AES versions) | 768 MB flash, ARM Cortex-M4 @ 168 MHz, 1 MB flash, 128 MB RAM, **two Lattice XP2 FPGAs**. Advertises running unpatched games by emulating original cartridge protections rather than pre-decrypting. | The two-FPGA split maps onto PROG/CHA, which is a strong hint about the right architecture. Also the compatibility bar the community will measure NeoForge against. `[VERIFIED: Terraonion product pages]` |
| **Darksoft multi / MultiAES** (MVS and AES) | Different ROM file format from NeoSD. | Second data point on cart file formats and on what "acceptable compatibility" looks like. `[VERIFIED: multiple community sources]` |
| Generic "161-in-1" style multicarts | Community reports a persistent 3V3-vs-5V flash issue in current revisions. | A worked example of the electrical mistake NeoForge must not make. `[ANECDOTAL: community sources]` |

**Field report worth heeding:** NeoSD MVS was reported to be picky about
motherboard revision — corruption and resets on NEO-MVH boards while working on
MVS-1A/1B/1C. `[ANECDOTAL: arcade-museum forum thread]` Whatever the true
cause, a professionally engineered cart with two FPGAs still had
board-revision-specific failures. Testing on one machine proves almost nothing.

---

## 7. Community knowledge bases

Much of what is actually known about this hardware was never written down
formally. These are where to ask, and where to search before asking.

- **[Arcade-Projects Forums](https://www.arcade-projects.com)** — active
  hardware modification and repair community; the Fusion converter build
  threads and repro cart discussions live here.
- **[NeoGeo.com / Neo-Geo forums](https://www.neo-geo.com)** — the long-running
  community hub.
- **yAronet NeoGeo development topics** — French-language dev community. The
  [development cartridge thread](https://www.yaronet.com/topics/171618-development-cartridge-for-neo-geo-aes-mvs)
  documents the donor-cart-plus-EPROM approach with photos of working AES dev
  carts on NEO-AEG PROGGS / NEO-AEG CHA42G-4 boards. `[VERIFIED: thread read]`
- **[RetroRGB](https://retrorgb.com)** — tracks open-source NeoGeo projects as
  they appear; useful for staying current. `[VERIFIED: article read]`
- **Furrtek's site and SiliconPr0n die shots** — decapped SNK silicon. The
  bottom of the evidence stack when nothing else answers a question.

**Historical note:** PRO-CT0's logic was reverse-engineered and published to
the dev wiki by Calpis, which is what made non-donor converters possible in the
first place. `[ANECDOTAL: AssemblerGames thread]` NeoForge exists downstream of
that work.

---

## 8. What does not exist

The point of this directory. Everything above is either closed, partial, or
adjacent. The gaps below are NeoForge's actual contribution — and each one is
worth more to the community than a marginally cheaper flash cart.

1. **An open, reproducible AES cartridge PCB.** Donor-cart conversions and
   closed commercial carts exist. A published board that anyone can order and
   populate does not. `[UNVERIFIED: absence of evidence after one search pass —
   re-check before claiming this publicly]`

2. **Synthesizable, validated serializer HDL packaged for cartridge use.**
   NeoGeoFPGA-sim is simulation-only. FusionConverter targets a converter, not
   a cart. NeoChips NEO-ZMC2 is a chip replacement, not a cartridge subsystem.
   Nobody has published "here is the serializer, here is the testbench, here is
   the proof it matches hardware."

3. **Measured AES bus timing.** Everything public is derived from schematics
   and datasheets. There is no published capture of what an actual AES does on
   its cartridge connector, cycle by cycle. **This is the highest-value thing
   NeoForge can produce**, it requires no PCB design, and it makes every
   downstream project — including MiSTer and the emulators — better.

4. **An AES revision compatibility matrix.** The NeoSD field reports show
   board-revision sensitivity is real, and there is no shared dataset of it.

5. **An open on-card ROM format.** NeoSD and Darksoft each have their own,
   both undocumented by the vendor. `neosdconv` reverse-engineered one.

6. **A written path from homebrew source to real AES hardware.** The knowledge
   is scattered across a French forum thread, a wiki, and three GitHub repos.
   Writing it down is a weekend of work and it is the on-ramp for every future
   contributor to this project.

---

## Maintenance

Add an entry the moment a project is discovered, even if it is only skimmed —
an `[UNVERIFIED]` line is more useful than a missing one. Promote it to
`[VERIFIED]` only after actually reading the repository.

Last full pass: 2026-09-05.
