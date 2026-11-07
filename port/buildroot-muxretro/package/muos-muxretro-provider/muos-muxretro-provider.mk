# SPDX-License-Identifier: MIT
MUOS_MUXRETRO_PROVIDER_VERSION = 1
MUOS_MUXRETRO_PROVIDER_SITE = /work/muxretro-provider/source
MUOS_MUXRETRO_PROVIDER_SITE_METHOD = local
MUOS_MUXRETRO_PROVIDER_LICENSE = GPL-3.0, MIT, BSD-2-Clause, Unlicense
MUOS_MUXRETRO_PROVIDER_LICENSE_FILES = frontend/LICENSE rcheevos/LICENSE \
	frontend/retro/core/libretro.h frontend/vendor/miniz/LICENSE \
	frontend/vendor/xxhash/LICENSE frontend/vendor/stb/LICENSE \
	frontend/vendor/mini/LICENSE frontend/vendor/json/LICENSE frontend/vendor/mdns/LICENSE \
	frontend/vendor/lvgl/LICENCE
MUOS_MUXRETRO_PROVIDER_DEPENDENCIES = muos-frontend-libs host-pkgconf \
	sdl2 sdl2_image sdl2_mixer sdl2_ttf harfbuzz freetype libpng libcurl \
	libarchive openssl zlib libegl libgles

define MUOS_MUXRETRO_PROVIDER_BUILD_CMDS
	cd $(STAGING_DIR) && sha256sum -c $(@D)/provider-staging.sha256
	$(TARGET_MAKE_ENV) sh $(@D)/build-host.sh \
		"$(TARGET_CC)" "$(TARGET_AR)" "$(PKG_CONFIG_HOST_BINARY)" \
		"$(STAGING_DIR)" "$(@D)" "$(TARGET_CFLAGS)" "$(TARGET_LDFLAGS)"
endef

define MUOS_MUXRETRO_PROVIDER_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/frontend/bin/muxretro $(TARGET_DIR)/opt/muos/frontend/muxretro
	$(INSTALL) -D -m 0644 $(@D)/provenance.json $(TARGET_DIR)/usr/share/muos-muxretro-provider/provenance.json
	$(INSTALL) -D -m 0644 $(@D)/provider-runtime.sha256 $(TARGET_DIR)/usr/share/muos-muxretro-provider/provider-runtime.sha256
	$(foreach f,$(MUOS_MUXRETRO_PROVIDER_LICENSE_FILES),$(INSTALL) -D -m 0644 $(@D)/$(f) $(TARGET_DIR)/usr/share/licenses/muos-muxretro-provider/$(f)$(sep))
	cd $(TARGET_DIR) && { sha256sum opt/muos/frontend/muxretro \
		usr/share/muos-muxretro-provider/provenance.json usr/share/muos-muxretro-provider/provider-runtime.sha256; \
		find usr/share/licenses/muos-muxretro-provider -type f -exec sha256sum '{}' ';'; \
		} | LC_ALL=C sort -k2 | sed 's|  |  /|' > usr/share/muos-muxretro-provider/payload.sha256
endef

# The provider owns its libraries. No platform path, boot hook or runtime caller.
$(eval $(generic-package))
