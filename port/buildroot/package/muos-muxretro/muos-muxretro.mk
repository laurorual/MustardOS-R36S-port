# SPDX-License-Identifier: MIT
MUOS_MUXRETRO_VERSION = 1
MUOS_MUXRETRO_SITE = /work/muxretro-package/source
MUOS_MUXRETRO_SITE_METHOD = local
MUOS_MUXRETRO_LICENSE = GPL-3.0, MIT, BSD-2-Clause, Unlicense
MUOS_MUXRETRO_LICENSE_FILES = frontend/LICENSE rcheevos/LICENSE \
	frontend/retro/core/libretro.h frontend/vendor/miniz/LICENSE \
	frontend/vendor/xxhash/LICENSE frontend/vendor/stb/LICENSE \
	frontend/vendor/mini/LICENSE frontend/vendor/json/LICENSE frontend/vendor/mdns/LICENSE
MUOS_MUXRETRO_DEPENDENCIES = host-pkgconf sdl2 sdl2_image sdl2_mixer sdl2_ttf \
	harfbuzz freetype libpng libcurl libarchive openssl zlib libegl libgles
MUOS_MUXRETRO_PLATFORM = /work/muxretro-package/platform

# Hashes and ELF/header checks are performed by the preparation/check scripts;
# this build guard pins the complete private link SDK before any compilation.
define MUOS_MUXRETRO_BUILD_CMDS
	cd $(MUOS_MUXRETRO_PLATFORM) && sha256sum -c $(@D)/platform.sha256
	$(TARGET_MAKE_ENV) sh $(@D)/build-host.sh \
		"$(TARGET_CC)" "$(TARGET_AR)" "$(PKG_CONFIG_HOST_BINARY)" \
		"$(STAGING_DIR)" "$(@D)" "$(MUOS_MUXRETRO_PLATFORM)" \
		"$(TARGET_CFLAGS)" "$(TARGET_LDFLAGS)"
endef

define MUOS_MUXRETRO_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/frontend/bin/muxretro \
		$(TARGET_DIR)/opt/muos/frontend/muxretro
	$(INSTALL) -D -m 0644 $(@D)/provenance.json \
		$(TARGET_DIR)/usr/share/muos-muxretro/provenance.json
	$(INSTALL) -D -m 0644 $(@D)/platform.sha256 \
		$(TARGET_DIR)/usr/share/muos-muxretro/platform.sha256
	$(foreach f,$(MUOS_MUXRETRO_LICENSE_FILES),$(INSTALL) -D -m 0644 $(@D)/$(f) $(TARGET_DIR)/usr/share/licenses/muos-muxretro/$(f)$(sep))
	cd $(TARGET_DIR) && { sha256sum opt/muos/frontend/muxretro \
		usr/share/muos-muxretro/provenance.json usr/share/muos-muxretro/platform.sha256; \
		find usr/share/licenses/muos-muxretro -type f -exec sha256sum '{}' ';'; \
		} | LC_ALL=C sort -k2 | sed 's|  |  /|' > usr/share/muos-muxretro/payload.sha256
endef

# Deliberately no init, boot hooks, platform libraries, cores or private data.
$(eval $(generic-package))
