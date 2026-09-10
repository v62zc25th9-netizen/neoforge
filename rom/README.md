# NeoForge fix-layer test ROM

The first ROM NeoForge has written. It is also the ROM that would test
[Q1](../docs/open-questions.md) on real hardware.

```sh
brew install ngdevkit ngdevkit-gngeo   # if not already
make          # build the cartridge
make gngeo    # build and run, AES mode
```

**You do not have to build it.** A prebuilt `neoforge-fixtest.zip` is attached
to the `fixtest-v1` release. If you have an AES and any flash cart, run it and
add a line to [`RESULTS.md`](RESULTS.md) — that is the single most useful thing
anyone outside this repository can do right now.

## What it does and why

Q1 established, from the HDL, that the fix layer never touches the sprite
serializer — but only where a fix pixel is **opaque**. Transparent fix pixels
fall through to the sprite line buffers instead.

ngdevkit's stock hello world calls `ng_cls()`, which fills the screen with tile
255, the **transparent** tile. Almost every pixel of it therefore lands in the
case that still depends on the sprite path. Booting that on a serializer-less
cartridge would tell you very little, and could easily mislead.

This ROM inverts that. The screen is opaque fix everywhere — background *and*
text cells — except one orange-framed rectangle of transparent fix. That
rectangle is a controlled window onto the sprite line buffer, and the backdrop
(palette entry `0xFFF`) is set to green.

### The alternation is the point

Every two seconds the ROM enables and disables a screen-filling sprite:

| Phase | Expected on an ordinary AES |
|---|---|
| `SPRITES: OFF` | Window **green** — nothing has written the line buffer |
| `SPRITES: ON` | Window **red** — the sprite path is writing it |

**That alternation is the positive control**, and without it the test would be
close to worthless. A green window on its own cannot distinguish *"the sprite
path is quiet"* from *"this ROM is incapable of seeing the sprite path."* Watch
it go red and you know the window has teeth.

**On a cartridge with no serializer and `DOTA`/`DOTB` tied low, the window
should stay green in both phases.** The difference between alternating and
staying green is exactly Q1's answer.

The sprite state is also set explicitly at boot — all 448 `SCB3` slots zeroed —
so the test runs from a known state rather than inheriting whatever the BIOS
left in VRAM.

### The one tile of sprite data

The C ROMs hold exactly one solid 16×16 tile, the minimum the control needs;
everything else in them is zero. An earlier revision had them entirely blank,
which was tidier but made a positive control impossible — a sprite pointing at
zeroed C ROM produces transparent pixels and writes nothing, so it would have
looked identical to no sprite at all.

Like the fix tiles, it needs no image tooling: for a tile of one colour the
block and row interleave cancels out, so C1 and C2 are each 64 bytes of two
repeating values. `[VERIFIED: wiki Sprite graphics format]`

## What a green window does and does not prove

In an emulator the sprite path is modelled correctly, so **alternating green and
red is the expected result** and proves only that the ROM works — which is
exactly what a positive control is for.

Two hardware results are worth having, and only one of them needs a donor cart:

**On an ordinary AES with any flash cart** — NeoSD, Darksoft, anything that can
load a homebrew `.zip`. The C ROMs here are all but empty, so with sprites off
the serializer is fed zeros and outputs `GAD`/`GBD` = 0 with `DOTA`/`DOTB` low:
the same end state a missing serializer with those pins grounded would produce.
That tests most of Q1 on real silicon with no soldering at all. **If you have an
AES and a flash cart, this is the single most useful thing you can contribute to
this project right now.**

**On a serializer-less cartridge** with `DOTA`/`DOTB` tied low — roadmap Phase 4.
Here the window should stay green through both phases. That is the result the
whole question turns on.

The remaining untested difference between the two is `GAD`/`GBD` floating rather
than driven to zero, and Q1's fourth finding is the reason to expect that not to
matter.

## Files

| | |
|---|---|
| `tiles.py` | Generates the S ROM: an 8×8 font at ASCII indices plus four NeoForge tiles. No image tooling — a solid fix tile is 32 identical bytes whatever the column interleave. |
| `main.c` | The ROM. |
| `Makefile` | Build. |

The fix tile format is documented on the wiki (*Fix graphics format*) and
restated in `tiles.py`'s docstring. `tiles.py` round-trips its own output during
development, so the encoder and a decoder written from the same spec agree —
which catches typos but would not catch a misreading of the spec. **The screen
is the real check.**

## The M ROM

This ROM makes no sound, but the BIOS expects a valid Z80 program in the M ROM
and talks to it during boot. `sound-driver.s` supplies the command jump table
and nothing else, linked against `nullsound-aes.lib`.

`nullsound` ships with ngdevkit, so **the build needs no second checkout** —
`make` works from a clean clone. `[MEASURED: 2026-09-10]` Earlier builds copied
a prebuilt driver out of an `ngdevkit-examples` tree, which made the build
unreproducible for anyone without it and put a third-party binary in the
release.

`-aes` rather than the default variant: the two differ only in frequency tables
derived from the audio clock, which AES and MVS drive differently. Nothing here
plays a note, so it makes no audible difference — but this is an AES project.

### The subtlety in the jump table

Entry 2 is not a command handler, and treating it like one produces something
that works in an emulator and may not on hardware.

Command 2 is *"reset the driver and play the eye-catcher music"*. nullsound
implements it by initialising the driver and then **calling entry 2 as a
subroutine**, with the main loop as the return address — the music itself has to
come from the game ROM, which is why nullsound cannot provide it. `01-helloworld`
points entry 2 at ngdevkit's attract music, which is the only reason that
example needs an extra library.

We have no music, so entry 2 must return cleanly and do nothing. It
deliberately does **not** jump to `snd_command_unused`: that ends in `retn`,
correct inside an NMI but wrong here, because by that point the driver has
already returned from the NMI. Entry 2 is a plain `ret`.

Licensing note: `sound-driver.s` is derived from ngdevkit-examples'
`base-sound-driver.s` and is therefore **LGPL-3.0-or-later** — the one file
under `rom/` that is not MIT. See [`../LICENSE.md`](../LICENSE.md).
