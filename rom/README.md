# NeoForge fix-layer test ROM

The first ROM NeoForge has written. It is also the ROM that would test
[Q1](../docs/open-questions.md) on real hardware.

```sh
brew install ngdevkit ngdevkit-gngeo   # if not already
make          # build the cartridge
make gngeo    # build and run, AES mode
```

## What it does and why

Q1 established, from the HDL, that the fix layer never touches the sprite
serializer — but only where a fix pixel is **opaque**. Transparent fix pixels
fall through to the sprite line buffers instead.

ngdevkit's stock hello world calls `ng_cls()`, which fills the screen with tile
255, the **transparent** tile. Almost every pixel of it therefore lands in the
case that still depends on the sprite path. Booting that on a serializer-less
cartridge would tell you very little, and could easily mislead.

This ROM inverts that:

1. **The whole screen is an opaque fix tile, including the text cells.**
   Everything legible is proof the fix path works with no sprite involvement.
2. **One deliberate rectangle is transparent fix**, framed in orange. That is a
   controlled window onto the sprite line buffer.

### The first run got this wrong, instructively

`[MEASURED: GnGeo, 2026-09-09]` The glyphs were originally encoded with
`bg=0` — colour 0, which on the Neo Geo is **transparent**. So every character
cell was white strokes on transparent fix, and every one of them fell through to
the sprite path. The first screenshot showed backdrop green behind all the text,
with the intended blue background visible only in the gaps between lines.

The ROM was behaving correctly; the design was wrong. Fixed by drawing glyphs on
an opaque background (`bg=1`), so a text cell is now genuinely opaque fix.

Two things worth keeping from that:

- It was a **stronger** pass than intended. Dozens of independent transparent
  regions scattered across the screen all resolved to backdrop, not merely one
  rectangle. Nothing was writing the line buffers anywhere.
- **Font glyph backgrounds are transparent by default**, in our font and in
  ngdevkit's. That makes stock hello world even more sprite-path-dependent than
  Q1 first noted: not just the cleared background, but the inside of every
  letter. Anyone testing a serializer-less cartridge with a stock text ROM is
  looking at the sprite path almost everywhere they think they are looking at
  the fix layer.

`linebuffer.v` forces the palette address to all ones during clearing writes,
ignoring `GAD`/`GBD` entirely, so a quiet sprite path resolves to palette entry
`0xFFF` — the backdrop. We set that to bright green.

| Window shows | Meaning |
|---|---|
| **Green** | Line buffer holds only backdrop. Q1's reasoning holds. |
| **Anything else** | Something is writing the line buffers. Q1 does not hold here. |

**There is no sprite data in this cartridge.** The C ROMs are zero-filled. It is
a genuinely sprite-free cartridge image.

## What a green window does and does not prove

In an emulator the sprite path is modelled correctly, so green is expected and
proves only that the ROM does what it claims — a useful check, and no more.

The result that matters is on real AES hardware with no serializer fitted and
`DOTA`/`DOTB` tied low. That is roadmap Phase 4, and it is the point of building
this now rather than later.

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

## Known rough edge

The M ROM is borrowed. This ROM makes no sound and does not care what the Z80
runs, but the system expects a valid program there, so the Makefile takes the
prebuilt driver from an `ngdevkit-examples` checkout:

```sh
make NGDEVKIT_EXAMPLES=/path/to/ngdevkit-examples
```

That is the build's only external dependency. Replacing it with a minimal driver
linked against `nullsound-aes.lib` — note the AES-specific variant — would make
this fully self-contained. Worth doing before anyone else is asked to build it.
