# Licensing

NeoForge is licensed per directory, because the material in this repository is
of four different kinds and one licence cannot serve all of them.

| What | Where | Licence | SPDX |
|---|---|---|---|
| Hardware designs — PCB, schematics, gerbers, BOMs | `hardware/` | CERN Open Hardware Licence v2 — Strongly Reciprocal | `CERN-OHL-S-2.0` |
| HDL — Verilog, testbenches, constraints | `hdl/`, `sim/` | GNU General Public License v3.0 or later | `GPL-3.0-or-later` |
| Software — tools, firmware, scripts | `tools/`, `firmware/`, `sw/`, `rom/` | MIT | `MIT` |
| Exception: the Z80 sound drivers | `rom/sound-driver.s`, `rom-sound/sound-driver.s` | GNU Lesser General Public License v3.0 or later | `LGPL-3.0-or-later` |
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

### We asked, and the question is still open

NeoForge opened `neogeodev/NeoChips` issue #1 on 2026-09-09 asking whether the
grant is v2-only or v2-or-later. It was closed without a licensing answer.
`[VERIFIED: NeoChips issue #1]`

So we continue to treat it as **v2-only**, which is the conservative reading and
the one the repository supports on its face: GitHub reports the licence as
GPL-2.0, and no "or later" grant appears in the LICENSE or the per-file headers.

Two things that are **not** in dispute, stated plainly because they are easy to
mistake for an answer to the question above:

- **Commercial use is permitted.** GPL-2.0 allows commercial use, modification,
  distribution, and one-for-one copies; the NeoChips README actively encourages
  building your own boards. Nobody had to grant us that — it is what the licence
  says.
- **Reciprocity comes with it.** A derivative must be released under the same
  licence. That condition is exactly what makes GPL-2.0-only incompatible with
  our GPL-3.0-or-later HDL.

The question was never *may we use it*. It was *may we combine it*, and absent
an answer we must assume no.

A trap worth naming: the NeoChips README says "See paragraphs 11 and 12 of the
LICENSE file." Those are GPL-2.0's **NO WARRANTY** and **limitation of
liability** clauses. They are a disclaimer, not a grant, and they say nothing
about versions or combination.

**This costs the project little.** The component route above is unaffected, and
`docs/serializer.md` shows both halves of NEO-ZMC2 are already characterised
from the NeoGeoFPGA-sim lineage, which we may derive from freely.

---

If you have looked at the NeoChips sources and then write serializer HDL, say
so in your pull request. This is not an accusation; it is how contamination
gets caught early instead of at the point where the project has to be
rewritten.

### Checked 2026-09-08 — and it is less settled than it looked

`FusionConverter` was checked: it also ships a bare **GPL-2.0** LICENSE file.
So both of the synthesizable serializer references are GPL-2.0, not just
NeoChips.

But **neither project states a version number anywhere except in the licence
text itself.** No per-file headers, no statement in either README:

- `NeoChips/NEO-ZMC2/neo-zmc2.v` begins `// NEO-ZMC2 repro / furrtek 2019 /
  Tested ok :)` — no licence header.
- `FusionConverter/fusion_vsense_top.v` begins `// Fusion converter / For CHA8
  (rev. H) and up...` — no licence header.

That matters, because **section 9 of the GPLv2 text both repositories ship**
says:

> If the Program does not specify a version number of this License, you may
> choose any version ever published by the Free Software Foundation.

On that reading, a recipient may take either project under GPL-3.0, which would
make both **compatible** with NeoForge's GPL-3.0-or-later HDL after all.

**We are not treating that as settled.** `[UNVERIFIED]` It is an interpretation
of licence text by people who are not lawyers, the presence of a v2 LICENSE file
is itself arguably "specifying a version", and the FSF advises per-file version
statements precisely because bare-LICENSE cases are ambiguous.

**The cheap, correct fix is to ask.** Both projects are Furrtek's. An issue on
each asking whether the intent is "v2 only" or "v2 or later" costs nothing and
settles it permanently — for us and for everyone else who wants to build on
them.

**Until that answer arrives, the conservative rule below stands:** use them as
components, do not read them into NeoForge's HDL.

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

## Built ROMs, and the ngdevkit runtime

`rom/` holds our own sources (MIT), but the **ROM image** built from them is not
just our code: it links ngdevkit's runtime and startup code, which is
**LGPL-3.0-or-later**. `[UNVERIFIED — confirm against ngdevkit's per-file
headers before the first release that anyone relies on]`

If that is right, distributing a built ROM carries the LGPL's relinking
obligation: recipients must be able to substitute a modified runtime and rebuild
a working image. In practice we satisfy that by publishing the complete build —
`rom/main.c`, `rom/tiles.py` and `rom/Makefile` are all here, and ngdevkit is
public — so anyone can rebuild from a modified runtime. We are not shipping an
opaque binary with the sources withheld, which is the case the clause exists to
prevent.

The same reasoning covers the M ROMs, which link `nullsound-aes.lib` —
also LGPL-3.0-or-later, also part of ngdevkit. Both `rom/sound-driver.s` and
`rom-sound/sound-driver.s` are derived from ngdevkit-examples
(`base-sound-driver.s` and `user_commands.s`) and carry that licence
themselves, which is why they are called out as an exception in the table
above. Everything else under `rom/` and `rom-sound/` is MIT, including the
generators — `tiles.py` and `sample.py` are our own.
`[MEASURED: 2026-09-10]` — the release no longer redistributes a third-party
binary; the driver is built from a source file in this repository.

One loose end, recorded rather than hidden:

- The exact licence and headers of every ngdevkit file we link have not been
  read individually. `nullsound` and the runtime carry LGPL-3.0-or-later
  headers where we have looked. Do a careful pass before treating the
  paragraphs above as settled.

## ROMs

No copyrighted ROM data belongs in this repository under any licence — no
commercial games, ROM fragments, encrypted blobs or BIOS dumps. ROMs built from
NeoForge's own sources are a different thing and are published deliberately.
See `contributing.md`.
