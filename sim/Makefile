# NeoForge - serializer simulation
#
# Requires Icarus Verilog:
#   macOS   brew install icarus-verilog
#   Debian  apt install iverilog
# Optional, for waveforms:
#   brew install gtkwave   /   apt install gtkwave
#
# The device under test is NOT vendored into this repository. zmc2_dot.v is
# GPL-3.0 and NeoForge is currently MIT; copying it in would create a licence
# conflict we have not resolved. This Makefile fetches it instead, so the
# GPL source stays in its own tree under its own terms.

REF_DIR  ?= ../.reference
NGFPGA   := $(REF_DIR)/NeoGeoFPGA-sim
DUT      := $(NGFPGA)/Video/zmc2_dot.v
IVERILOG ?= iverilog
VVP      ?= vvp

.PHONY: all run wave clean distclean

all: run

$(NGFPGA):
	@echo "==> fetching NeoGeoFPGA-sim (GPL-3.0, not vendored)"
	@mkdir -p $(REF_DIR)
	git clone --depth 1 https://github.com/neogeodev/NeoGeoFPGA-sim.git $(NGFPGA)

zmc2_tb: zmc2_dot_tb.v $(NGFPGA)
	$(IVERILOG) -g2012 -o $@ zmc2_dot_tb.v $(DUT)

run: zmc2_tb
	@$(VVP) ./zmc2_tb

wave: run
	gtkwave zmc2_dot.vcd

clean:
	rm -f zmc2_tb zmc2_dot.vcd

distclean: clean
	rm -rf $(REF_DIR)
