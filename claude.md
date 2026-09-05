# CLAUDE.md

Context for AI assistants working in this repo.

## What this is

NeoForge is an open-source Neo Geo **AES** cartridge research and development
project. Target: an SD-card flash cartridge for original AES hardware.

The maintainer owns an AES. There is no MVS hardware on hand.

## Current state

Documentation only. Five commits, no code, no board files. We are at roadmap
stage 1 (research and documentation).

## Positioning — get this right

Flash carts for the Neo Geo already exist and are sold today:

- **Terraonion NeoSD** — MVS and AES versions, plus NeoSD Pro
- **Darksoft multi** — MVS and AES (MultiAES) versions

The gap NeoForge fills is that **none of them are open**. Do not write or
repeat the claim that no Neo Geo flash cart exists; it is false and it will
cost the project credibility with the people whose help it needs.

## Evidence convention

This is the most important rule in this repo.

Neo Geo hardware is old, poorly documented in mainstream sources, and
surrounded by confident misinformation. Wikipedia states that MVS and AES
carts are incompatible "due to different physical sizes." That is wrong. The
real reason is the sprite serializer chip (see `docs/cartridge-architecture.md`).

Therefore every technical claim in this repo must carry one of these markers:

- `[VERIFIED: <source>]` — backed by wiki.neogeodev.org, a schematic, published
  vendor specs, or reverse-engineered source
- `[ANECDOTAL: <source>]` — forum reports, single-user experience
- `[UNVERIFIED]` — inference, assumption, or reasoning not yet confirmed
- `[MEASURED: <date>]` — our own scope capture or bench test

Do not silently upgrade an `[UNVERIFIED]` claim. If you reason your way to a
conclusion, it stays `[UNVERIFIED]` until something external confirms it.

When asked a hardware question you cannot source, say so rather than answering
from general knowledge. General knowledge about this platform is unreliable.

## The open decision

**How does the first physical cartridge get its sprite serializer?**

On AES the serializer (PRO-CT0 / NEO-ZMC2) lives *in the cartridge*, not on the
board. There is no such thing as a dumb EPROM-only AES cart. Two paths:

1. **Donor chip** — harvest a PRO-CT0 or NEO-ZMC2 from a dead/cheap AES cart.
   Fastest to something that boots. Isolates ROM mapping work from serializer
   risk. Not reproducible by others at scale.
2. **CPLD** — implement the serializer in programmable logic from the start.
   References exist (see below). More work up front, but it de-risks the single
   hardest unknown early and makes the FPGA stage a scale-up rather than a
   redesign.

Current lean: **CPLD**. Not yet decided. The roadmap in `roadmap.md` currently
lists "first physical single-game cartridge" (5) before "FPGA-based cartridge"
(6), which is not achievable in that order on AES. Resolve this before writing
any hardware.

## Reference material

Primary documentation:
- https://wiki.neogeodev.org — the authoritative source, hosted by Furrtek

Open source to read before writing HDL:
- `neogeodev/NeoGeoFPGA-sim` — chipset in Verilog. `neo_zmc2.v` (largely by
  Kyuusaku) and `zmc2_dot.v` are the serializer. Also `neo_c1.v`, `lspc_a2.v`.
- `neogeodev/FusionConverter` — open-hardware MVS-to-AES converter, CPLD
  sources. A working serializer implementation in the exact context we need.
- `furrtek/Neogeo_MiSTer` — full FPGA core
- MAME `neogeo.c` driver — protection and decryption algorithms

Clone these alongside NeoForge so they can be read directly rather than
paraphrased from the wiki.

## Licensing

Repo is currently MIT. MIT is appropriate for HDL, firmware and tooling. It is
a poor fit for PCB files — most open hardware uses CERN-OHL-S or CERN-OHL-W.
Split this before accepting hardware contributions.

## ROMs

This project does not distribute copyrighted ROMs and no ROM data belongs in
this repo. Development uses homebrew, public domain software, or the
maintainer's own legally obtained dumps.
