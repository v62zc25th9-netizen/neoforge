# NeoForge fix-layer test ROM
#
# Builds a cartridge image containing NO sprite data at all - the C ROMs are
# zero-filled - to exercise the display path a serializer-less AES cartridge
# would use. See main.c and docs/open-questions.md Q1.
#
#   make            build the cartridge zip
#   make gngeo      build and run in GnGeo, AES mode
#   make clean
#
# Requires ngdevkit on PATH (brew install ngdevkit; brew install ngdevkit-gngeo)

GAMEROM   := neoforge-fixtest
BUILD     := build
ROM       := $(BUILD)/rom
PYTHON    ?= python3

PKGCONFIG ?= pkg-config
NGCFLAGS  := $(shell $(PKGCONFIG) --cflags ngdevkit)
NGLIBS    := $(shell $(PKGCONFIG) --libs ngdevkit)
SHAREDIR  := $(shell $(PKGCONFIG) --variable=sharedir ngdevkit)

GCC        := m68k-neogeo-elf-gcc
OBJCOPY    := m68k-neogeo-elf-objcopy
Z80OBJCOPY := z80-neogeo-ihx-sdobjcopy
ROMTOOL    := romtool.py
GNGEO      ?= ngdevkit-gngeo

CFLAGS := -std=c99 -fomit-frame-pointer -O2 -g

# The Z80 sound driver.
#
# This ROM makes no sound and does not care what is in the M ROM, but the
# system expects a valid Z80 program there. For now we borrow the prebuilt
# driver from an ngdevkit-examples checkout rather than building one.
#
# TODO: link a minimal driver against nullsound-aes.lib so this build is
# self-contained. Until then this is the one external dependency.
NGDEVKIT_EXAMPLES ?= $(HOME)/ngdevkit-examples
SOUND_DRIVER      ?= $(NGDEVKIT_EXAMPLES)/01-helloworld/build/assets/base-sound-driver.ihx

# GnGeo's own data archive, for the AES BIOS wiring
GNGEO_DATA ?= $(shell brew --prefix ngdevkit-gngeo 2>/dev/null)/share/ngdevkit-gngeo/gngeo_data.zip

PROM  := $(ROM)/$(GAMEROM)-p1.p1
SROM  := $(ROM)/$(GAMEROM)-s1.s1
MROM  := $(ROM)/$(GAMEROM)-m1.m1
CROM1 := $(ROM)/$(GAMEROM)-c1.c1
CROM2 := $(ROM)/$(GAMEROM)-c2.c2
VROM  := $(ROM)/$(GAMEROM)-v1.v1
CART  := $(ROM)/$(GAMEROM).zip

# Sizes the cartridge format expects
P_SIZE := 1048576
S_SIZE := 131072
M_SIZE := 131072
C_SIZE := 2097152
V_SIZE := 524288

pad = $(PYTHON) -c 'import sys;open(sys.argv[1],"ab").truncate(int(sys.argv[2]))' $(1) $(2)

.PHONY: all gngeo clean distclean
all: $(CART)

$(ROM):
	@mkdir -p $(ROM)

# --- fix tiles, font and the one sprite tile, all generated ------------------
# tiles.py emits the S ROM plus a single solid sprite tile split across C1/C2.
# No image tooling: for a tile of one colour the block/row interleave cancels.
$(BUILD)/neoforge.fix $(BUILD)/neoforge.c1 $(BUILD)/neoforge.c2: tiles.py | $(ROM)
	$(PYTHON) tiles.py $(BUILD)/neoforge.fix $(BUILD)/neoforge.c1 $(BUILD)/neoforge.c2

$(SROM): $(BUILD)/neoforge.fix
	cp $< $@
	$(call pad,$@,$(S_SIZE))

# --- 68k program -------------------------------------------------------------
$(BUILD)/main.o: main.c | $(ROM)
	$(GCC) $(NGCFLAGS) $(CFLAGS) -c $< -o $@

$(BUILD)/rom.elf: $(BUILD)/main.o
	$(GCC) -o $@ $< $(NGLIBS)

$(PROM): $(BUILD)/rom.elf
	$(OBJCOPY) -O binary -S -R .text2 --gap-fill 0xff --pad-to $(P_SIZE) $< $@
	dd if=$@ of=$@ conv=notrunc,swab status=none

# --- Z80 program (borrowed; see note above) ----------------------------------
$(MROM): | $(ROM)
	@test -f "$(SOUND_DRIVER)" || { \
	  echo "ERROR: sound driver not found at $(SOUND_DRIVER)"; \
	  echo "       set NGDEVKIT_EXAMPLES=/path/to/ngdevkit-examples, or"; \
	  echo "       SOUND_DRIVER=/path/to/base-sound-driver.ihx"; exit 1; }
	$(Z80OBJCOPY) -I ihex -O binary "$(SOUND_DRIVER)" $@ --pad-to $(M_SIZE)

# --- C ROMs: exactly one solid sprite tile, the rest zero --------------------
# The tile exists only so the positive control has something opaque to draw.
$(CROM1): $(BUILD)/neoforge.c1
	cp $< $@
	$(call pad,$@,$(C_SIZE))

$(CROM2): $(BUILD)/neoforge.c2
	cp $< $@
	$(call pad,$@,$(C_SIZE))

$(VROM): | $(ROM)
	: > $@
	$(call pad,$@,$(V_SIZE))

# --- assemble ----------------------------------------------------------------
$(CART): $(PROM) $(SROM) $(MROM) $(CROM1) $(CROM2) $(VROM)
	$(ROMTOOL) -b cartridge -f zip -p $(PROM) -c $(CROM1) $(CROM2) -v $(VROM) \
	  -s $(SROM) -m $(MROM) -n $(GAMEROM) -x "zip.comment=" -o $@
	$(ROMTOOL) -b hash -f gngeo -p $(PROM) -c $(CROM1) $(CROM2) -v $(VROM) \
	  -s $(SROM) -m $(MROM) -n $(GAMEROM) -l "NeoForge fix-layer test" \
	  -x gngeo.data=$(GNGEO_DATA) -o $(ROM)/gngeo_data.zip
	cp $(SHAREDIR)/aes.zip $(SHAREDIR)/neogeo.zip $(ROM)/
	@echo
	@echo "built $(CART)"

# --system home is AES mode
gngeo: $(CART)
	$(GNGEO) --scale 3 --no-resize --system home -i $(ROM) -d $(ROM)/gngeo_data.zip $(GAMEROM)

clean:
	rm -rf $(BUILD)

distclean: clean
