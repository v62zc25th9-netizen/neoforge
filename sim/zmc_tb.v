// SPDX-License-Identifier: GPL-3.0-or-later
// NeoForge — self-checking testbench for the M1 bankswitching half of NEO-ZMC2.
//
// Device under test: zmc, from neogeodev/NeoGeoFPGA-sim, Cartridge/zmc.v,
// GPL-3.0. NeoForge does not modify it — this file drives it and checks what
// comes out.
//
// Why this file exists
// --------------------
// neo_zmc2.v names two halves. The pixel half, zmc2_dot, is implemented and
// NeoForge already has a passing testbench for it. The other half appears in
// neo_zmc2.v only as a commented-out instantiation:
//
//     //zmc2_zmc ZMC2ZMC(SDRD0, SDA_L, SDA_U, MA);
//
// No module named zmc2_zmc exists in the repository. Cartridge/zmc.v has the
// identical port list and is instantiated in mvs_cha.v with exactly those
// signals, so we treat it as the same logic under a different name.
// [UNVERIFIED] — that identification is from the port list and usage, not from
// a datasheet or an upstream statement.
//
// What the block does
// -------------------
// It is the Z80's mapper. The Z80 has 16 address lines and the M1 ROM is
// larger than 64 KB, so four bank registers redirect four windows of Z80
// address space into an 11-bit upper address, MA[21:11]:
//
//   Z80 range     window   register   MA composition            max reach
//   0000-7FFF     32 KB    (none)     {6'b0, A[15:11]}          pass-through
//   8000-BFFF     16 KB    RANGE_3    {RANGE_3, A[13:11]}       4 MB
//   C000-DFFF      8 KB    RANGE_2    {1'b0, RANGE_2, A[12:11]} 2 MB
//   E000-EFFF      4 KB    RANGE_1    {2'b0, RANGE_1, A[11]}    1 MB
//   F000-F7FF      2 KB    RANGE_0    {3'b0, RANGE_0}           512 KB
//
// A bank is programmed by a Z80 I/O read: SDA_L (the low address bits) picks
// the register and SDA_U (the high address byte, which on a Z80 `IN A,(n)`
// carries the accumulator) supplies the value. The register latches on the
// rising edge of SDRD0.

`timescale 1ns/1ns

module zmc_tb;

    reg         SDRD0 = 1'b1;
    reg  [1:0]  SDA_L = 2'b00;
    reg  [15:8] SDA_U = 8'h00;

    wire [21:11] MA_REF;    // the reference implementation
    wire [21:11] MA_FIX;    // the same logic with one width corrected

    integer errors = 0;
    integer checks = 0;

    zmc       REF (SDRD0, SDA_L, SDA_U, MA_REF);
    zmc_fixed FIX (SDRD0, SDA_L, SDA_U, MA_FIX);

    // ---------------------------------------------------------------------
    task chk;
        input [255:0] name;
        input [10:0]  got, want;
        begin
            checks = checks + 1;
            if (got !== want) begin
                errors = errors + 1;
                $display("  FAIL %0s: got %h want %h", name, got, want);
            end
        end
    endtask

    // Program one bank register, on both instances at once.
    task bank;
        input [1:0] idx;
        input [7:0] value;
        begin
            SDA_L = idx;
            SDA_U = value;
            SDRD0 = 1'b0; #20;
            SDRD0 = 1'b1; #20;    // latches here
        end
    endtask

    // Present a Z80 address and return the full byte address the M1 ROM sees.
    function [21:0] flat;
        input [10:0] ma;
        input [15:0] addr;
        begin
            flat = {ma, addr[10:0]};
        end
    endfunction

    reg [15:0] a;

    initial begin
        $dumpfile("zmc.vcd");
        $dumpvars(0, zmc_tb);

        $display("");
        $display("NEO-ZMC2, M1 bankswitching half (zmc2_zmc / zmc)");
        $display("========================================");
        $display("");

        // ---- Test 1: the unbanked window ---------------------------------
        // 0000-7FFF passes straight through. This is the whole reason a small
        // Z80 program needs no mapper at all.
        $display("Test 1 - 0000-7FFF passes through unmapped");
        for (a = 16'h0000; a < 16'h8000; a = a + 16'h0800) begin
            SDA_U = a[15:8]; #1;
            chk("passthrough ref", MA_REF, {6'b000000, a[15:11]});
            chk("passthrough fix", MA_FIX, {6'b000000, a[15:11]});
            if (flat(MA_REF, a) !== {6'b0, a}) begin
                errors = errors + 1;
                $display("  FAIL identity at %04h -> %06h", a, flat(MA_REF, a));
            end
        end
        $display("  0000-7FFF maps to itself, both models. 32 KB reachable");
        $display("  with no bank register programmed.");
        $display("");

        // ---- Test 2: the bank registers are one bit wide -----------------
        // zmc.v declares:   wire BANKSEL = SDA_U[15:8];
        // BANKSEL is a scalar. The eight-bit right-hand side is truncated to
        // its least significant bit, so only SDA_U[8] survives and every bank
        // register can hold only 0 or 1.
        $display("Test 2 - the reference truncates the bank value");
        bank(2'd3, 8'h5A);          // 0101_1010, bit 0 of the slice = 0
        a = 16'h8000; SDA_U = a[15:8]; #1;
        $display("  wrote RANGE_3 = 5a");
        $display("    reference MA = %h  -> bank %h", MA_REF, MA_REF >> 3);
        $display("    corrected MA = %h  -> bank %h", MA_FIX, MA_FIX >> 3);
        chk("ref keeps only bit 8", MA_REF, {8'h00, 3'b000});
        chk("fix keeps all eight",  MA_FIX, {8'h5A, 3'b000});

        bank(2'd3, 8'h01);          // bit 0 set
        a = 16'h8000; SDA_U = a[15:8]; #1;
        $display("  wrote RANGE_3 = 01");
        $display("    reference MA = %h  -> bank %h", MA_REF, MA_REF >> 3);
        chk("ref passes bit 8", MA_REF, {8'h01, 3'b000});
        $display("  => the reference can select bank 0 or bank 1, nothing else.");
        $display("     This is a width bug in NeoGeoFPGA-sim, not the silicon.");
        $display("     Every check below therefore runs against the corrected");
        $display("     model. See docs/serializer.md.");
        $display("");

        // ---- Test 3: window arithmetic -----------------------------------
        $display("Test 3 - each window lands where the bank says");
        $display("  reg     bank  Z80 addr  ->  M1 byte addr   expected");
        $display("  ------  ----  --------      ------------   ------------");

        bank(2'd3, 8'h5A);  a = 16'h9ABC; SDA_U = a[15:8]; #1;
        $display("  RANGE_3   5a     %04h    ->     %06h       %06h",
                 a, flat(MA_FIX, a), 22'h5A * 22'h4000 + (a - 16'h8000));
        chk("range3", MA_FIX, {8'h5A, 3'b011});

        bank(2'd2, 8'h33);  a = 16'hCDEF; SDA_U = a[15:8]; #1;
        $display("  RANGE_2   33     %04h    ->     %06h       %06h",
                 a, flat(MA_FIX, a), 22'h33 * 22'h2000 + (a - 16'hC000));
        chk("range2", MA_FIX, {1'b0, 8'h33, 2'b01});

        bank(2'd1, 8'h77);  a = 16'hEABC; SDA_U = a[15:8]; #1;
        $display("  RANGE_1   77     %04h    ->     %06h       %06h",
                 a, flat(MA_FIX, a), 22'h77 * 22'h1000 + (a - 16'hE000));
        chk("range1", MA_FIX, {2'b00, 8'h77, 1'b1});

        bank(2'd0, 8'h11);  a = 16'hF123; SDA_U = a[15:8]; #1;
        $display("  RANGE_0   11     %04h    ->     %06h       %06h",
                 a, flat(MA_FIX, a), 22'h11 * 22'h0800 + (a - 16'hF000));
        chk("range0", MA_FIX, {3'b000, 8'h11});
        $display("");

        // ---- Test 4: the windows are independent -------------------------
        $display("Test 4 - the four registers do not disturb each other");
        bank(2'd0, 8'hAA); bank(2'd1, 8'hBB);
        bank(2'd2, 8'hCC); bank(2'd3, 8'hDD);
        a = 16'hF000; SDA_U = a[15:8]; #1; chk("r0 after all", MA_FIX, {3'b000, 8'hAA});
        a = 16'hE000; SDA_U = a[15:8]; #1; chk("r1 after all", MA_FIX, {2'b00, 8'hBB, 1'b0});
        a = 16'hC000; SDA_U = a[15:8]; #1; chk("r2 after all", MA_FIX, {1'b0, 8'hCC, 2'b00});
        a = 16'h8000; SDA_U = a[15:8]; #1; chk("r3 after all", MA_FIX, {8'hDD, 3'b000});
        $display("  four registers, four windows, no interaction.");
        $display("");

        // ---- Test 5: F800-FFFF aliases the F000 window -------------------
        // MA for the top window is {3'b000, RANGE_0} and ignores A11, so
        // F800-FFFF produces the same MA as F000-F7FF. On real hardware the
        // Z80's work RAM is decoded up there and never reaches this chip, so
        // the alias is invisible — but a cartridge that maps ROM into F800
        // would find it mirrored.
        $display("Test 5 - F800-FFFF aliases F000-F7FF");
        bank(2'd0, 8'h11);
        a = 16'hF123; SDA_U = a[15:8]; #1;
        chk("F123", MA_FIX, {3'b000, 8'h11});
        a = 16'hF923; SDA_U = a[15:8]; #1;
        chk("F923 aliases", MA_FIX, {3'b000, 8'h11});
        $display("  both map to MA=%h. A11 is not used in this window.", MA_FIX);
        $display("  Invisible in practice: Z80 RAM is decoded at F800 on the");
        $display("  motherboard and never reaches the cartridge.");
        $display("");

        // ---- Test 6: power-on state --------------------------------------
        // zmc.v carries the comment "// Initialize ?". The registers have no
        // reset. This is not a modelling artefact to paper over: it is a real
        // constraint on cartridge software.
        $display("Test 6 - the bank registers have no reset");
        $display("  zmc.v comments this as an open question and models it as X.");
        $display("  Consequence for cartridge software: a Z80 program must");
        $display("  program all four registers before executing from any");
        $display("  banked window, or stay entirely inside 0000-7FFF.");
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


// ---------------------------------------------------------------------------
// zmc_fixed — NeoForge's corrected model.
//
// Derived from NeoGeoFPGA-sim's Cartridge/zmc.v (GPL-3.0), which is why this
// file is GPL-3.0-or-later. Exactly one line differs:
//
//     reference:  wire       BANKSEL = SDA_U[15:8];   // scalar - truncates
//     here:       wire [7:0] BANKSEL = SDA_U[15:8];
//
// Everything else, including the comments' claimed window sizes and the lack
// of a reset, is preserved so that this stays a faithful model of the chip
// rather than an improvement of it.
// ---------------------------------------------------------------------------
module zmc_fixed(
    input        SDRD0,
    input  [1:0] SDA_L,
    input [15:8] SDA_U,
    output [21:11] MA
);

    wire [7:0] BANKSEL = SDA_U[15:8];

    reg [7:0] RANGE_0;      // 2 KB window,  reaches 512 KB
    reg [7:0] RANGE_1;      // 4 KB window,  reaches 1 MB
    reg [7:0] RANGE_2;      // 8 KB window,  reaches 2 MB
    reg [7:0] RANGE_3;      // 16 KB window, reaches 4 MB

    assign MA = SDA_U[15] ?
                    ~SDA_U[14] ?
                        {RANGE_3, SDA_U[13:11]} :                // 8000-BFFF
                        ~SDA_U[13] ?
                            {1'b0, RANGE_2, SDA_U[12:11]} :      // C000-DFFF
                            ~SDA_U[12] ?
                                {2'b00, RANGE_1, SDA_U[11]} :    // E000-EFFF
                                {3'b000, RANGE_0}                // F000-F7FF
                  : {6'b000000, SDA_U[15:11]};                   // 0000-7FFF

    always @(posedge SDRD0)
        case (SDA_L)
            0: RANGE_0 <= BANKSEL;
            1: RANGE_1 <= BANKSEL;
            2: RANGE_2 <= BANKSEL;
            3: RANGE_3 <= BANKSEL;
        endcase

endmodule
