// SPDX-License-Identifier: GPL-3.0-or-later
/*
 * NeoForge fix-layer test ROM.
 *
 * Tests the display path a serializer-less AES cartridge would use, and -
 * importantly - proves that the test is capable of failing.
 *
 * Background, from docs/open-questions.md Q1:
 *
 *   Fix graphics run from the S ROM straight to the cartridge edge connector
 *   and never touch the sprite serializer. In NEO-B1 an *opaque* fix pixel
 *   beats the sprite line buffers outright. A *transparent* fix pixel falls
 *   through to the line buffer instead - and linebuffer.v forces the palette
 *   address to all ones during clearing writes, ignoring GAD/GBD, so a line
 *   buffer nothing has written resolves to the backdrop.
 *
 * The screen is opaque fix everywhere except one framed rectangle, which is
 * transparent fix: a controlled window onto the sprite line buffer. The
 * backdrop (palette entry 0xFFF) is set to green.
 *
 * THE ALTERNATION IS THE POINT.
 *
 * Every two seconds the ROM enables and disables a screen-filling sprite:
 *
 *   sprites OFF -> nothing writes the line buffer -> window is GREEN
 *   sprites ON  -> the sprite path writes the line buffer -> window is RED
 *
 * On an ordinary AES the window must alternate. That is the positive control:
 * it demonstrates the window can register sprite activity at all. Without it a
 * green window would be worthless, because "the sprite path is quiet" and "this
 * ROM cannot see the sprite path" look identical.
 *
 * On a cartridge with no serializer and DOTA/DOTB tied low, the window should
 * stay GREEN IN BOTH PHASES. The difference between those two behaviours is
 * precisely Q1's answer.
 *
 * The C ROMs hold exactly one solid tile - the minimum the control needs.
 * Everything else in them is zero.
 */

#include <ngdevkit/neogeo.h>
#include <ngdevkit/ng-fix.h>
#include <ngdevkit/ng-video.h>

/* Tiles from tiles.py. ASCII glyphs occupy 0x00-0x7F. */
#define TILE_BG      0x80
#define TILE_WINDOW  0x81
#define TILE_BORDER  0x82

#define PAL_MAIN     0

/* Neo Geo colour: bit15 dark, 14-12 low bits of R/G/B, 11-8 R, 7-4 G, 3-0 B */
#define C_TRANSPARENT 0x8000
#define C_BACKGROUND  0x0125   /* colour 1  - muted blue   */
#define C_BORDER      0x0f80   /* colour 2  - orange       */
#define C_SPRITE      0x0f00   /* colour 4  - bright red   */
#define C_TEXT        0x0fff   /* colour 15 - white        */
#define C_BACKDROP    0x00f0   /* palette 0xFFF - green    */

#define PALETTE_BACKDROP_INDEX 0xFFF

/* Window rectangle, in fix-map tiles */
#define WIN_X0  11
#define WIN_X1  28
#define WIN_Y0   8
#define WIN_Y1  15

/* Sprites: 20 columns of 16px covers the 320px screen; 32 tiles is the
   maximum height and spans the visible 224 lines whatever the alignment. */
#define SPR_COUNT   20
#define SPR_TILES   32
#define SPR_HEIGHT  32
/* SCB3 Y field: actual screen position is 496 - Y, so 496 is the top border */
#define SPR_Y      496

#define TOGGLE_FRAMES 120      /* ~2 seconds at 60 Hz */

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
    MMAP_PALBANK1[4]  = C_SPRITE;
    MMAP_PALBANK1[15] = C_TEXT;
    MMAP_PALBANK1[PALETTE_BACKDROP_INDEX] = C_BACKDROP;
}

/* Every sprite off: SCB3 size field 0 means no tiles are drawn.
   Done for all 448 SCB3 slots so we start from a known state rather than
   inheriting whatever the BIOS left in VRAM. */
static void sprites_clear_all(void) {
    *REG_VRAMADDR = ADDR_SCB3;
    *REG_VRAMMOD  = 1;
    for (u16 i = 0; i < 0x200; i++) *REG_VRAMRW = 0;
}

/* Tilemaps, zoom and X positions. Written once; the toggle only touches
   SCB3, which keeps VRAM traffic low. */
static void sprites_setup(void) {
    for (u8 i = 0; i < SPR_COUNT; i++) {
        *REG_VRAMADDR = ADDR_SCB1 + (i * 64);
        *REG_VRAMMOD  = 1;
        for (u8 t = 0; t < SPR_TILES; t++) {
            *REG_VRAMRW = 0;                  /* tile 0 - our one solid tile */
            *REG_VRAMRW = (PAL_MAIN << 8);    /* palette, no flip            */
        }
        /* SCB2/3/4 sit 0x200 apart, so one MOD walks all three */
        *REG_VRAMMOD  = 0x200;
        *REG_VRAMADDR = ADDR_SCB2 + i;
        *REG_VRAMRW = 0x0FFF;                 /* SCB2: no shrinking          */
        *REG_VRAMRW = 0;                      /* SCB3: size 0 = off for now  */
        *REG_VRAMRW = ((i * 16) << 7);        /* SCB4: X                     */
    }
}

static void sprites_enable(u8 on) {
    *REG_VRAMADDR = ADDR_SCB3;
    *REG_VRAMMOD  = 1;
    for (u8 i = 0; i < SPR_COUNT; i++)
        *REG_VRAMRW = on ? ((SPR_Y << 7) | SPR_HEIGHT) : 0;
}

int main(void) {
    setup_palette();
    sprites_clear_all();
    sprites_setup();

    ng_cls_args(PAL_MAIN, TILE_BG);
    fill_rect(WIN_X0 - 1, WIN_Y0 - 1, WIN_X1 + 1, WIN_Y1 + 1, PAL_MAIN, TILE_BORDER);
    fill_rect(WIN_X0,     WIN_Y0,     WIN_X1,     WIN_Y1,     PAL_MAIN, TILE_WINDOW);

    ng_center_text(1,  PAL_MAIN, "NEOFORGE FIX-LAYER TEST");
    ng_center_text(3,  PAL_MAIN, "TEXT AND BACKGROUND ARE OPAQUE FIX");
    ng_center_text(4,  PAL_MAIN, "C ROM HOLDS ONE TILE, FOR THE TEST");

    ng_center_text(18, PAL_MAIN, "THE WINDOW IS TRANSPARENT FIX - IT");
    ng_center_text(19, PAL_MAIN, "SHOWS THE SPRITE LINE BUFFER");

    ng_center_text(21, PAL_MAIN, "OFF SHOULD BE GREEN, ON SHOULD BE RED");
    ng_center_text(22, PAL_MAIN, "GREEN IN BOTH = NO SPRITE PATH AT ALL");

    ng_center_text(26, PAL_MAIN, "DOCS/OPEN-QUESTIONS.MD  Q1");

    u8  on = 0;
    u16 frames = 0;
    sprites_enable(0);
    ng_text(14, 24, PAL_MAIN, "SPRITES: OFF");

    for (;;) {
        ng_wait_vblank();
        if (++frames >= TOGGLE_FRAMES) {
            frames = 0;
            on = !on;
            sprites_enable(on);
            ng_text(14, 24, PAL_MAIN, on ? "SPRITES: ON " : "SPRITES: OFF");
        }
    }
    return 0;
}
