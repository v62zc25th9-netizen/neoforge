# Neo Geo Cartridge Architecture: MVS vs AES

Status: initial research notes. Claims marked per the evidence convention in
`CLAUDE.md`.

Primary source throughout is the NeoGeo Development Wiki
(https://wiki.neogeodev.org), hosted by Furrtek.

---

## 1. The difference that actually matters

The common explanation — that MVS and AES cartridges are incompatible because
of physical size or pinout — is wrong, or at best incidental. Wikipedia states
the incompatibility is "due to different physical sizes." Ignore this.

The real difference is **where the sprite graphics serializer lives**.

Sprite pixel data must be serialized before reaching the video chain. The
serializer takes the C ROM data bus as C0~C31 (two 16-bit halves), which
supplies all pixel data for an 8-pixel line, clocked by EVEN1, EVEN2, H and
LOAD from the LSPC, returning DOTA/DOTB pixel opacity to it.
`[VERIFIED: wiki NEO-ZMC2, LSPC2-A2]`

- **MVS**: the serializer is **on the motherboard**. The cartridge exposes the
  complete C ROM data bus at the edge connector, and the board's chip
  serializes it. Because NEO-ZMC2 is not present in the cart, plain NEO-ZMC
  handles M1 ROM bankswitching instead. `[VERIFIED: wiki MVS cartridge]`

- **AES**: the serializer is **in the cartridge**. AES carts contain a
  NEO-ZMC2 or PRO-CT0. The wiki states plainly that this is the reason
  MVS-to-AES converters cannot be passive devices.
  `[VERIFIED: wiki AES cartridge]`

### Consequence for NeoForge

There is no such thing as a dumb ROM-only AES cartridge. Even a single-game
EPROM board must contain a serializer, whether a harvested donor chip or
programmable logic. This is the project's first hard requirement.

---

## 2. Serializer chip lineage

| Chip | Notes |
|---|---|
| PRO-CT0 | Early gate array. Also sold as **SNK-9201** and **ALPHA-8921** (original Alpha Denshi name, from their Alpha68k system). Serializes sprite graphics in AES carts and MVS boards. `[VERIFIED: wiki PRO-CT0]` |
| NEO-ZMC2 | NEO-ZMC (Z80 bankswitching) + PRO-CT0 (serializer) in one package. Found in second-revision MVS boards for the PRO-CT0 logic only, and in AES cartridges. `[VERIFIED: wiki NEO-ZMC2]` |
| NEO-CMC | Later replacement. The 90G06CF7042 variant bundles NEO-273 logic, NEO-ZMC logic, C-ROM decryption, C and S-ROM multiplexing, and S-ROM bankswitching. The CF7050 variant adds M-ROM decryption. `[VERIFIED: MAME neogeo.c chip notes, sourced from wiki]` |

Downstream, NEO-B1 receives serialized sprite graphics from the multiplexer
(NEO-ZMC2, PRO-CT0 or NEO-CMC) while fix-layer graphics come directly from the
enabled fix ROM. Two pixels are written at a time into internal line buffers.
`[VERIFIED: wiki NEO-B1]`

**`[UNVERIFIED]`** — Because NEO-CMC-era cartridges carry the multiplexer
function on the cart itself, they plausibly behave differently through an
MVS-to-AES converter than pre-CMC cartridges do. This would explain why
converter compatibility varies by title. Not confirmed; needs testing or a
source.

---

## 3. Connectors

Both formats are two boards (PROG and CHA) with double-sided edge connectors.
The count differs:

- **MVS**: 2 × 2 × 60 = **240 pins** `[VERIFIED: wiki MVS cartridge]`
- **AES**: 2 × 2 × 50 = **200 pins**, some missing or unused
  `[VERIFIED: wiki AES cartridge / AES cartridge pinout]`

### Known documentation trap

The wiki warns that pinouts published elsewhere have **/ROMOE and 4MB
swapped**, an error originating in the official schematics. Correct values:
/ROMOE on pin 33 bottom, 4MB on pin 34 bottom. `[VERIFIED: wiki MVS cartridge
pinout]`

Treat any third-party pinout as suspect until cross-checked against the wiki.

---

## 4. MVS-only signals

`SLOTCS` goes low when a slot is in use. On multi-slot boards it is driven from
NEO-F0 SLOT0~5; on single-slot boards it is tied to SYSTEMB. Link-capable games
use it to trap the HD6301 in an idle loop when high. `[VERIFIED: wiki MVS
cartridge pinout, incl. Furrtek's correction that PROGEOP uses SLOTCS rather
than PROGSF1]`

Link-capable titles — Thrash Rally, Riding Hero, League Bowling — carry HD6301
microcontrollers and SN75176 differential bus drivers for point-to-point play
over 3.5mm cables. `[VERIFIED: wiki MVS cartridge]`

Not directly relevant to an AES-only cart, but relevant to any future converter
or MVS variant.

---

## 5. Protection hardware

Precomputable (decrypt offline in the loader):
- NEO-CMC C-ROM and M-ROM decryption
- SMA P-ROM scrambling
- PCM2 sound encryption

Requires live logic (challenge-response — cannot be precomputed):
- **PRO-CT0 / SNK-9201 as security device**, on PROG-G2 boards for Fatal Fury 2
  and Super Sidekicks. SNK's first copy-protection attempt: the game writes
  values and expects specific replies determined by the chip's hard-to-guess
  logic. `[VERIFIED: wiki PRO-CT0]`
- **Altera MAX CPLDs** (EPM7128SQC100-15) on KOF '98 (NEO-MVS PROGSF1) and
  Metal Slug X (NEO-MVS PROGEOP). `[VERIFIED: wiki MVS cartridge, MAME chip
  notes]`

Note that Terraonion's NeoSD MVS advertises running **unpatched** games by
emulating the original cartridge protections rather than pre-decrypting.
`[VERIFIED: Terraonion product page]` Offline decryption remains the cheaper
route for a first version, at the cost of a ROM format incompatible with
existing carts.

---

## 6. Prior art

### Commercial

**Terraonion NeoSD** (MVS and AES versions, plus Pro): 768 MB flash, ARM
Cortex-M4 at 168 MHz with 1 MB flash and 128 MB RAM, **two Lattice XP2 FPGAs**.
`[VERIFIED: Terraonion product pages]`

The two-FPGA arrangement is worth studying — it maps onto the PROG/CHA split.

**Darksoft multi**: MVS and AES (MultiAES) versions. Uses a different ROM file
format than NeoSD. `[VERIFIED: multiple community sources]`

### Compatibility warning from the field

NeoSD MVS has been reported to be picky about motherboard revision, with
corruption and resets on NEO-MVH boards while working on MVS-1A, MVS-1B and
MVS-1C. The vendor's stated explanation was that the cart uses edge contacts
standard cartridges do not. `[ANECDOTAL: arcade-museum forum thread]`

Whatever the actual cause, this is evidence that testing on one machine proves
very little. Plan for testing across AES board revisions.

### Open source

- `neogeodev/FusionConverter` — open-hardware MVS-to-AES converter with CPLD
  sources. Directly relevant: a working serializer implementation.
- `neogeodev/NeoGeoFPGA-sim` — chipset in Verilog. `neo_zmc2.v` (largely by
  Kyuusaku) and `zmc2_dot.v` are the serializer core.
- `furrtek/Neogeo_MiSTer` — full FPGA core.

Historical note: the PRO-CT0 logic was reverse-engineered and published to the
NeoGeo dev wiki by Calpis, which is what made non-donor converters possible.
`[ANECDOTAL: AssemblerGames thread]`

---

## 7. Electrical

The Neo Geo bus is 5V. Modern FPGAs and CPLDs are 3.3V or lower, so the design
needs either 5V-tolerant I/O or real level translation across 100+ signals.

Community criticism of cheap multicarts centres on exactly this — the 161-in-1
is reported to still have a "3V3 vs 5V flash issue" in current revisions, which
some consider makes it unsafe to run on expensive AES hardware.
`[ANECDOTAL: shmups forum]`

**`[UNVERIFIED]`** — Whether that specific mismatch is the cause of the
161-in-1's known ADPCM audio failures through MVS-to-AES converters is not
established. The observation that the failure persisted after a converter was
repaired with a ZMC2 — while original carts and other bootlegs worked — points
at the multicart's own FPGA rather than the conversion, since the ADPCM ROM is
on the cartridge and the serializer never touches the audio path.
`[ANECDOTAL: AssemblerGames thread]`

---

## Open questions

1. Donor chip or CPLD for the first physical cart? (See `CLAUDE.md`.)
2. Offline decryption or live protection emulation?
3. Which AES board revisions exist, and how do they differ? Not yet researched.
4. C-ROM bandwidth budget — the LSPC fetches continuously during active
   display. What storage and arbitration meets it? Not yet analysed.
5. How does the YM2610's independent ADPCM address bus get serviced?
