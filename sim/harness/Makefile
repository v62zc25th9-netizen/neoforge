# NeoForge - whole-console simulation harness
#
# Runs a NeoForge ROM through a full Verilog model of the Neo Geo, so the
# cartridge's access time can be swept without any hardware.
#
#   make lint     fetch, patch, and lint the whole system   <- works today
#   make clean
#
# STATUS: lints clean. It does not run yet - see README.md for exactly what
# remains. Do not mistake `make lint` passing for a working simulation.
#
# Requires Verilator 5. Version 4 ignores #delay entirely, which would make a
# timing study silently meaningless:
#   macOS   brew install verilator
#   Debian  apt install verilator
#
# Neither reference is vendored. Both are GPL-3.0 and are cloned into
# .reference/ at the repository root, which is gitignored. See LICENSE.md.

REF_DIR  ?= ../../.reference
NGFPGA   := $(REF_DIR)/NeoGeoFPGA-sim
FX68K    := $(REF_DIR)/fx68k
VERILATOR ?= verilator

# fx68k mixes blocking and non-blocking assignment to the same variables and
# has several multiply-driven nets. Verilator errors on these by default. They
# are upstream's style, not ours, and the core is widely used as-is.
WAIVERS := -Wno-lint -Wno-style -Wno-BLKANDNBLK -Wno-MULTIDRIVEN \
           -Wno-UNOPTFLAT -Wno-INITIALDLY -Wno-DECLFILENAME

# Modules whose file names do not match them, so Verilator's -y search cannot
# find them. Not a bug - just an hour to work out the first time.
ODDBALLS := $(NGFPGA)/ROMs/*.v $(NGFPGA)/RAMs/*.v \
            $(NGFPGA)/Video/timer.v $(NGFPGA)/Audio/jedi.v

LIBS := -y $(NGFPGA)/CPUs -y $(NGFPGA)/Cartridge -y $(NGFPGA)/Cartridge/ROMs \
        -y $(NGFPGA)/Video -y $(NGFPGA)/Audio -y $(NGFPGA)/System \
        -y $(NGFPGA)/IO -y $(NGFPGA)/RAMs -y $(NGFPGA)/B1RE \
        -y $(NGFPGA)/LSPC2RE -y $(NGFPGA)/Alpha68k -y $(NGFPGA)/ROMs \
        -y $(NGFPGA)/Cells

SRCS := $(NGFPGA)/Cells/*.v $(ODDBALLS) logger_stub.v tg68.sv \
        $(FX68K)/fx68k.sv $(FX68K)/fx68kAlu.sv $(FX68K)/uaddrPla.sv \
        $(NGFPGA)/neogeo.v

.PHONY: all lint fetch patch clean distclean

all: lint

$(NGFPGA)/neogeo.v:
	@echo "==> fetching NeoGeoFPGA-sim (GPL-3.0, not vendored)"
	@mkdir -p $(REF_DIR)
	git clone --depth 1 https://github.com/neogeodev/NeoGeoFPGA-sim.git $(NGFPGA)
	@$(MAKE) patch

$(FX68K)/fx68k.sv:
	@echo "==> fetching fx68k (GPL-3.0, not vendored)"
	@mkdir -p $(REF_DIR)
	git clone --depth 1 https://github.com/ijor/fx68k.git $(FX68K)

fetch: $(NGFPGA)/neogeo.v $(FX68K)/fx68k.sv

# Idempotent: every hunk checks whether it has already been applied.
patch:
	@sh ./patch-reference.sh $(NGFPGA)

lint: fetch
	@echo "==> linting the whole system with fx68k in place of tg68"
	$(VERILATOR) --lint-only --timing $(WAIVERS) --top-module neogeo \
	  $(LIBS) $(SRCS)
	@echo "==> lint clean"

clean:
	rm -rf obj_dir

distclean: clean
	rm -rf $(REF_DIR)
