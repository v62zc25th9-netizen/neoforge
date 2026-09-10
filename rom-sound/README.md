# NeoForge V ROM test

Plays one ADPCM-A sample from the cartridge V ROM, every two seconds, with no
controller needed.

```sh
brew install ngdevkit ngdevkit-gngeo   # if not already
make          # build the cartridge
make gngeo    # build and run, AES mode
```

## Why this exists

A cartridge supplies five ROMs, and they are five separate jobs the board has
to do:

| ROM | Feeds | Exercised before this? |
|---|---|---|
| P | 68k program | yes, by everything |
| S | fix tiles | yes, heavily |
| M | Z80 program | yes, since we started building our own |
| C | sprite graphics | barely — one tile |
| V | ADPCM samples | **no. 512 KB of zeroes.** |

The V ROM is not decoration. The YM2610 lives on the motherboard, but the
samples it plays come from the cartridge, over their own address and data lines
across the connector, with cartridge-side decode logic behind them — on
PROGBK1, a 74LS139. See [`../docs/prom-banking.md`](../docs/prom-banking.md).

If a NeoForge board cannot serve V ROM reads, every game is silent, and nothing
else we have built would notice. This closes that gap before anyone burns an
EPROM.

## What you should hear

A short click, then two tones an octave apart — 440 Hz then 880 Hz. About a
third of a second, repeating every two seconds. The on-screen counter shows how
many times it has fired.

| What happens | What it means |
|---|---|
| Click and two tones, counter climbing | The V ROM path works. |
| Silence, counter climbing | Either the V ROM path is broken or the Z80 driver never started. **Check the volume first** — it is the usual cause. |
| Counter stuck | The 68k is wedged. Nothing to do with sound. |
| Nothing on screen at all | The ROM did not boot. Interesting, and unrelated to this test. |

Deliberately unmusical. The question is *"did any sample data reach the
YM2610"*, and an octave jump answers it through a small television speaker in a
noisy room. A pure sine is easy to mistake for hum; noise is easy to mistake
for a fault.

## What this proves, and where

**In an emulator:** that our V ROM is correctly constructed — ADPCM-A encoding,
sample offsets, the map `vromtool` generates from `samples.yaml`. Those are
real build-correctness questions, and an emulator can answer them. That is more
than GnGeo could do for the fix-layer test, where it could only validate the
instrument.

**On hardware:** that a cartridge can serve V ROM reads. Only silicon answers
that — and only once *our* board is doing the serving, which is roadmap Phase 7.
Run on a donor cart or a commercial flash cart, this tests our ROM image and
SNK's board, which is still worth knowing before an EPROM gets burned.

## The sample is generated, not borrowed

`sample.py` synthesises `assets/chirp.wav` with nothing but the Python standard
library. No audio file is committed here.

That is the same reasoning as `../rom/tiles.py` drawing its own graphics, and
the same reasoning that got the borrowed Z80 driver out of the fix-layer test:
a third-party asset carries a licensing question that a generated one does not.
The YM2610's ADPCM-A decoder runs at a fixed rate near 18.5 kHz, so the sample
is generated at 18500 Hz mono directly rather than resampled.

## Files

| | |
|---|---|
| `sample.py` | Generates the WAV. MIT. |
| `samples.yaml` | Sample map. `vromtool` packs the V ROM and emits the offsets from this. |
| `sound-driver.s` | Z80 driver — the jump table plus one command that plays the sample. **LGPL-3.0-or-later**, derived from ngdevkit-examples. |
| `main.c` | The 68k side. Writes a command byte to `0x320000`. MIT. |
| `Makefile` | Build. |

The fix tiles come from `../rom/tiles.py` — one font generator, two ROMs.

## Why this is a separate ROM

`../rom` is published as `fixtest-v1` with a results table people may already
be collecting into. Changing what that ROM does would invalidate those results.
The two Makefiles overlap and are expected to drift, because they test
different things.

## Note on the `-aes` nullsound variant

The driver links `nullsound-aes.lib` rather than the default. For this ROM that
is a formality: the two variants differ only in `fm-tables.inc` and
`ssg-tables.inc`, only `entrypoint.s` is assembled per-variant, and **ADPCM-A
does not use those tables** — its playback rate is fixed by the YM2610's own
clock. `[VERIFIED: ngdevkit nullsound/Makefile.in]`

So the chirp sounds identical either way. The distinction becomes real the
moment anything here uses FM or SSG, because AES and MVS clock the YM2610
differently and the tables are computed from that clock.

## Note on `vromtool`

It runs twice, because `--roms` and `--asm` are mutually exclusive modes: once
to pack the V ROM, once to emit the assembler defines the driver includes. The
`-o` pattern must contain a literal `X`, which `vromtool` replaces with the ROM
number — so `neoforge-vromtest-vX.vX` produces `neoforge-vromtest-v1.v1`. This
is not documented anywhere obvious and is easy to lose an hour to.
