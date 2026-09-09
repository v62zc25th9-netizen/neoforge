#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Generate NeoForge's fix-layer tiles and font as an S ROM image.

Fix tile format, per the NeoGeo Development Wiki (Fix graphics format):

  8x8 pixels, 4 bits per pixel, 32 bytes per tile. Pixels are stored as
  pairs in bytes, in columns top to bottom, with the pixel positions
  swapped inside each byte - left pixel in bits 0-3, right pixel in 4-7.

  Byte offset within a tile is  H C L L L :
      H = half   1 = left,  0 = right
      C = column 0 = left,  1 = right (within that half)
      L = line   0-7
  so offsets  0-7  are pixel columns 4,5
              8-15 are columns 6,7
             16-23 are columns 0,1
             24-31 are columns 2,3

A tile of one colour is 32 identical bytes regardless of that ordering,
which is why the solid fill tiles need no image tooling at all.

[VERIFIED: wiki Fix graphics format, read 2026-09-08]
"""
import sys

TILE_BYTES = 32

def solid(colour: int) -> bytes:
    """A tile where every pixel is `colour`. Column order is irrelevant."""
    return bytes([((colour & 0xF) << 4) | (colour & 0xF)]) * TILE_BYTES

def encode(rows, fg=15, bg=0) -> bytes:
    """
    Encode 8 strings of 8 characters ('#' = foreground) into a fix tile,
    honouring the wiki's column interleave.
    """
    assert len(rows) == 8, f"tile must have 8 rows, got {len(rows)}"
    assert all(len(r) <= 8 for r in rows), "no row may exceed 8 pixels"
    rows = [r.ljust(8, '.') for r in rows]
    px = [[fg if ch == '#' else bg for ch in row] for row in rows]
    out = bytearray(TILE_BYTES)
    for half in (0, 1):            # H
        for col in (0, 1):         # C
            # left half (H=1) covers columns 0-3, right half (H=0) columns 4-7
            base_col = (0 if half else 4) + col * 2
            for line in range(8):  # L
                left  = px[line][base_col]
                right = px[line][base_col + 1]
                out[half * 16 + col * 8 + line] = (left & 0xF) | ((right & 0xF) << 4)
    return bytes(out)

# --- font -------------------------------------------------------------------
# Hand-authored 5x7 glyphs in an 8x8 cell. Ours, so no provenance questions.
GLYPHS = {
' ': "........ ........ ........ ........ ........ ........ ........ ........",
'A': "..###... .#...#.. #.....# #.....# ####### #.....# #.....# ........",
'B': "######.. #.....#. #.....#. ######.. #.....#. #.....#. ######.. ........",
'C': ".#####.. #.....#. #....... #....... #....... #.....#. .#####.. ........",
'D': "######.. #.....#. #.....#. #.....#. #.....#. #.....#. ######.. ........",
'E': "####### #....... #....... #####... #....... #....... ####### ........",
'F': "####### #....... #....... #####... #....... #....... #....... ........",
'G': ".#####.. #.....#. #....... #..####. #.....#. #.....#. .#####.. ........",
'H': "#.....# #.....# #.....# ####### #.....# #.....# #.....# ........",
'I': "..###... ...#.... ...#.... ...#.... ...#.... ...#.... ..###... ........",
'J': "....###. .....#.. .....#.. .....#.. #....#.. #....#.. .####... ........",
'K': "#....#.. #...#... #..#.... ###..... #..#.... #...#... #....#.. ........",
'L': "#....... #....... #....... #....... #....... #....... ####### ........",
'M': "#.....# ##...## #.#.#.# #..#..# #.....# #.....# #.....# ........",
'N': "#.....# ##....# #.#...# #..#..# #...#.# #....## #.....# ........",
'O': ".#####.. #.....#. #.....#. #.....#. #.....#. #.....#. .#####.. ........",
'P': "######.. #.....#. #.....#. ######.. #....... #....... #....... ........",
'Q': ".#####.. #.....#. #.....#. #.....#. #...#.#. #....##. .####.#. ........",
'R': "######.. #.....#. #.....#. ######.. #...#... #....#.. #.....#. ........",
'S': ".######. #....... #....... .#####.. ......#. .......# ######.. ........",
'T': "####### ...#.... ...#.... ...#.... ...#.... ...#.... ...#.... ........",
'U': "#.....# #.....# #.....# #.....# #.....# #.....# .#####. ........",
'V': "#.....# #.....# #.....# #.....# .#...#. ..#.#.. ...#... ........",
'W': "#.....# #.....# #.....# #..#..# #.#.#.# ##...## #.....# ........",
'X': "#.....# .#...#. ..#.#.. ...#... ..#.#.. .#...#. #.....# ........",
'Y': "#.....# .#...#. ..#.#.. ...#... ...#... ...#... ...#... ........",
'Z': "####### .....#. ....#.. ...#... ..#.... .#..... ####### ........",
'0': ".#####.. #....##. #...#.#. #..#..#. #.#...#. ##....#. .#####.. ........",
'1': "...#.... ..##.... ...#.... ...#.... ...#.... ...#.... .#####.. ........",
'2': ".#####.. #.....#. ......#. ...###.. ..#..... .#...... #######. ........",
'3': "######.. ......#. ......#. .#####.. ......#. ......#. ######.. ........",
'4': "....##.. ...#.#.. ..#..#.. .#...#.. #######. .....#.. .....#.. ........",
'5': "#######. #....... ######.. ......#. ......#. #.....#. .#####.. ........",
'6': "..####.. .#...... #....... ######.. #.....#. #.....#. .#####.. ........",
'7': "#######. ......#. .....#.. ....#... ...#.... ..#..... ..#..... ........",
'8': ".#####.. #.....#. #.....#. .#####.. #.....#. #.....#. .#####.. ........",
'9': ".#####.. #.....#. #.....#. .######. ......#. .....#.. .####... ........",
'.': "........ ........ ........ ........ ........ ...##... ...##... ........",
',': "........ ........ ........ ........ ...##... ...##... ..#..... ........",
':': "........ ...##... ...##... ........ ...##... ...##... ........ ........",
'-': "........ ........ ........ .#####.. ........ ........ ........ ........",
'/': "......#. .....#.. ....#... ...#.... ..#..... .#...... #....... ........",
'!': "...#.... ...#.... ...#.... ...#.... ...#.... ........ ...#.... ........",
'?': ".#####.. #.....#. ......#. ...###.. ...#.... ........ ...#.... ........",
'(': "....#... ...#.... ..#..... ..#..... ..#..... ...#.... ....#... ........",
')': "..#..... ...#.... ....#... ....#... ....#... ...#.... ..#..... ........",
'+': "........ ...#.... ...#.... .#####.. ...#.... ...#.... ........ ........",
'=': "........ ........ .#####.. ........ .#####.. ........ ........ ........",
}

# Tile map.
# ASCII glyphs occupy tiles 0x00-0x7F, indexed directly by character code, so
# ngdevkit's ng_text() works with the default SROM_TXT_TILE_OFFSET of 0.
# NeoForge's own tiles sit above them.
TILE_BG     = 0x80   # opaque background      (colour 1)
TILE_WINDOW = 0x81   # fully transparent      (colour 0) - the deliberate hole
TILE_BORDER = 0x82   # opaque frame           (colour 2)
TILE_CHECK  = 0x83   # opaque checkerboard    (colours 1/3)

def build() -> bytes:
    tiles = []
    # Glyphs are drawn on an OPAQUE background (colour 1), not a transparent
    # one. This matters: a transparent glyph background is a fix pixel that
    # falls through to the sprite line buffer, so text cells would show the
    # sprite path rather than the fix path - which is the opposite of what
    # this ROM is trying to demonstrate. Observed on hardware^Wemulator
    # 2026-09-09: with bg=0 every character cell rendered backdrop green.
    for code in range(0x80):
        spec = GLYPHS.get(chr(code).upper())
        tiles.append(encode(spec.split(), fg=15, bg=1) if spec
                     else solid(1))
    tiles.append(solid(1))   # TILE_BG
    tiles.append(solid(0))   # TILE_WINDOW - colour 0 is transparent
    tiles.append(solid(2))   # TILE_BORDER
    tiles.append(encode([    # TILE_CHECK
        "####....", "####....", "####....", "####....",
        "....####", "....####", "....####", "....####",
    ], fg=1, bg=3))
    return b"".join(tiles)

if __name__ == "__main__":
    data = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "neoforge.fix"
    with open(out, "wb") as f:
        f.write(data)
    print(f"{out}: {len(data)} bytes, {len(data)//TILE_BYTES} tiles "
          f"(ASCII 0x00-0x7F, then BG=0x{TILE_BG:02X} WINDOW=0x{TILE_WINDOW:02X} "
          f"BORDER=0x{TILE_BORDER:02X} CHECK=0x{TILE_CHECK:02X})")
