# C65 library derivative of phase4-frontend.mk. M6: TEST_IMAGE (default 1,
# the pinned C65 build) selects upstream's test or release build (common.mk
# BUILD=release: -DTEST_IMAGE=0 -DMUOS_RELEASE: no watermark, no LVGL
# FPS/CPU monitor; LVGL structs change, so every part that links libui or
# libmuxcom is rebuilt with the same value), and the executables that link
# the libraries (muxfrontend, muhotkey, mubattery; upstream's $(MODULES)
# rule) are built too. Each value has its own object and output tree.
TEST_IMAGE ?= 1
PKGS = sdl2 SDL2_image SDL2_mixer SDL2_ttf harfbuzz freetype2 libpng libcurl libavformat libavcodec libswscale libswresample libavutil libarchive openssl
CPPFLAGS = -I. -Ivendor -Imodule -Imodule/ui -Ivendor/plutosvg/source -Ivendor/plutosvg/plutovg/include -I../deps/include $(shell $(PKG_CONFIG) --cflags $(PKGS)) -DMINIZ_NO_ZLIB_COMPATIBLE_NAMES
override CFLAGS += -std=c11 -D_GNU_SOURCE -DTEST_IMAGE=$(TEST_IMAGE) $(if $(filter 0,$(TEST_IMAGE)),-DMUOS_RELEASE) -fPIC -ffunction-sections -fdata-sections -fstack-protector-strong -Wall -Wno-unused-function -Wno-format-zero-length -ffile-prefix-map=/work=.
COMMON = $(filter-out common/runtime/crash.c,$(shell find common -name '*.c')) vendor/json/json.c vendor/mini/mini.c vendor/miniz/miniz.c vendor/xxhash/xxhash.c
UI = $(shell find vendor/lvgl/src -name '*.c')
PLUTO = vendor/plutosvg/source/plutosvg.c $(wildcard vendor/plutosvg/plutovg/source/*.c)
MODULES := $(shell sed -n '/^MODULES =/,/^$$/p' module/Makefile | sed 's/^MODULES =//;s/\\//g')
MODSRC = $(addprefix module/,$(addsuffix .c,$(MODULES))) $(wildcard module/ui/*.c)
VARIANT = $(if $(filter 0,$(TEST_IMAGE)),-release)
OBJ = ../frontend-objects$(VARIANT)
BIN = ../frontend-bin$(VARIANT)
EXES = muxfrontend muhotkey mubattery
obj = $(addprefix $(OBJ)/,$(1:.c=.o))
LIBS = $(shell $(PKG_CONFIG) --libs $(PKGS)) -lm -lpthread -ldl -latomic
RPATH = -Wl,--enable-new-dtags,-rpath,'$$ORIGIN'
.DEFAULT_GOAL := all
.PHONY: all exes
all: $(addprefix $(BIN)/lib/,libui.so libmuxcom.so libmuxmod.so libplutosvg.so)
exes: $(addprefix $(BIN)/,$(EXES))
$(addprefix $(BIN)/,$(EXES)): $(BIN)/%: $(OBJ)/module/%.o $(BIN)/lib/libmuxmod.so
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJ)/module/$*.o $(wildcard $(OBJ)/module/ui/ui_$*.o) -L$(BIN)/lib -lui -lmuxcom -lmuxmod -lplutosvg $(LIBS) -pie -Wl,--gc-sections -Wl,-z,relro,-z,now -Wl,--enable-new-dtags,-rpath,'$$ORIGIN/lib' -s -o $@
$(BIN)/lib/libplutosvg.so: $(call obj,$(PLUTO))
	@mkdir -p $(dir $@)
	$(CC) -shared $(CFLAGS) $(LDFLAGS) $^ -Wl,-z,relro,-z,now -lm -o $@
$(BIN)/lib/libui.so: $(call obj,$(UI))
	@mkdir -p $(dir $@)
	$(CC) -shared $(CFLAGS) $(LDFLAGS) $^ $(LIBS) $(RPATH) -Wl,-z,relro,-z,now -o $@
$(BIN)/lib/libmuxcom.so: $(call obj,$(COMMON)) $(BIN)/lib/libplutosvg.so ../deps/libmojibake-pic.a
	$(CC) -shared $(CFLAGS) $(LDFLAGS) $(call obj,$(COMMON)) ../deps/libmojibake-pic.a -L$(BIN)/lib -lplutosvg $(LIBS) $(RPATH) -Wl,-z,relro,-z,now -o $@
$(BIN)/lib/libmuxmod.so: $(call obj,$(MODSRC)) $(BIN)/lib/libmuxcom.so $(BIN)/lib/libui.so
	$(CC) -shared $(CFLAGS) $(LDFLAGS) $(call obj,$(MODSRC)) -L$(BIN)/lib -lui -lmuxcom -lplutosvg $(LIBS) $(RPATH) -Wl,-z,relro,-z,now -o $@
$(OBJ)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
-include $(shell find $(OBJ) -name '*.d' 2>/dev/null)
