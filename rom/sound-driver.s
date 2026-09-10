;;; SPDX-License-Identifier: LGPL-3.0-or-later
;;;
;;; NeoForge - minimal Z80 sound driver
;;;
;;; Derived from ngdevkit-examples' base-sound-driver.s, Copyright (c)
;;; 2026 Damien Ciabrini, LGPL-3.0-or-later. This file inherits that
;;; licence - it is the one file under rom/ that is not MIT. See
;;; ../LICENSE.md.
;;;
;;; This ROM makes no sound. It needs an M ROM anyway, because the BIOS
;;; expects a valid Z80 program there and talks to it during boot. So this
;;; provides the command jump table the BIOS needs and nothing else, linked
;;; against nullsound-aes.lib, which ships with ngdevkit.
;;;
;;; Why not just borrow one
;;; -----------------------
;;; Earlier builds copied base-sound-driver.ihx out of an ngdevkit-examples
;;; checkout. That made the build unreproducible for anyone who did not have
;;; that checkout, and put a third-party binary in our release. This file
;;; removes both problems: nullsound-aes.lib is part of the toolchain, so a
;;; plain `make` now works from a clean clone.
;;;
;;; Why -aes
;;; --------
;;; nullsound ships two variants. They differ only in the frequency tables,
;;; which are computed from the audio clock, and AES and MVS clock the YM2610
;;; differently. Nothing here plays a note, so it makes no audible difference
;;; - but this is an AES project and linking the MVS variant into an AES
;;; cartridge would be a small lie in the build.

        .include "helpers.inc"

        .area   CODE


;;; The BIOS reaches the driver through this table. nullsound's NMI handler
;;; intercepts commands 1, 2 and 3 before the table is consulted; everything
;;; else is queued and dispatched through it.
;;;
;;; Entry 2 is not a command handler. Command 2 is "reset the driver and play
;;; the eye-catcher music", and nullsound implements it by initialising the
;;; driver and then *calling entry 2 as a subroutine*, with the main loop as
;;; the return address. The music is expected to live in the game ROM, which
;;; is why nullsound cannot provide it.
;;;
;;; We have no music, so entry 2 must return cleanly and do nothing. It
;;; deliberately does not jump to snd_command_unused: that ends in `retn`,
;;; which is correct inside an NMI but wrong here, because by this point the
;;; driver has already returned from the NMI. A plain `ret` is what the
;;; caller expects.

cmd_jmptable::
        jp      snd_command_unused                      ; 00 unused
        jp      snd_command_01_prepare_for_rom_switch   ; 01 wait in RAM
        jp      no_eye_catcher                          ; 02 post-init hook
        jp      snd_command_03_reset_driver             ; 03 reset driver
        init_unused_cmd_jmptable                        ; 04..7f -> unused

;;; Must be defined *after* the padding macro: the macro sizes itself from
;;; the distance back to cmd_jmptable, so anything placed in between would
;;; silently shorten the table.
no_eye_catcher:
        ret
