# SPDX-License-Identifier: MIT
MUOS_BOOTREC_VERSION = 1
MUOS_BOOTREC_SITE = $(BR2_EXTERNAL_MUOS_R35S_PATH)/../device/rk-r35s-p0/bootrec
MUOS_BOOTREC_SITE_METHOD = local
MUOS_BOOTREC_LICENSE = MIT, GPL-2.0+ or MIT (bootrec.c)
MUOS_BOOTREC_LICENSE_FILES = LICENSE

define MUOS_BOOTREC_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -std=gnu11 -Wall -Wextra -Werror \
		-o $(@D)/muos-bootrec $(@D)/muos-bootrec.c $(@D)/bootrec.c $(TARGET_LDFLAGS)
endef

define MUOS_BOOTREC_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/muos-bootrec $(TARGET_DIR)/usr/libexec/muos-bootrec
endef

$(eval $(generic-package))
