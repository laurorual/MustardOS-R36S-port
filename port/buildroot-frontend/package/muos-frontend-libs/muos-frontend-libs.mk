# SPDX-License-Identifier: MIT
MUOS_FRONTEND_LIBS_VERSION = 1
MUOS_FRONTEND_LIBS_SITE = /work/frontend-libs/source
MUOS_FRONTEND_LIBS_SITE_METHOD = local
MUOS_FRONTEND_LIBS_LICENSE = GPL-3.0, MIT, BSD-2-Clause, Unlicense
MUOS_FRONTEND_LIBS_LICENSE_FILES = frontend/LICENSE frontend/vendor/lvgl/LICENCE \
	frontend/vendor/plutosvg/LICENSE frontend/vendor/plutosvg/plutovg/LICENSE \
	frontend/vendor/json/LICENSE frontend/vendor/mini/LICENSE frontend/vendor/miniz/LICENSE \
	frontend/vendor/xxhash/LICENSE frontend/vendor/stb/LICENSE frontend/vendor/mdns/LICENSE \
	deps/mojibake-0.3.6/LICENSE
MUOS_FRONTEND_LIBS_DEPENDENCIES = host-pkgconf sdl2 sdl2_image sdl2_mixer sdl2_ttf \
	harfbuzz freetype libpng libcurl ffmpeg libarchive openssl zlib libegl libgles
MUOS_FRONTEND_LIBS_INSTALL_STAGING = YES
MUOS_FRONTEND_LIBS_NAMES = libui.so libmuxcom.so libmuxmod.so libplutosvg.so

define MUOS_FRONTEND_LIBS_BUILD_CMDS
	$(TARGET_MAKE_ENV) sh $(@D)/build-libs.sh \
		"$(TARGET_CC)" "$(TARGET_AR)" "$(PKG_CONFIG_HOST_BINARY)" \
		"$(STAGING_DIR)" "$(@D)" "$(TARGET_CFLAGS)" "$(TARGET_LDFLAGS)"
endef

define MUOS_FRONTEND_LIBS_INSTALL_STAGING_CMDS
	$(foreach f,$(MUOS_FRONTEND_LIBS_NAMES),$(INSTALL) -D -m 0644 $(@D)/frontend-bin/lib/$(f) $(STAGING_DIR)/usr/lib/$(f)$(sep))
endef

define MUOS_FRONTEND_LIBS_INSTALL_TARGET_CMDS
	$(foreach f,$(MUOS_FRONTEND_LIBS_NAMES),$(INSTALL) -D -m 0644 $(@D)/frontend-bin/lib/$(f) $(TARGET_DIR)/opt/muos/frontend/lib/$(f)$(sep))
	$(INSTALL) -D -m 0644 $(@D)/provenance.json $(TARGET_DIR)/usr/share/muos-frontend-libs/provenance.json
	$(foreach f,$(MUOS_FRONTEND_LIBS_LICENSE_FILES),$(INSTALL) -D -m 0644 $(@D)/$(f) $(TARGET_DIR)/usr/share/licenses/muos-frontend-libs/$(f)$(sep))
	cd $(TARGET_DIR) && { \
		sha256sum $(addprefix opt/muos/frontend/lib/,$(MUOS_FRONTEND_LIBS_NAMES)) usr/share/muos-frontend-libs/provenance.json; \
		find usr/share/licenses/muos-frontend-libs -type f -exec sha256sum '{}' ';'; \
		} | LC_ALL=C sort -k2 | sed 's|  |  /|' > usr/share/muos-frontend-libs/payload.sha256
endef

# Consumers carry matching frontend headers. No public header SDK is claimed.
# No init, executable, diagnostic variant, core, ROM or saved state is installed.
$(eval $(generic-package))
