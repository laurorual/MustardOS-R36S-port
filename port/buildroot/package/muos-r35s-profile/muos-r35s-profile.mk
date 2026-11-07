# SPDX-License-Identifier: MIT
MUOS_R35S_PROFILE_VERSION = 1
MUOS_R35S_PROFILE_SITE = /work/runtime-profile/source
MUOS_R35S_PROFILE_SITE_METHOD = local
MUOS_R35S_PROFILE_LICENSE = MIT AND GPL-3.0
MUOS_R35S_PROFILE_LICENSE_FILES = LICENSE.port LICENSE.upstream
MUOS_R35S_PROFILE_DEPENDENCIES = muos-core

# The final rootfs overlay runs after package installation. Keep a distinct
# payload and apply it with the explicit post-build hook, after that overlay.
define MUOS_R35S_PROFILE_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/share/muos-r35s-profile
	cp -a $(@D)/payload/. $(TARGET_DIR)/usr/share/muos-r35s-profile/
	$(INSTALL) -D -m 0644 $(@D)/LICENSE.port $(TARGET_DIR)/usr/share/licenses/muos-r35s-profile/LICENSE.port
	$(INSTALL) -D -m 0644 $(@D)/LICENSE.upstream $(TARGET_DIR)/usr/share/licenses/muos-r35s-profile/LICENSE.upstream
endef

$(eval $(generic-package))
