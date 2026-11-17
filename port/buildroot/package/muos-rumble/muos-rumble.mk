# SPDX-License-Identifier: MIT
MUOS_RUMBLE_VERSION = 1
MUOS_RUMBLE_SITE = $(BR2_EXTERNAL_MUOS_R35S_PATH)/../device/rk-r35s-p0/rumble
MUOS_RUMBLE_SITE_METHOD = local
MUOS_RUMBLE_LICENSE = MIT
MUOS_RUMBLE_LICENSE_FILES = LICENSE

define MUOS_RUMBLE_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -std=gnu11 -Wall -Wextra -Werror \
		-o $(@D)/muos-rumble $(@D)/muos-rumble.c $(TARGET_LDFLAGS)
endef

define MUOS_RUMBLE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/muos-rumble $(TARGET_DIR)/usr/libexec/muos-rumble
endef

$(eval $(generic-package))
