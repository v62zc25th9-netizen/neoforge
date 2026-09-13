// SPDX-License-Identifier: GPL-3.0-or-later
//
// NeoForge - fx68k behind NeoGeoFPGA-sim's tg68 interface.
//
// The model instantiates `tg68`, which is VHDL, so Icarus Verilog cannot
// simulate the system at all. This module has the same name and the same port
// list, so nothing in CPUs/cpu_68k.v changes - but inside it is fx68k, Jorge
// Cwik's cycle-accurate 68000 in SystemVerilog.
//
// That is an upgrade, not a workaround. TG68K is not cycle-exact; fx68k is
// microcode-accurate. For a study of bus timing that difference is the whole
// point. See docs/simulation-harness.md.
//
// Requires Verilator 5 (`--timing`), which honours the `#delay` annotations on
// the ROM models. Verilator 4 ignores delays entirely and would silently
// produce a meaningless answer.
//
// fx68k is Copyright (c) 2018,2021 Jorge Cwik and is fetched, not vendored.

`default_nettype none

module tg68 (
    input  wire        clk,        // CLK_68KCLK - the 12 MHz 68000 clock
    input  wire        clk_2x,     // CLK_24M - added by our patch, see README
    input  wire        reset,      // active LOW (nRESET)
    input  wire        clkena_in,
    input  wire [15:0] data_in,
    input  wire  [2:0] IPL,        // active low, {1'b1, IPL1, IPL0}
    input  wire        dtack,      // active LOW (nDTACK)
    output wire [31:0] addr,
    output wire [15:0] data_out,
    output wire        as,         // active LOW
    output wire        uds,        // active LOW
    output wire        lds,        // active LOW
    output wire        rw,         // 1 = read
    output wire [15:0] REG_D6      // debug only in the original; unused here
);

    // ---------------------------------------------------------------------
    // Clock phases
    //
    // fx68k does not take a bare 68000 clock. It runs from a faster clock and
    // is told which half of the 68000 cycle is coming next, via enPhi1 and
    // enPhi2. On this system the faster clock already exists: CLK_24M is
    // exactly twice CLK_68KCLK.
    //
    // *** THIS IS THE PART THAT IS NOT YET VERIFIED. *** The two enables must
    // land in the correct phase relationship with CLK_68KCLK, because the
    // cartridge's wait-state logic is keyed to that clock. Alternating them
    // gives the right *rate*; whether the alignment is right is exactly what
    // bring-up has to establish, and getting it wrong produces a machine that
    // almost works, which is the worst kind. See README.md.
    // ---------------------------------------------------------------------
    reg phi = 1'b0;
    reg clk_d = 1'b0;

    always @(posedge clk_2x) begin
        clk_d <= clk;
        // Re-sync the phase to the 68000 clock's rising edge rather than
        // free-running, so the two cannot drift apart over a long run.
        if (clk && !clk_d)
            phi <= 1'b0;
        else
            phi <= ~phi;
    end

    wire enPhi1 = (phi == 1'b0);
    wire enPhi2 = (phi == 1'b1);

    // ---------------------------------------------------------------------
    // Reset. tg68's `reset` is active low; fx68k's extReset is active high.
    // pwrUp must be asserted with reset on a cold start and only then.
    // ---------------------------------------------------------------------
    wire extReset = ~reset;

    reg  pwr_seen = 1'b0;
    wire pwrUp = ~pwr_seen & extReset;
    always @(posedge clk_2x)
        if (!extReset) pwr_seen <= 1'b1;

    // ---------------------------------------------------------------------
    // Bus
    // ---------------------------------------------------------------------
    wire [23:1] eab;
    assign addr = {8'h00, eab, 1'b0};   // tg68 presented a 32-bit address;
                                        // cpu_68k.v only uses [23:1]

    fx68k CPU (
        .clk        (clk_2x),
        .HALTn      (1'b1),
        .extReset   (extReset),
        .pwrUp      (pwrUp),
        .enPhi1     (enPhi1),
        .enPhi2     (enPhi2),

        .eRWn       (rw),
        .ASn        (as),
        .LDSn       (lds),
        .UDSn       (uds),
        .E          (),
        .VMAn       (),

        .FC0        (),
        .FC1        (),
        .FC2        (),
        .BGn        (),
        .oRESETn    (),
        .oHALTEDn   (),

        .DTACKn     (dtack),
        .VPAn       (1'b1),      // no 6800-style peripherals on this bus
        .BERRn      (1'b1),      // nothing generates a bus error here
        .BRn        (1'b1),      // no other bus master
        .BGACKn     (1'b1),

        .IPL0n      (IPL[0]),
        .IPL1n      (IPL[1]),
        .IPL2n      (IPL[2]),

        .iEdb       (data_in),
        .oEdb       (data_out),
        .eab        (eab)
    );

    assign REG_D6 = 16'h0000;   // debug output in the original, unused

endmodule

`default_nettype wire
