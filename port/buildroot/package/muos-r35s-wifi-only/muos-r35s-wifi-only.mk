# SPDX-License-Identifier: MIT
MUOS_R35S_WIFI_ONLY_VERSION = 1
MUOS_R35S_WIFI_ONLY_SITE = $(BR2_EXTERNAL_MUOS_R35S_PATH)/../device/rk-r35s-p0/wifi-only
MUOS_R35S_WIFI_ONLY_SITE_METHOD = local
MUOS_R35S_WIFI_ONLY_LICENSE = MIT
MUOS_R35S_WIFI_ONLY_LICENSE_FILES = LICENSE

define MUOS_R35S_WIFI_ONLY_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0644 $(@D)/90-muos-r35s-wifi-only.conf \
		$(TARGET_DIR)/etc/modprobe.d/90-muos-r35s-wifi-only.conf
	$(INSTALL) -D -m 0644 $(@D)/LICENSE \
		$(TARGET_DIR)/usr/share/licenses/muos-r35s-wifi-only/LICENSE
endef

# No init action, module load/unload, rootfs hook or image generation.
$(eval $(generic-package))
