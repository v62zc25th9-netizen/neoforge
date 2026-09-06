# Licensing

NeoForge is licensed per directory, because the material in this repository is
of four different kinds and one licence cannot serve all of them.

| What | Where | Licence | SPDX |
|---|---|---|---|
| Hardware designs — PCB, schematics, gerbers, BOMs | `hardware/` | CERN Open Hardware Licence v2 — Strongly Reciprocal | `CERN-OHL-S-2.0` |
| HDL — Verilog, testbenches, constraints | `hdl/`, `sim/` | GNU General Public License v3.0 or later | `GPL-3.0-or-later` |
| Software — tools, firmware, scripts | `tools/`, `firmware/`, `sw/` | MIT | `MIT` |
| Documentation | `docs/`, `*.md` at root | Creative Commons Attribution-ShareAlike 4.0 | `CC-BY-SA-4.0` |

Full texts are in [`LICENSES/`](LICENSES/). Where a file's location is
ambiguous, its SPDX header wins. New files should carry one:

```
// SPDX-License-Identifier: GPL-3.0-or-later
```

---

## Why these, specifically

### Hardware — CERN-OHL-S (strongly reciprocal)

The project's premise is that Neo Geo flash cartridges already exist and none of
them are open. A permissive hardware licence would let a vendor take NeoForge's
boards closed and ship exactly the thing the project exists as an alternative
to. Strong reciprocity means anyone who distributes a modified NeoForge board
must publish their design files as well.

This does not prevent commercial use. Someone can manufacture and sell NeoForge
cartridges. They simply cannot fork the design closed.

### HDL — GPL-3.0-or-later

**This one is forced, not chosen.**

NeoForge's serializer work derives from `neogeodev/NeoGeoFPGA-sim`, which is
GPL-3.0-**or-later** (confirmed in per-file headers, not merely the LICENSE
file). A derivative of GPL-3.0 code cannot be distributed under MIT. Our HDL
therefore has to be GPL-3.0-or-later, and the repository's blanket MIT was
already wrong the moment `sim/zmc2_dot_tb.v` was written.

### Software — MIT

Tooling has no inherited obligation and benefits from maximum reuse. A ROM
analysis tool that ngdevkit or MAME could borrow from is worth more permissive
than protected. This is what the repository was already under and it stays.

### Documentation — CC-BY-SA

Most of what NeoForge produces that other people will want is documentation and
measurements. ShareAlike matches the norm of the community this work builds on,
and lets the NeoGeo Development Wiki and similar projects use it with
attribution.

---

## The GPL-2.0 / GPL-3.0 incompatibility — read before writing HDL

There are two open implementations of the sprite serializer, and **they are
under mutually incompatible licences:**

| Project | Licence | Notes |
|---|---|---|
| `neogeodev/NeoGeoFPGA-sim` | GPL-3.0-**or-later** | Per-file "or (at your option) any later version" grant |
| `neogeodev/NeoChips` | GPL-**2.0** | No "or later" grant found in the repository |

GPL-2.0-only and GPL-3.0 cannot be combined into a single derivative work.
**NeoForge cannot derive from both.** The project has chosen the
NeoGeoFPGA-sim lineage, which means:

- ✅ **Do** read and derive from NeoGeoFPGA-sim, under GPL-3.0-or-later.
- ✅ **Do** use NeoChips' NEO-ZMC2 as a **component** — buy it, or build it from
  their published files and fit it to a board. Using a separately-licensed part
  creates no obligation on our sources.
- ❌ **Do not** read `NeoChips/NEO-ZMC2/neo-zmc2.v` (or its `.jed`) into
  NeoForge's own HDL. That would create a work derived from GPL-2.0-only code
  that we cannot then license as GPL-3.0.

If you have looked at the NeoChips sources and then write serializer HDL, say
so in your pull request. This is not an accusation; it is how contamination
gets caught early instead of at the point where the project has to be
rewritten.

`FusionConverter`'s licence has not been checked yet. **`[UNVERIFIED]`** — do
that before deriving from it.

---

## Reference material is not vendored

Sources under other licences are fetched into `.reference/` by the build rather
than copied into this repository. See `sim/Makefile`. This keeps foreign
licences in their own trees under their own terms and keeps this repository's
own licensing statements true.

---

## Contributing

By submitting a contribution you agree to license it under the licence
governing the directory it lands in. If that does not work for you, open an
issue before writing the code rather than after.

There is no CLA and no copyright assignment. Contributors keep their copyright.
The practical consequence is that **this licensing structure is now effectively
permanent** — changing it later would require the agreement of everyone who has
contributed by then.

## ROMs

No copyrighted ROM data belongs in this repository under any licence. See
`contributing.md`.
