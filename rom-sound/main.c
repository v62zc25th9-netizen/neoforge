// SPDX-License-Identifier: MIT
/*
 * NeoForge V ROM test.
 *
 * A cartridge supplies five ROMs, and they are five separate jobs the board
 * has to do:
 *
 *   P  68k program        exercised by every ROM we have written
 *   S  fix tiles          exercised heavily by the fix-layer test
 *   M  Z80 program        exercised since we started building our own
 *   C  sprite graphics    exercised, barely - one tile
 *   V  ADPCM samples      never exercised at all
 *
 * The V ROM has been 512 KB of zeroes in everything we have built. That is a
 * gap worth closing before anyone burns an EPROM, because the V ROM is a
 * cartridge function with its own address and data lines across the connector
 * and its own decode logic behind them - on PROGBK1, a 74LS139. See
 * docs/prom-banking.md.
 *
 * The YM2610 lives on the motherboard and is not ours to doubt. What this
 * tests is the path from cartridge V ROM to that chip. If a board cannot
 * serve those reads, every game is silent, and nothing else we have built
 * would notice.
 *
 * WHAT THIS PROVES WHERE
 *
 *   In an emulator: that our V ROM is correctly constructed - ADPCM-A
 *   encoding, sample offsets, the map vromtool generates. Those are real
 *   build-correctness questions and an emulator can answer them, which is
 *   more than GnGeo could do for the fix-layer test.
 *
 *   On hardware: that the cartridge can actually serve V ROM reads. Only
 *   silicon answers that, and only once our own board is serving them -
 *   roadmap Phase 7. Until then a donor cart tests the ROM image, not the
 *   board.
 *
 * It plays on its own, every two seconds, with no controller needed - so it
 * can be tested in the time it takes to plug a flash cart in.
 */

#include <ngdevkit/neogeo.h>
#include <ngdevkit/ng-fix.h>
#include <ngdevkit/ng-video.h>

/* The 68k talks to the Z80 by writing a command byte here. */
#define REG_SOUND ((volatile u8*)0x320000)

#define SND_RESET_DRIVER  3    /* reserved, handled inside nullsound */
#define SND_PLAY_CHIRP    4    /* ours - see sound-driver.s          */

/* Tiles from ../rom/tiles.py. ASCII glyphs occupy 0x00-0x7F. */
#define TILE_BG   0x80
#define PAL_MAIN  0

#define C_TRANSPARENT 0x8000
#define C_BACKGROUND  0x0125   /* colour 1  - muted blue */
#define C_TEXT        0x0fff   /* colour 15 - white      */

#define PLAY_FRAMES   120      /* ~2 seconds at 60 Hz */
#define SETTLE_FRAMES  60      /* let the driver come up before the first play */

static void setup_palette(void) {
    MMAP_PALBANK1[0]  = C_TRANSPARENT;
    MMAP_PALBANK1[1]  = C_BACKGROUND;
    MMAP_PALBANK1[15] = C_TEXT;
}

/* Three digits, no stdio. printf would pull a formatter into the P ROM for
   the sake of a counter. */
static void put_count(u8 x, u8 y, u16 n) {
    char buf[4];
    buf[0] = '0' + (n / 100) % 10;
    buf[1] = '0' + (n / 10) % 10;
    buf[2] = '0' + n % 10;
    buf[3] = '\0';
    ng_text(x, y, PAL_MAIN, buf);
}

int main(void) {
    /* Reset the sound driver first. Until this lands the Z80 is idling in
       RAM waiting for the 68k, and any command we send is ignored. */
    *REG_SOUND = SND_RESET_DRIVER;

    setup_palette();
    ng_cls_args(PAL_MAIN, TILE_BG);

    ng_center_text(2,  PAL_MAIN, "NEOFORGE V ROM TEST");

    ng_center_text(5,  PAL_MAIN, "PLAYS ONE ADPCM-A SAMPLE FROM THE");
    ng_center_text(6,  PAL_MAIN, "CARTRIDGE V ROM, EVERY TWO SECONDS");
    ng_center_text(7,  PAL_MAIN, "NO CONTROLLER NEEDED");

    ng_center_text(10, PAL_MAIN, "YOU SHOULD HEAR A CLICK, THEN TWO");
    ng_center_text(11, PAL_MAIN, "TONES AN OCTAVE APART - 440 AND 880");

    ng_center_text(14, PAL_MAIN, "SOUND      = V ROM PATH WORKS");
    ng_center_text(15, PAL_MAIN, "SILENCE    = IT DOES NOT, OR THE");
    ng_center_text(16, PAL_MAIN, "             Z80 DRIVER NEVER STARTED");
    ng_center_text(17, PAL_MAIN, "COUNTER STUCK = THE 68K IS WEDGED");

    ng_center_text(20, PAL_MAIN, "CHECK YOUR VOLUME BEFORE REPORTING");
    ng_center_text(21, PAL_MAIN, "SILENCE. IT IS THE USUAL CAUSE.");

    ng_text(13, 24, PAL_MAIN, "PLAYS: ");
    ng_center_text(26, PAL_MAIN, "ROM-SOUND/README.MD");

    u16 frames = 0;
    u16 plays  = 0;
    put_count(20, 24, 0);

    /* Give the driver time to initialise before the first command. */
    for (u16 i = 0; i < SETTLE_FRAMES; i++) ng_wait_vblank();

    for (;;) {
        if (frames == 0) {
            *REG_SOUND = SND_PLAY_CHIRP;
            plays++;
            put_count(20, 24, plays);
        }
        ng_wait_vblank();
        if (++frames >= PLAY_FRAMES) frames = 0;
    }
    return 0;
}
