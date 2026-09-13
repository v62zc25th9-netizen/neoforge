// SPDX-License-Identifier: GPL-3.0-or-later
//
// NeoForge - stub for NeoGeoFPGA-sim's logger.
//
// neogeo.v instantiates `logger`, and Testbench/logger.v reads
// `testbench_1.MC` by hierarchical name. That couples the system model to one
// specific testbench: elaborate `neogeo` under any other top and the reference
// disappears.
//
// Our harness has its own top, so we substitute an empty module with the same
// interface. The logger only produced diagnostic output; nothing depends on it.
//
// Arguably an upstream wart rather than a bug - but it does mean neogeo.v
// cannot be used outside testbench_1 without doing this.

module logger(
    input CLK_6MB,
    input nBNKB,
    input SHADOW,
    input COUNTER1,
    input COUNTER2,
    input LOCKOUT1,
    input LOCKOUT2
);
endmodule
