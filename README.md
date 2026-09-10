
# NeoForge

### A vibe coded open-source Neo Geo AES cartridge research and development platform.

NeoForge is an open-source project dedicated to understanding, simulating, and
eventually implementing modern cartridge hardware for the original SNK Neo Geo
AES.  

The goal is simple:

> Understand the cartridge. Simulate the cartridge. Build the cartridge.

The project starts with software simulation and documentation before moving
toward physical hardware.

## Project Goals

- Document the Neo Geo AES cartridge interface and architecture
- Build a software model of AES cartridge behavior
- Develop tools for analyzing Neo Geo ROM sets
- Create FPGA-based cartridge implementations
- Develop an SD-card-based flash cartridge
- Support original Neo Geo AES hardware
- Build open-source hardware that others can reproduce and modify

## Development Philosophy

NeoForge is being developed incrementally.

We are intentionally starting with simulation and research rather than
immediately designing a flash cartridge.

### Planned progression

1. AES cartridge research and documentation
2. ROM format and cartridge mapping tools
3. Software cartridge simulator
4. AES bus simulation and testbench
5. First physical single-game cartridge
6. FPGA-based cartridge
7. SD-card loading
8. Multi-game support
9. Compatibility testing across AES revisions
10. Advanced cartridge features

## Current Status

🚧 **Early research / development**

The project is currently in the research and simulation phase. Open source flash cart final destination with intermediary stops at hello world cart.  

## Documentation

- [Roadmap](roadmap.md) — phased plan, exit criteria, cost and skill estimates
- [P ROM banking and cartridge families](docs/prom-banking.md) — the memory
  map, how banking works, and why a board must copy SNK's mapper rather than
  invent one
- [AES cartridge connector](docs/aes-connector.md) — the pinout as text, plus
  [machine-readable CSV](docs/data/aes-cartridge-pinout.csv)
- [Why the serializer moved](docs/why-the-split.md) — why AES puts it in the
  cartridge and MVS on the board, and why we don't think it was anti-piracy
- [Cartridge architecture](docs/cartridge-architecture.md) — MVS vs AES, the
  serializer, connectors, protection hardware
- [Open questions](docs/open-questions.md) — unresolved decisions, what would
  settle each, and what changes either way
- [Prior art directory](docs/prior-art.md) — existing open and commercial work,
  and an explicit list of what does *not* yet exist
- [Fix-layer test ROM](rom/README.md) — a ROM we wrote, with a positive
  control, that tests Q1 on real hardware. Results land in
  [`rom/RESULTS.md`](rom/RESULTS.md)
- [NEO-ZMC2, the cartridge chip](docs/serializer.md) — both halves, from
  simulation: the sprite serializer and the Z80 mapper, what they mean for the
  project, and what is still unknown. How to run it: [sim/README.md](sim/README.md)
- [Hello World cart](hello-world.md) — the first hardware target
- [Contributing](contributing.md) — including the evidence convention

## If you have an AES and a flash cart

There is one thing anyone can do today that would help more than anything else:
**run the [fix-layer test ROM](rom/README.md) and tell us what you see.** It
needs no soldering and no special hardware — NeoSD, Darksoft, anything that
loads a homebrew `.zip`. Grab the release, watch the framed window for four
seconds, and add a line to [`rom/RESULTS.md`](rom/RESULTS.md).

It tests most of [Q1](docs/open-questions.md) — whether an AES cartridge can
skip the sprite serializer entirely — which we have so far only answered by
reading HDL. Nobody has checked it on silicon.

## Contributing

NeoForge is intended to be a community project.

Contributions are welcome in:

- Hardware research
- AES/MVS documentation
- ROM analysis tools
- Simulation
- FPGA/HDL development
- Firmware
- PCB design
- Testing
- Documentation

If you have knowledge of Neo Geo hardware or cartridge development, we'd
especially like to hear from you.

## Copyright and ROMs

NeoForge does not distribute copyrighted Neo Geo game ROMs, ROM fragments,
encrypted blobs or BIOS dumps.

ROMs NeoForge builds from its own sources are a different thing, and we publish
them — the fix-layer test ROM is in the releases, precisely so that people can
run it without building a toolchain first.

Development and testing should otherwise use legally obtained ROM dumps,
homebrew, public-domain software, or other material for which the user has
appropriate rights.

## Disclaimer

NeoForge is an independent open-source project and is not affiliated with,
endorsed by, or sponsored by SNK or any Neo Geo hardware manufacturer.

## License

NeoForge is licensed **per directory** — CERN-OHL-S-2.0 for hardware,
GPL-3.0-or-later for HDL, MIT for software, CC-BY-SA-4.0 for documentation.
See [LICENSE.md](LICENSE.md) for the full table and the reasoning, including
the GPL-2.0/3.0 incompatibility that anyone writing serializer HDL needs to
read first.
