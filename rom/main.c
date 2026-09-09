// SPDX-License-Identifier: GPL-3.0-or-later
/*
 * NeoForge fix-layer test ROM.
 *
 * Purpose: exercise exactly the display path that a serializer-less AES
 * cartridge would use, and put the sprite path on screen where it can be
 * inspected.
 *
 * Background of Q1 (docs/open-questions.md):
 *
 *   Fix-layer graphics run from the S ROM straight to the cartridge edge
 *   connector and never touch the sprite serializer. In NEO-B1 an *opaque*
 *   fix pixel wins outright over the sprite line buffers. Where a fix pixel
 *   is *transparent*, the line buffer shows through instead - and with no
 *   serializer fitted, its contents depend on DOTA/DOTB gating the writes.
 *
 * So this ROM does two things at once:
 *
 *   1. Fills the whole screen with an opaque fix tile. Everything you can
 *      read is proof the fix path works with no sprite involvement.
 *   2. Leaves one deliberate rectangle of transparent fix tiles. That is a
 *      controlled window onto the sprite line buffer. With the sprite path
 *      quiet it should show the backdrop colour - palette entry 0xFFF, which
 *      we set to bright green - because linebuffer.v forces DATA_IN to all
 *      ones during clearing writes, ignoring GAD/GBD entirely.
 *
 * Green window  -> sprite path is quiet, as predicted.
 * Anything else -> the line buffers are being written, and Q1's reasoning
 *                  does not hold on this hardware.
 *
 * There are no sprites and no C ROM data in this cartridge at all.
 *
 * In an emulator the sprite path is modelled correctly, so green is expected
 * and proves only that the ROM does what it claims. The result that matters
 * is on real hardware with no serializer fitted.
 */

#include <ngdevkit/neogeo.h>
#include <ngdevkit/ng-fix.h>

/* Tile indices produced by tiles.py. ASCII glyphs live at 0x00-0x7F. */
#define TILE_BG      0x80   /* opaque, colour 1 */
#define TILE_WINDOW  0x81   /* fully transparent - the hole */
#define TILE_BORDER  0x82   /* opaque, colour 2 */

#define PAL_MAIN     0

/* Neo Geo colour: bit15 dark, 14-12 low bits of R/G/B, 11-8 R, 7-4 G, 3-0 B */
#define C_TRANSPARENT 0x8000
#define C_BACKGROUND  0x0125   /* muted blue  - colour 1 */
#define C_BORDER      0x0f80   /* orange      - colour 2 */
#define C_CHECK       0x0223   /* dim slate   - colour 3 */
#define C_TEXT        0x0fff   /* white       - colour 15 */
#define C_BACKDROP    0x00f0   /* bright green - palette entry 0xFFF */

/* The backdrop is the last entry of palette RAM. linebuffer.v forces the
   palette address to all ones while clearing, so this is what a transparent
   fix pixel resolves to when nothing has written the line buffer. */
#define PALETTE_BACKDROP_INDEX 0xFFF

/* Window rectangle, in fix-map tiles (40 wide x 32 tall, ~28 rows visible) */
#define WIN_X0  11
#define WIN_X1  28
#define WIN_Y0   9
#define WIN_Y1  15

static void fill_rect(u8 x0, u8 y0, u8 x1, u8 y1, u8 palette, u16 tile) {
    u16 val = (palette << 12) | tile;
    for (u8 x = x0; x <= x1; x++) {
        /* Fix map is column-major: ADDR_FIXMAP + (x * 32) + y */
        *REG_VRAMADDR = ADDR_FIXMAP + (x << 5) + y0;
        *REG_VRAMMOD  = 1;
        for (u8 y = y0; y <= y1; y++) *REG_VRAMRW = val;
    }
}

static void setup_palette(void) {
    MMAP_PALBANK1[0]  = C_TRANSPARENT;
    MMAP_PALBANK1[1]  = C_BACKGROUND;
    MMAP_PALBANK1[2]  = C_BORDER;
    MMAP_PALBANK1[3]  = C_CHECK;
    MMAP_PALBANK1[15] = C_TEXT;
    MMAP_PALBANK1[PALETTE_BACKDROP_INDEX] = C_BACKDROP;
}

int main(void) {
    setup_palette();

    /* Everything opaque. No pixel reaches the sprite path except the window. */
    ng_cls_args(PAL_MAIN, TILE_BG);

    /* Frame, then punch the transparent window inside it. */
    fill_rect(WIN_X0 - 1, WIN_Y0 - 1, WIN_X1 + 1, WIN_Y1 + 1, PAL_MAIN, TILE_BORDER);
    fill_rect(WIN_X0,     WIN_Y0,     WIN_X1,     WIN_Y1,     PAL_MAIN, TILE_WINDOW);

    ng_center_text(2,  PAL_MAIN, "NEOFORGE FIX-LAYER TEST");
    ng_center_text(4,  PAL_MAIN, "THIS TEXT AND BACKGROUND ARE");
    ng_center_text(5,  PAL_MAIN, "OPAQUE FIX TILES - NO SPRITES");
    ng_center_text(6,  PAL_MAIN, "AND NO C ROM DATA IN THIS CART");

    ng_center_text(18, PAL_MAIN, "THE WINDOW ABOVE IS TRANSPARENT");
    ng_center_text(19, PAL_MAIN, "FIX - IT SHOWS THE SPRITE PATH");

    ng_center_text(21, PAL_MAIN, "GREEN = LINE BUFFER IS CLEAN");
    ng_center_text(22, PAL_MAIN, "ANYTHING ELSE = IT IS NOT");

    ng_center_text(25, PAL_MAIN, "SEE DOCS/OPEN-QUESTIONS.MD  Q1");

    for (;;) {}
    return 0;
}
