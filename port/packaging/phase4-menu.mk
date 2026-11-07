# Native muxlaunch diagnostic, compiled only against the Buildroot SDK.
PKGS = sdl2 SDL2_image SDL2_mixer SDL2_ttf harfbuzz freetype2 libpng libcurl libavformat libavcodec libswscale libswresample libavutil libarchive openssl
CPPFLAGS += -I. -Ivendor -Imodule -Imodule/ui -Ivendor/plutosvg/source -Ivendor/plutosvg/plutovg/include -I../deps/include $(shell $(PKG_CONFIG) --cflags $(PKGS)) -DMINIZ_NO_ZLIB_COMPATIBLE_NAMES
override CFLAGS += -std=c11 -D_GNU_SOURCE -DTEST_IMAGE=1 -fPIE -ffunction-sections -fdata-sections -fstack-protector-strong -Wall -Wno-unused-function -Wno-format-zero-length -ffile-prefix-map=/work=.
COMMON = $(filter-out common/runtime/crash.c,$(shell find common -name '*.c'))
LVGL = $(shell find vendor/lvgl/src -name '*.c')
PLUTO = vendor/plutosvg/source/plutosvg.c $(wildcard vendor/plutosvg/plutovg/source/*.c)
VENDOR = vendor/json/json.c vendor/mini/mini.c vendor/miniz/miniz.c vendor/xxhash/xxhash.c
SOURCES = $(COMMON) $(LVGL) $(PLUTO) $(VENDOR) module/muxshare.c module/muxlaunch.c module/ui/ui_muxlaunch.c phase4-menu.c
OBJECTS = $(addprefix ../menu-objects/,$(SOURCES:.c=.o))
LDLIBS = $(shell $(PKG_CONFIG) --libs $(PKGS)) ../deps/libmojibake.a -lm -lpthread -ldl -latomic
LDFLAGS += -pie -Wl,--gc-sections,-z,relro,-z,now -Wl,--wrap=run_exec,--wrap=load_mux,--wrap=play_sound
.DEFAULT_GOAL := ../phase4-menu
../phase4-menu: $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) $(LDLIBS) -Wl,-Map,../phase4-menu.map -o $@
../menu-objects/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
-include $(OBJECTS:.o=.d)
