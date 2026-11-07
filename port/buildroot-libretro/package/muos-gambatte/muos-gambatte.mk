# SPDX-License-Identifier: MIT
MUOS_GAMBATTE_VERSION = 77f2567d718b8973d02caa2daa8dce4953faf811
MUOS_GAMBATTE_SITE = https://github.com/libretro/gambatte-libretro/archive
MUOS_GAMBATTE_SOURCE = $(MUOS_GAMBATTE_VERSION).tar.gz
# COPYING is GPLv2; compiled source also contains GPLv3 and MIT notices.
# Keep that distinction, rather than infer every file's license from COPYING.
MUOS_GAMBATTE_LICENSE = GPL-2.0, GPL-3.0, MIT
MUOS_GAMBATTE_LICENSE_FILES = COPYING libgambatte/libretro/cc_resampler.c \
	libgambatte/libretro/cc_resampler.h libgambatte/libretro/blipper.c \
	libgambatte/libretro-common/include/libretro.h libgambatte/libretro-common/streams/file_stream.c
MUOS_GAMBATTE_REDISTRIBUTE = NO

define MUOS_GAMBATTE_BUILD_CMDS
	$(TARGET_MAKE_ENV) CFLAGS="$(TARGET_CFLAGS)" CXXFLAGS="$(TARGET_CXXFLAGS)" LDFLAGS="$(TARGET_LDFLAGS)" \
		$(MAKE) -C $(@D) -f Makefile.libretro \
		CC="$(TARGET_CC)" CXX="$(TARGET_CXX)" platform=unix \
		HAVE_NETWORK=0 VIDEO_RGB565=1 GIT_VERSION='" unknown"'
endef

define MUOS_GAMBATTE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0644 $(@D)/gambatte_libretro.so $(TARGET_DIR)/opt/muos/share/core/gambatte_libretro.so
	$(INSTALL) -D -m 0644 $(MUOS_GAMBATTE_PKGDIR)/license-review.json $(TARGET_DIR)/usr/share/muos-gambatte/license-review.json
	$(foreach f,$(MUOS_GAMBATTE_LICENSE_FILES),$(INSTALL) -D -m 0644 $(@D)/$(f) $(TARGET_DIR)/usr/share/licenses/muos-gambatte/$(f)$(sep))
	cd $(TARGET_DIR) && { sha256sum opt/muos/share/core/gambatte_libretro.so usr/share/muos-gambatte/license-review.json; \
		find usr/share/licenses/muos-gambatte -type f -exec sha256sum '{}' ';'; \
		} | LC_ALL=C sort -k2 | sed 's|  |  /|' > usr/share/muos-gambatte/payload.sha256
endef

$(eval $(generic-package))
