// SPDX-License-Identifier: GPL-3.0-or-later
//
// NeoForge - whole-console testbench.
//
// Wires NeoGeoFPGA-sim's `neogeo` (the console) to `aes_cart` (the cartridge)
// and watches the 68000 bus. The model's own testbench_1 drives an *MVS* cart
// and leaves the AES one commented out; this is the AES equivalent.
//
// There is no clock to drive. neo_d0 contains the oscillator - `always #20.8
// CLK_24M = !CLK_24M` - so the console self-clocks, which is exactly why this
// harness needs Verilator 5's --timing. Under version 4, which ignores delay
// controls entirely, there would be no clock at all.
//
// FIRST MILESTONE, and what this is currently written to show: the 68000
// fetching its reset vector. If SSP and PC come back as 0010f300 / 00c04300
// then the clocks run, reset sequences, the bus arbitrates, and the BIOS ROM
// is loaded and oriented correctly - four things at once, from one result.
// Booting all the way is a later problem.

`timescale 1ns/1ns

module neoforge_tb;

    // ---- console <-> cartridge ------------------------------------------
    reg         nRESET_BTN;
    reg  [9:0]  P1_IN, P2_IN;
    reg  [7:0]  DIPSW;

    wire [15:0] M68K_DATA;
    wire [23:1] M68K_ADDR;
    wire        M68K_RW, nAS, nLDS, nUDS;
    wire [2:0]  LED_LATCH;
    wire [7:0]  LED_DATA;

    wire        CLK_68KCLKB, CLK_8M, CLK_4MB, CLK_12M, CLK_24M;
    wire        nRESET;

    wire        nROMOE, nSLOTCS, nROMOEL, nROMOEU;
    wire        nROMWAIT, nPWAIT0, nPWAIT1, PDTACK;
    wire        nPORTOEL, nPORTOEU, nPORTWEL, nPORTWEU, nPORTADRS;

    wire [7:0]  SDRAD, SDPAD;
    wire [9:8]  SDRA_L;
    wire [23:20] SDRA_U;
    wire        SDRMPX, nSDROE;
    wire [11:8] SDPA;
    wire        SDPMPX, nSDPOE;

    wire        nSDROM, nSDMRD, SDRD0, SDRD1;
    wire [15:0] SDA;
    wire [7:0]  SDD;

    wire [23:0] PBUS;
    wire        nVCS, S2H1, CA4, PCK1B, PCK2B;
    wire        EVEN, LOAD, H;
    wire [3:0]  GAD, GBD;
    wire [7:0]  FIXD_CART;
    wire        DOTA, DOTB;      // cart drives these; the console recomputes
                                 // them from GAD/GBD and does not take them.
                                 // See docs/serializer.md.

    wire [4:0]  CDA_U;
    wire        nCRDC, nCRDO, CARD_PIN_nWE, CARD_PIN_nREG;
    wire        nCD1 = 1'b1, nCD2 = 1'b1, nWP = 1'b1;   // no memory card

    wire [6:0]  VIDEO_R, VIDEO_G, VIDEO_B;
    wire        VIDEO_SYNC;

    // ---- the console -----------------------------------------------------
    neogeo NG (
        .nRESET_BTN(nRESET_BTN),
        .P1_IN(P1_IN), .P2_IN(P2_IN), .DIPSW(DIPSW),
        .M68K_DATA(M68K_DATA), .M68K_ADDR(M68K_ADDR),
        .M68K_RW(M68K_RW), .nAS(nAS), .nLDS(nLDS), .nUDS(nUDS),
        .LED_LATCH(LED_LATCH), .LED_DATA(LED_DATA),
        .CLK_68KCLKB(CLK_68KCLKB), .CLK_8M(CLK_8M), .CLK_4MB(CLK_4MB),
        .nROMOE(nROMOE), .nSLOTCS(nSLOTCS),
        .nROMWAIT(nROMWAIT), .nPWAIT0(nPWAIT0), .nPWAIT1(nPWAIT1),
        .PDTACK(PDTACK),
        .nPORTOEL(nPORTOEL), .nPORTOEU(nPORTOEU),
        .nPORTWEL(nPORTWEL), .nPORTWEU(nPORTWEU), .nPORTADRS(nPORTADRS),
        .SDRAD(SDRAD), .SDRA_L(SDRA_L), .SDRA_U(SDRA_U),
        .SDRMPX(SDRMPX), .nSDROE(nSDROE),
        .SDPAD(SDPAD), .SDPA(SDPA), .SDPMPX(SDPMPX), .nSDPOE(nSDPOE),
        .nSDROM(nSDROM), .nSDMRD(nSDMRD), .SDA(SDA), .SDD(SDD),
        .PBUS(PBUS), .nVCS(nVCS), .S2H1(S2H1), .CA4(CA4),
        .PCK1B(PCK1B), .PCK2B(PCK2B),
        .CLK_12M(CLK_12M), .EVEN(EVEN), .LOAD(LOAD), .H(H),
        .GAD(GAD), .GBD(GBD), .FIXD_CART(FIXD_CART),
        .CDA_U(CDA_U), .nCRDC(nCRDC), .nCRDO(nCRDO),
        .CARD_PIN_nWE(CARD_PIN_nWE), .CARD_PIN_nREG(CARD_PIN_nREG),
        .nCD1(nCD1), .nCD2(nCD2), .nWP(nWP),
        .VIDEO_R(VIDEO_R), .VIDEO_G(VIDEO_G), .VIDEO_B(VIDEO_B),
        .VIDEO_SYNC(VIDEO_SYNC),
        // exported by our patch - see patch-reference.sh item 5
        .nRESET(nRESET),
        .nROMOEL(nROMOEL), .nROMOEU(nROMOEU),
        .CLK_24M(CLK_24M),
        .SDRD0(SDRD0), .SDRD1(SDRD1)
    );

    // ---- the cartridge ---------------------------------------------------
    aes_cart CART (
        .nPORTADRS(nPORTADRS),
        .nSDPOE(nSDPOE), .SDPMPX(SDPMPX), .SDPA(SDPA), .SDPAD(SDPAD),
        .nRESET(nRESET), .CLK_68KCLKB(CLK_68KCLKB),
        .nPORTWEL(nPORTWEL), .nPORTWEU(nPORTWEU),
        .nPORTOEL(nPORTOEL), .nPORTOEU(nPORTOEU),
        .nROMOEL(nROMOEL), .nROMOEU(nROMOEU),
        .nAS(nAS), .M68K_RW(M68K_RW), .M68K_DATA(M68K_DATA),
        .M68K_ADDR(M68K_ADDR[19:1]), .nROMOE(nROMOE),
        .nROMWAIT(nROMWAIT), .nPWAIT1(nPWAIT1), .nPWAIT0(nPWAIT0),
        .PDTACK(PDTACK),
        .SDRAD(SDRAD), .SDRA_L(SDRA_L), .SDRA_U(SDRA_U),
        .SDRMPX(SDRMPX), .nSDROE(nSDROE), .CLK_4MB(CLK_4MB),
        .CLK_24M(CLK_24M), .nSDROM(nSDROM), .nSDMRD(nSDMRD), .SDA(SDA),
        .SDRD1(SDRD1), .SDRD0(SDRD0), .PBUS(PBUS),
        .CA4(CA4), .LOAD(LOAD), .H(H), .EVEN(EVEN), .S2H1(S2H1),
        .CLK_12M(CLK_12M), .PCK2B(PCK2B), .PCK1B(PCK1B),
        .FIXD(FIXD_CART), .DOTA(DOTA), .DOTB(DOTB),
        .GAD(GAD), .GBD(GBD), .SDD(SDD), .CLK_8M(CLK_8M)
    );

    // ---- stimulus --------------------------------------------------------
    initial begin
        nRESET_BTN = 1'b1;
        P1_IN = 10'b1111111111;     // joypads idle, active low
        P2_IN = 10'b1111111111;
        DIPSW = 8'b11111111;        // test mode off
        #30   nRESET_BTN = 1'b0;    // hold reset ~1 us, as testbench_1 does
        #1000 nRESET_BTN = 1'b1;
    end

    // ---- watch the bus ---------------------------------------------------
    // The reset vector fetch is four word reads: SSP high, SSP low, PC high,
    // PC low, at $000000-$000006. On this machine those come from the BIOS,
    // not the cartridge, because the vector table is mapped from the BIOS at
    // reset.
    integer cycles = 0;
    reg [23:0] a;
    reg [31:0] ssp = 32'hxxxxxxxx, pc = 32'hxxxxxxxx;

    always @(negedge nAS) begin
        a = {M68K_ADDR, 1'b0};
        if (cycles < 24)
            begin $display("  %7t  addr %06h  %s", $time, a, M68K_RW ? "read" : "WRITE"); $fflush; end
        cycles = cycles + 1;
    end

    // Capture what the CPU actually latched for the vector fetch.
    always @(posedge nAS) begin
        a = {M68K_ADDR, 1'b0};
        case (a)
            24'h000000: ssp[31:16] = M68K_DATA;
            24'h000002: ssp[15:0]  = M68K_DATA;
            24'h000004: pc[31:16]  = M68K_DATA;
            24'h000006: pc[15:0]   = M68K_DATA;
        endcase
    end

    // Progress, so a long run is distinguishable from a hung one.
    initial begin
        forever begin
            #5000;
            $display("  ... %0t ns simulated, %0d bus cycles", $time, cycles);
            $fflush;
        end
    end

    initial begin
        $display("");
        $display("NeoForge whole-console harness");
        $display("========================================");
        $display("");
        $display("  first bus cycles after reset:");
        $fflush;
        #40000;                     // 40 us - reset pulse plus vector fetch
        $display("");
        $display("  bus cycles seen : %0d", cycles);
        $display("  SSP fetched     : %08h", ssp);
        $display("  PC  fetched     : %08h", pc);
        $display("");
        if (cycles == 0)
            $display("FAIL - the 68000 never asserted /AS. No clock, or held in reset.");
        else if (ssp === 32'h0010f300 && pc === 32'h00c04300)
            $display("PASS - reset vector fetched correctly from the BIOS.");
        else
            $display("INCOMPLETE - bus runs, but the vector is not what nullbios holds (expected SSP 0010f300, PC 00c04300).");
        $display("");
        $finish;
    end

endmodule
