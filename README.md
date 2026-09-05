
# NeoForge

### An open-source Neo Geo AES cartridge research and development platform.

NeoForge is an open-source project dedicated to understanding, simulating, and
eventually implementing modern cartridge hardware for the original SNK Neo Geo
AES.  

We will use "vibe coding" for this project.  

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

NeoForge does not distribute copyrighted Neo Geo game ROMs.

Development and testing should use legally obtained ROM dumps, homebrew,
public-domain software, or other material for which the user has appropriate
rights.

## Disclaimer

NeoForge is an independent open-source project and is not affiliated with,
endorsed by, or sponsored by SNK or any Neo Geo hardware manufacturer.

## License

See [LICENSE](LICENSE) for licensing information.
