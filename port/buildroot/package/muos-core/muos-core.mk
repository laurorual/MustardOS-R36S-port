# SPDX-License-Identifier: MIT
MUOS_CORE_VERSION = 1
MUOS_CORE_SITE = /work/core/source
MUOS_CORE_SITE_METHOD = local
MUOS_CORE_LICENSE = GPL-3.0
MUOS_CORE_LICENSE_FILES = frontend/LICENSE internal/LICENSE tool/LICENSE
MUOS_CORE_DEPENDENCIES = jq procps-ng dbus alsa-utils pipewire wireplumber

define MUOS_CORE_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -D_GNU_SOURCE -fPIE -I$(@D)/frontend \
		$(@D)/frontend/module/muvarctl.c $(@D)/frontend/common/config/var_store.c \
		$(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now -o $(@D)/muvarctl
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -D_GNU_SOURCE -fPIE -I$(@D)/frontend \
		$(@D)/frontend/module/mulog.c $(TARGET_LDFLAGS) -pie -o $(@D)/mulog
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -fPIE $(@D)/tool/utils/fnv1a.c \
		$(TARGET_LDFLAGS) -pie -o $(@D)/fnv1a
	$(TARGET_MAKE_ENV) $(MAKE) -C $(@D)/frontend/input \
		CC="$(TARGET_CC)" CFLAGS="$(TARGET_CFLAGS) -std=c11 -D_GNU_SOURCE -fPIE" \
		LDFLAGS="$(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now" BUILDDIR=$(@D)/input-build
endef

define MUOS_CORE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/muvarctl $(TARGET_DIR)/opt/muos/frontend/muvarctl
	$(INSTALL) -D -m 0755 $(@D)/mulog $(TARGET_DIR)/opt/muos/frontend/mulog
	$(INSTALL) -D -m 0755 $(@D)/input-build/bin/muinput $(TARGET_DIR)/opt/muos/frontend/muinput
	$(INSTALL) -D -m 0755 $(@D)/fnv1a $(TARGET_DIR)/opt/muos/bin/fnv1a
	cp -a $(@D)/internal/script $(TARGET_DIR)/opt/muos/
	cp -a $(@D)/internal/share $(TARGET_DIR)/opt/muos/
	cp -a $(@D)/overlay/. $(TARGET_DIR)/
	$(INSTALL) -D -m 0644 $(@D)/internal/LICENSE $(TARGET_DIR)/usr/share/licenses/muos-core/LICENSE
endef

define MUOS_CORE_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(@D)/S95muos-core $(TARGET_DIR)/etc/init.d/S95muos-core
endef

$(eval $(generic-package))
