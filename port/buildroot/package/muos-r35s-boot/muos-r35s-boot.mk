# SPDX-License-Identifier: MIT
MUOS_R35S_BOOT_VERSION = 1
MUOS_R35S_BOOT_SITE = /work/boot-order/source
MUOS_R35S_BOOT_SITE_METHOD = local
MUOS_R35S_BOOT_LICENSE = MIT
MUOS_R35S_BOOT_LICENSE_FILES = LICENSE
MUOS_R35S_BOOT_DEPENDENCIES = muos-r35s-session

define MUOS_R35S_BOOT_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/libexec/muos-boot/bin
	for name in service.sh step.sh order.sh native-functions.sh card-guard.sh select.sh select-functions.sh diagnostic.sh diagnostic-save.sh power-functions.sh; do \
		$(INSTALL) -m 0755 $(@D)/$$name $(TARGET_DIR)/usr/libexec/muos-boot/$$name || exit 1; \
	done
	$(INSTALL) -m 0755 $(TARGET_DIR)/usr/libexec/muos-session/bin/muos-run-bounded \
		$(TARGET_DIR)/usr/libexec/muos-boot/bin/muos-run-bounded
	$(INSTALL) -D -m 0644 $(@D)/muos-boot.default $(TARGET_DIR)/etc/default/muos-boot
	$(INSTALL) -D -m 0644 $(@D)/inittab $(TARGET_DIR)/usr/share/muos-r35s-boot/inittab
	$(INSTALL) -D -m 0644 $(@D)/contract.json $(TARGET_DIR)/usr/share/muos-r35s-boot/contract.json
	$(INSTALL) -D -m 0644 $(@D)/LICENSE $(TARGET_DIR)/usr/share/licenses/muos-r35s-boot/LICENSE
endef

# Deliberately no INSTALL_INIT_SYSV and no replacement of /etc/inittab.
$(eval $(generic-package))
