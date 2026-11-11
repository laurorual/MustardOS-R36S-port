# SPDX-License-Identifier: MIT
MUOS_SDL_AUDIO_PROBE_VERSION = 1
MUOS_SDL_AUDIO_PROBE_SITE = $(BR2_EXTERNAL_MUOS_R35S_PATH)/../tools/sdl-audio-probe
MUOS_SDL_AUDIO_PROBE_SITE_METHOD = local
MUOS_SDL_AUDIO_PROBE_LICENSE = MIT
MUOS_SDL_AUDIO_PROBE_LICENSE_FILES = LICENSE
MUOS_SDL_AUDIO_PROBE_DEPENDENCIES = sdl2 host-pkgconf

define MUOS_SDL_AUDIO_PROBE_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -Wall -Wextra -Werror \
		`$(PKG_CONFIG_HOST_BINARY) --cflags sdl2` \
		-o $(@D)/muos-sdl-audio-probe $(@D)/sdl-audio-probe.c \
		$(TARGET_LDFLAGS) `$(PKG_CONFIG_HOST_BINARY) --libs sdl2`
endef

define MUOS_SDL_AUDIO_PROBE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/muos-sdl-audio-probe \
		$(TARGET_DIR)/usr/libexec/muos-sdl-audio-probe
endef

$(eval $(generic-package))
