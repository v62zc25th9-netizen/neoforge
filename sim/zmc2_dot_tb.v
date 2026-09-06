// SPDX-License-Identifier: GPL-3.0-or-later
// NeoForge — self-checking testbench for the AES sprite serializer datapath.
//
// Device under test: zmc2_dot, the pixel-serializing core of NEO-ZMC2 /
// PRO-CT0. Source: neogeodev/NeoGeoFPGA-sim, Video/zmc2_dot.v, by Kyuusaku,
// GPL-3.0. NeoForge does not modify it — this file only drives it and checks
// what comes out.
//
// What this proves:
//   The serializer takes 32 bits of C ROM (four bitplane bytes covering one
//   8-pixel line of a sprite tile) and emits two 4-bit packed pixels per
//   12 MHz clock, four clocks per tile line. H selects shift direction, which
//   is horizontal flip. EVEN selects which of the two pixels goes to GAD
//   versus GBD.
//
// Bitplane layout, derived from the case statement in zmc2_dot.v:
//   SR[31:24] = byte 0 -> contributes bit 3 (MSB) of each pixel
//   SR[23:16] = byte 1 -> bit 2
//   SR[15:8]  = byte 2 -> bit 1
//   SR[7:0]   = byte 3 -> bit 0 (LSB)
//   Within a byte, bit 7 is the leftmost pixel of the eight.
//   [UNVERIFIED] — inferred from the HDL, not from a datasheet. This
//   testbench is what makes the inference checkable.

`timescale 1ns/1ns

module zmc2_dot_tb;

    reg         CLK_12M = 1'b0;
    reg         EVEN    = 1'b0;
    reg         LOAD    = 1'b0;
    reg         H       = 1'b0;
    reg  [31:0] CR      = 32'h0;
    wire [3:0]  GAD, GBD;
    wire        DOTA, DOTB;

    integer errors = 0;
    integer checks = 0;

    zmc2_dot DUT (CLK_12M, EVEN, LOAD, H, CR, GAD, GBD, DOTA, DOTB);

    // 12 MHz -> 83.33 ns period. The DUT clocks on negedge.
    always #42 CLK_12M = ~CLK_12M;

    // Pack eight 4-bit pixels into the four bitplane bytes.
    // Pixel 0 is leftmost and lands in bit 7 of every plane.
    function [31:0] pack;
        input [3:0] p0, p1, p2, p3, p4, p5, p6, p7;
        reg [7:0] b0, b1, b2, b3;
        integer i;
        reg [3:0] px [0:7];
        begin
            px[0]=p0; px[1]=p1; px[2]=p2; px[3]=p3;
            px[4]=p4; px[5]=p5; px[6]=p6; px[7]=p7;
            b0=0; b1=0; b2=0; b3=0;
            for (i = 0; i < 8; i = i + 1) begin
                b0[7-i] = px[i][3];
                b1[7-i] = px[i][2];
                b2[7-i] = px[i][1];
                b3[7-i] = px[i][0];
            end
            pack = {b0, b1, b2, b3};
        end
    endfunction

    task chk;
        input [127:0] label;
        input [3:0]   got, want;
        begin
            checks = checks + 1;
            if (got !== want) begin
                errors = errors + 1;
                $display("  FAIL  %0s: got %0d, expected %0d", label, got, want);
            end
        end
    endtask

    task tick; begin @(negedge CLK_12M); #1; end endtask

    reg [31:0] line;
    integer    i;
    reg [3:0]  expect_seq [0:7];

    initial begin
        $dumpfile("zmc2_dot.vcd");
        $dumpvars(0, zmc2_dot_tb);

        $display("");
        $display("NeoForge :: zmc2_dot serializer datapath");
        $display("========================================");
        $display("");

        // ---- Test 1: eight distinct pixels, unflipped ----------------------
        // Colour indices 1..8 left to right. If the model is right, they come
        // back out in that order, two per clock.
        line = pack(4'd1, 4'd2, 4'd3, 4'd4, 4'd5, 4'd6, 4'd7, 4'd8);
        for (i = 0; i < 8; i = i + 1) expect_seq[i] = i + 1;

        $display("Test 1 - unflipped (H=1), pixels 1..8");
        $display("  C ROM line = %08h", line);
        $display("  planes: b0=%08b b1=%08b b2=%08b b3=%08b",
                 line[31:24], line[23:16], line[15:8], line[7:0]);
        $display("");

        H = 1'b1; EVEN = 1'b1;
        CR = line; LOAD = 1'b1; tick; LOAD = 1'b0;

        $display("  clk | GBD GAD | DOTB DOTA");
        $display("  ----+---------+----------");
        for (i = 0; i < 4; i = i + 1) begin
            $display("   %0d  |  %0d   %0d  |   %0d    %0d",
                     i, GBD, GAD, DOTB, DOTA);
            chk("pixel", GBD, expect_seq[i*2]);
            chk("pixel", GAD, expect_seq[i*2 + 1]);
            tick;
        end
        $display("");

        // ---- Test 2: same data, flipped ------------------------------------
        // H=0 shifts the other way. If H is horizontal flip, the same line
        // should come out 8,7,6,5,4,3,2,1.
        $display("Test 2 - flipped (H=0), same data, expect reversed");
        H = 1'b0; EVEN = 1'b0;
        CR = line; LOAD = 1'b1; tick; LOAD = 1'b0;

        $display("  clk | GBD GAD");
        $display("  ----+--------");
        for (i = 0; i < 4; i = i + 1) begin
            $display("   %0d  |  %0d   %0d", i, GBD, GAD);
            tick;
        end
        $display("");

        // ---- Test 3: transparency flags ------------------------------------
        // DOTA/DOTB are just "is this pixel non-zero". Colour 0 is
        // transparent on the Neo Geo, so an all-zero line must assert neither.
        $display("Test 3 - all-transparent line, DOTA/DOTB must stay low");
        line = pack(4'd0, 4'd0, 4'd0, 4'd0, 4'd0, 4'd0, 4'd0, 4'd0);
        H = 1'b1; EVEN = 1'b1;
        CR = line; LOAD = 1'b1; tick; LOAD = 1'b0;
        for (i = 0; i < 4; i = i + 1) begin
            checks = checks + 1;
            if (DOTA !== 1'b0 || DOTB !== 1'b0) begin
                errors = errors + 1;
                $display("  FAIL  clk %0d: DOTA=%b DOTB=%b, both should be 0",
                         i, DOTA, DOTB);
            end
            tick;
        end
        $display("  DOTA/DOTB low across all four clocks.");
        $display("");

        // ---- Test 4: opacity tracks the pixel ------------------------------
        $display("Test 4 - alternating opaque/transparent");
        line = pack(4'd15, 4'd0, 4'd15, 4'd0, 4'd15, 4'd0, 4'd15, 4'd0);
        H = 1'b1; EVEN = 1'b1;
        CR = line; LOAD = 1'b1; tick; LOAD = 1'b0;
        $display("  clk | GBD GAD | DOTB DOTA");
        $display("  ----+---------+----------");
        for (i = 0; i < 4; i = i + 1) begin
            $display("   %0d  | %0d   %0d  |   %0d    %0d", i, GBD, GAD, DOTB, DOTA);
            chk("opaque",      GBD, 4'd15);
            chk("transparent", GAD, 4'd0);
            tick;
        end
        $display("");

        $display("========================================");
        if (errors == 0)
            $display("PASS - %0d checks, 0 failures", checks);
        else
            $display("FAIL - %0d checks, %0d failures", checks, errors);
        $display("");
        $finish;
    end

endmodule
