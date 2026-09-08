# NeoForge - serializer simulation
#
# Requires Icarus Verilog:
#   macOS   brew install icarus-verilog
#   Debian  apt install iverilog
# Optional, for waveforms:
#   brew install gtkwave   /   apt install gtkwave
#
# The device under test is NOT vendored into this repository. zmc2_dot.v is
# GPL-3.0; keeping foreign sources in their own tree under their own terms
# keeps our licensing statements true. See LICENSE.md.
#
# .reference/ is gitignored at the repository root. Do not commit it.

REF_DIR  ?= ../.reference
NGFPGA   := $(REF_DIR)/NeoGeoFPGA-sim
DUT      := $(NGFPGA)/Video/zmc2_dot.v
IVERILOG ?= iverilog
VVP      ?= vvp

.PHONY: all run wave clean distclean

all: run

# Depend on the source file, not the directory. An empty or half-fetched
# .reference/NeoGeoFPGA-sim would otherwise satisfy a directory target and
# produce a confusing compile error instead of re-fetching.
$(DUT):
	@echo "==> fetching NeoGeoFPGA-sim (GPL-3.0, not vendored)"
	@rm -rf $(NGFPGA)
	@mkdir -p $(REF_DIR)
	git clone --depth 1 https://github.com/neogeodev/NeoGeoFPGA-sim.git $(NGFPGA)

zmc2_tb: zmc2_dot_tb.v $(DUT)
	$(IVERILOG) -g2012 -o $@ zmc2_dot_tb.v $(DUT)

run: zmc2_tb
	@$(VVP) ./zmc2_tb

wave: run
	gtkwave zmc2_dot.vcd

clean:
	rm -f zmc2_tb zmc2_dot.vcd

distclean: clean
	rm -rf $(REF_DIR)
