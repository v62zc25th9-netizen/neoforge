# NeoForge - AES cartridge logic simulation
#
# Requires Icarus Verilog:
#   macOS   brew install icarus-verilog
#   Debian  apt install iverilog
# Optional, for waveforms:
#   brew install gtkwave   /   apt install gtkwave
#
# The devices under test are NOT vendored into this repository. They are
# GPL-3.0; keeping foreign sources in their own tree under their own terms
# keeps our licensing statements true. See LICENSE.md.
#
# .reference/ is gitignored at the repository root. Do not commit it.

REF_DIR  ?= ../.reference
NGFPGA   := $(REF_DIR)/NeoGeoFPGA-sim
DUT_DOT  := $(NGFPGA)/Video/zmc2_dot.v
DUT_ZMC  := $(NGFPGA)/Cartridge/zmc.v
IVERILOG ?= iverilog
VVP      ?= vvp

BENCHES  := zmc2_tb zmc_tb

.PHONY: all run wave wave-dot wave-zmc clean distclean

all: run

# Depend on a source file, not the directory. An empty or half-fetched
# .reference/NeoGeoFPGA-sim would otherwise satisfy a directory target and
# produce a confusing compile error instead of re-fetching.
$(DUT_DOT):
	@echo "==> fetching NeoGeoFPGA-sim (GPL-3.0, not vendored)"
	@rm -rf $(NGFPGA)
	@mkdir -p $(REF_DIR)
	git clone --depth 1 https://github.com/neogeodev/NeoGeoFPGA-sim.git $(NGFPGA)

# Same tree, so fetching one fetches both.
$(DUT_ZMC): $(DUT_DOT)

# The sprite serializer datapath - NEO-ZMC2's graphics half.
zmc2_tb: zmc2_dot_tb.v $(DUT_DOT)
	$(IVERILOG) -g2012 -o $@ zmc2_dot_tb.v $(DUT_DOT)

# The M1 bankswitcher - NEO-ZMC2's other half. zmc_tb.v carries its own
# corrected model alongside the reference, so both are compiled here.
zmc_tb: zmc_tb.v $(DUT_ZMC)
	$(IVERILOG) -g2012 -o $@ zmc_tb.v $(DUT_ZMC)

run: $(BENCHES)
	@for b in $(BENCHES); do $(VVP) ./$$b || exit 1; done

wave: wave-dot

wave-dot: zmc2_tb
	@$(VVP) ./zmc2_tb
	gtkwave zmc2_dot.vcd

wave-zmc: zmc_tb
	@$(VVP) ./zmc_tb
	gtkwave zmc.vcd

clean:
	rm -f $(BENCHES) zmc2_dot.vcd zmc.vcd

distclean: clean
	rm -rf $(REF_DIR)
