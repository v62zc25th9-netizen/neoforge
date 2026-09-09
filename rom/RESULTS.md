# Fix-layer test results

Reports from running `rom/` on real hardware. **Please add yours** — open a pull
request against this file, or an issue, whichever is easier.

The question is [Q1](../docs/open-questions.md): does a fix-layer-only AES
cartridge need a sprite serializer? We think not, from reading the HDL. Nobody
has checked it on silicon.

## What to report

Run the ROM and watch the framed window for one full cycle, about four seconds.

| Window behaviour | What it means |
|---|---|
| Alternates **green** and **red** with the status line | Expected on stock hardware. The sprite path works and the test can see it. |
| **Green in both phases** | On a serializer-less cartridge: Q1 confirmed. On stock hardware: a genuine surprise — please tell us. |
| **Anything else** — garbage, flicker, wrong colours, no boot | The interesting case. Photograph it. |

Please include your console (AES model and region if you know it), how you
loaded the ROM, and a photograph if anything is unexpected.

## Results

| Date | Console | Loaded via | Sprites OFF | Sprites ON | Notes |
|---|---|---|---|---|---|
| 2026-09-09 | — (GnGeo emulator) | ngdevkit build | green | red | Reference. An emulator models the sprite path correctly and cannot fail this test; recorded to show the expected reading. |

<!-- Add a row above. Keep the reference row last so the emulator baseline stays visible. -->

## Why an emulator result is not enough

GnGeo and MAME implement the serializer internally and correctly, so they will
always produce the alternating result. What they validate is the *instrument* —
that the window can register sprite activity at all. Only hardware can answer
the question.

## The two hardware results worth having

**On stock hardware with any flash cart** — NeoSD, Darksoft, anything that loads
a homebrew `.zip`. The C ROMs here are all but empty, so with sprites off the
serializer is fed zeros and outputs `GAD`/`GBD` = 0 with `DOTA`/`DOTB` low: the
same end state a missing serializer with those pins grounded would produce. That
tests most of Q1 on real silicon **with no soldering at all.**

**On a cartridge with no serializer fitted** and `DOTA`/`DOTB` tied low. The
window should stay green through both phases. That is roadmap Phase 4 and the
result the whole question turns on.
