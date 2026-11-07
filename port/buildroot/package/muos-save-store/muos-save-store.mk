# SPDX-License-Identifier: MIT
MUOS_SAVE_STORE_VERSION = 1
MUOS_SAVE_STORE_SITE = /work/save-store-package/source
MUOS_SAVE_STORE_SITE_METHOD = local
MUOS_SAVE_STORE_LICENSE = MIT
MUOS_SAVE_STORE_LICENSE_FILES = LICENSE
MUOS_SAVE_STORE_DEPENDENCIES = zlib

# The preparation script stages exactly C source, license and contract.
# Buildroot legal-info archives the same whitelist, not the entire port tree.

define MUOS_SAVE_STORE_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -Wall -Wextra -Werror \
		-fstack-protector-strong -fPIE $(@D)/muos-save-store.c \
		$(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now -lz -o $(@D)/muos-save-store
endef

define MUOS_SAVE_STORE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/muos-save-store \
		$(TARGET_DIR)/usr/libexec/muos-save-store/muos-save-store
	$(INSTALL) -D -m 0644 $(@D)/contract.json \
		$(TARGET_DIR)/usr/share/muos-save-store/contract.json
	$(INSTALL) -D -m 0644 $(@D)/LICENSE \
		$(TARGET_DIR)/usr/share/licenses/muos-save-store/LICENSE
	cd $(TARGET_DIR) && sha256sum usr/libexec/muos-save-store/muos-save-store \
		usr/share/muos-save-store/contract.json usr/share/licenses/muos-save-store/LICENSE | \
		sed 's|  |  /|' > usr/libexec/muos-save-store/payload.sha256
endef

# No INIT_SYSV/SYSTEMD, post-build hook, data initialization or default config.
$(eval $(generic-package))
