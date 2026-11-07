# C65 library-only derivative of phase4-frontend.mk; no executable targets.
PKGS = sdl2 SDL2_image SDL2_mixer SDL2_ttf harfbuzz freetype2 libpng libcurl libavformat libavcodec libswscale libswresample libavutil libarchive openssl
CPPFLAGS = -I. -Ivendor -Imodule -Imodule/ui -Ivendor/plutosvg/source -Ivendor/plutosvg/plutovg/include -I../deps/include $(shell $(PKG_CONFIG) --cflags $(PKGS)) -DMINIZ_NO_ZLIB_COMPATIBLE_NAMES
override CFLAGS += -std=c11 -D_GNU_SOURCE -DTEST_IMAGE=1 -fPIC -ffunction-sections -fdata-sections -fstack-protector-strong -Wall -Wno-unused-function -Wno-format-zero-length -ffile-prefix-map=/work=.
COMMON = $(filter-out common/runtime/crash.c,$(shell find common -name '*.c')) vendor/json/json.c vendor/mini/mini.c vendor/miniz/miniz.c vendor/xxhash/xxhash.c
UI = $(shell find vendor/lvgl/src -name '*.c')
PLUTO = vendor/plutosvg/source/plutosvg.c $(wildcard vendor/plutosvg/plutovg/source/*.c)
MODULES := $(shell sed -n '/^MODULES =/,/^$$/p' module/Makefile | sed 's/^MODULES =//;s/\\//g')
MODSRC = $(addprefix module/,$(addsuffix .c,$(MODULES))) $(wildcard module/ui/*.c)
OBJ = ../frontend-objects
BIN = ../frontend-bin
obj = $(addprefix $(OBJ)/,$(1:.c=.o))
LIBS = $(shell $(PKG_CONFIG) --libs $(PKGS)) -lm -lpthread -ldl -latomic
RPATH = -Wl,--enable-new-dtags,-rpath,'$$ORIGIN'
.DEFAULT_GOAL := all
.PHONY: all
all: $(addprefix $(BIN)/lib/,libui.so libmuxcom.so libmuxmod.so libplutosvg.so)
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
