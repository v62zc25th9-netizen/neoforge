# NeoForge Roadmap

> Understand the cartridge. Simulate the cartridge. Build the cartridge.

NeoForge is being developed incrementally, starting with research and
simulation and progressing toward open-source Neo Geo AES cartridge hardware.

This roadmap is intentionally iterative. Technical decisions may change as
we learn more about the AES cartridge architecture and test our assumptions
against real hardware.

---

## Phase 0 — Project Foundation

**Status: 🟢 In Progress**

Establish the project, development environment, documentation structure, and
contribution workflow.

### Goals

- [x] Create the NeoForge repository
- [ ] Establish project licensing
- [ ] Create contribution guidelines
- [ ] Establish development conventions
- [ ] Create initial project documentation
- [ ] Establish issue and milestone structure
- [ ] Document project scope and goals

### Deliverable

A clean public repository ready for research and collaboration.

---

# Phase 1 — AES Cartridge Research

**Status: 🔵 Next**

Develop a detailed understanding of the Neo Geo AES cartridge interface and
architecture.

### Goals

- [ ] Document the AES cartridge connector
- [ ] Document cartridge address and data buses
- [ ] Document cartridge control signals
- [ ] Document P ROM architecture
- [ ] Document C ROM architecture
- [ ] Document S ROM architecture
- [ ] Document M ROM architecture
- [ ] Document V ROM architecture
- [ ] Document cartridge memory maps
- [ ] Document cartridge address decoding
- [ ] Document cartridge banking mechanisms
- [ ] Document AES vs. MVS cartridge differences
- [ ] Document known cartridge hardware configurations
- [ ] Document known AES hardware revisions
- [ ] Identify existing open-source Neo Geo hardware projects
- [ ] Identify gaps in existing documentation

### Deliverable

A comprehensive, community-maintained technical reference for AES cartridge
hardware.

---

# Phase 2 — ROM Analysis & Tooling

**Status: ⚪ Planned**

Create tools for examining and describing Neo Geo software without requiring
physical hardware.

### Goals

- [ ] Develop NeoForge ROM analysis tool
- [ ] Identify P/C/S/M/V ROM components
- [ ] Parse common Neo Geo ROM formats
- [ ] Identify cartridge configuration
- [ ] Identify memory requirements
- [ ] Generate machine-readable cartridge descriptions
- [ ] Develop ROM validation tools
- [ ] Develop test ROM support
- [ ] Document ROM formats and assumptions

### Deliverable

A command-line toolkit capable of turning a Neo Geo ROM set into a
machine-readable cartridge description.

Example:

    neoforge-rominfo game.zip

    Game: Example Game
    System: AES/MVS

    P-ROM:  1 MB
    C-ROM:  4 MB
    S-ROM: 128 KB
    M-ROM: 128 KB
    V-ROM:  2 MB

    Cartridge: Standard
    Mapper: ...

---

# Phase 3 — Cartridge Simulator

**Status: ⚪ Planned**

Build a software representation of an AES cartridge.

### Goals

- [ ] Create virtual cartridge model
- [ ] Implement P ROM model
- [ ] Implement C ROM model
- [ ] Implement S ROM model
- [ ] Implement M ROM model
- [ ] Implement V ROM model
- [ ] Implement address decoding
- [ ] Implement cartridge memory mapping
- [ ] Implement banking
- [ ] Create automated tests
- [ ] Validate simulator against known cartridge configurations
- [ ] Document simulator architecture

### Deliverable

A software cartridge that can be queried as if it were connected to an AES.

---

# Phase 4 — AES Bus Simulation

**Status: ⚪ Planned**

Model the interaction between an AES system and a cartridge at the bus level.

### Goals

- [ ] Model AES cartridge bus cycles
- [ ] Model address/data transactions
- [ ] Model cartridge control signals
- [ ] Model reset behavior
- [ ] Model timing requirements
- [ ] Develop Verilog/SystemVerilog testbench
- [ ] Compare simulation results with existing Neo Geo FPGA research
- [ ] Identify required cartridge response timing
- [ ] Establish a reusable cartridge verification environment

### Deliverable

A testable virtual AES/cartridge interface.

---

# Phase 5 — First Physical Cartridge

**Status: ⚪ Planned**

Build the simplest possible physical cartridge.

The first cartridge will intentionally avoid SD cards, menus, and complex
features.

### Goals

- [ ] Select development hardware
- [ ] Design first cartridge PCB
- [ ] Implement a simple fixed ROM configuration
- [ ] Manufacture prototype PCB
- [ ] Program test cartridge
- [ ] Test electrical compatibility
- [ ] Test cartridge boot behavior
- [ ] Boot first game on original AES hardware
- [ ] Document hardware results

### Target

> **Boot one game on an original Neo Geo AES using NeoForge hardware.**

### Deliverable

**NeoForge Cartridge v0.1**

A simple, reproducible development cartridge.

---

# Phase 6 — FPGA Cartridge

**Status: ⚪ Planned**

Replace fixed cartridge logic with programmable FPGA-based hardware.

### Goals

- [ ] Select FPGA platform
- [ ] Develop FPGA cartridge bus interface
- [ ] Implement cartridge memory mapping
- [ ] Implement programmable address decoding
- [ ] Implement external RAM interface
- [ ] Implement flash memory interface
- [ ] Create FPGA simulation testbench
- [ ] Validate FPGA implementation against simulator
- [ ] Boot first game using FPGA cartridge hardware

### Deliverable

**NeoForge Cartridge v0.2**

An FPGA-based programmable AES cartridge.

---

# Phase 7 — SD Card Loader

**Status: ⚪ Planned**

Add modern storage while retaining original AES hardware.

### Goals

- [ ] Select microcontroller
- [ ] Implement SD card interface
- [ ] Implement filesystem support
- [ ] Develop game loader
- [ ] Transfer ROM data to cartridge memory
- [ ] Implement cartridge reset/loading sequence
- [ ] Create basic game selection interface
- [ ] Implement error handling
- [ ] Validate loading reliability

### Deliverable

**NeoForge Flash Cartridge v0.3**

A physical SD-based cartridge capable of loading multiple games.

---

# Phase 8 — Multi-Game Platform

**Status: ⚪ Planned**

Expand the cartridge from a proof-of-concept into a practical platform.

### Goals

- [ ] Game database
- [ ] Game metadata
- [ ] Improved menu
- [ ] Save RAM support
- [ ] Automatic cartridge configuration
- [ ] Larger ROM support
- [ ] Additional cartridge mappings
- [ ] AES/MVS investigation
- [ ] Homebrew support
- [ ] Firmware update mechanism
- [ ] USB development/debug interface

### Deliverable

A practical open-source Neo Geo flash cartridge platform.

---

# Phase 9 — Compatibility

**Status: ⚪ Planned**

Test NeoForge across the broader AES hardware ecosystem.

### Goals

- [ ] Test multiple AES revisions
- [ ] Test Japanese AES systems
- [ ] Test US AES systems
- [ ] Test European AES systems
- [ ] Document compatibility
- [ ] Identify hardware-specific behavior
- [ ] Resolve timing differences
- [ ] Create AES compatibility database

### Deliverable

A documented compatibility matrix covering multiple AES revisions.

---

# Phase 10 — Advanced Cartridge Support

**Status: ⚪ Planned**

Support increasingly complex Neo Geo cartridge architectures.

### Potential Goals

- [ ] Complex banking
- [ ] Large cartridge configurations
- [ ] Additional mapper implementations
- [ ] Special cartridge hardware
- [ ] Encryption/decryption research
- [ ] Advanced memory management
- [ ] Cartridge diagnostics
- [ ] Development/debug features

### Deliverable

Broad compatibility with the Neo Geo cartridge ecosystem.

---

# Long-Term Vision

The ultimate goal of NeoForge is not simply to create another flashcart.

We want to create an open platform for **understanding, developing, testing,
and reproducing Neo Geo cartridge hardware**.

This could eventually include:

- Open-source cartridge hardware
- Open FPGA designs
- Open firmware
- ROM analysis tools
- Cartridge simulation
- Automated hardware verification
- Homebrew development tools
- AES cartridge development hardware
- Community-maintained cartridge documentation

The project should remain useful even if someone never builds the final
flash cartridge.

---

## Guiding Principles

### 1. Simulation before hardware

Whenever practical, understand and test the behavior in software before
committing it to physical hardware.

### 2. Small steps

Each milestone should produce something functional and testable.

### 3. Original hardware

NeoForge targets the original Neo Geo AES hardware rather than replacing it
with software emulation.

### 4. Open development

Research, documentation, hardware designs, and software should be developed
publicly whenever possible.

### 5. Community knowledge

NeoForge should build upon existing Neo Geo research rather than duplicating
work unnecessarily.

### 6. No copyrighted ROM distribution

NeoForge will not distribute copyrighted commercial game ROMs. Development
should use legally obtained material, homebrew, test ROMs, or other
appropriately licensed content.

---

## Versioning

Early versions represent development milestones rather than commercial
products.

- `v0.x` — Research, simulation, and prototype hardware
- `v1.x` — Functional open flash cartridge platform
- `v2.x` — Expanded compatibility and advanced features

Version numbers may change as the project evolves.
