# SPDX-License-Identifier: MIT
MUOS_R35S_LAUNCHER_ONCE_VERSION = 1
MUOS_R35S_LAUNCHER_ONCE_SITE = $(BR2_EXTERNAL_MUOS_R35S_PATH)/../device/rk-r35s-p0/launcher-once
MUOS_R35S_LAUNCHER_ONCE_SITE_METHOD = local
MUOS_R35S_LAUNCHER_ONCE_LICENSE = MIT
MUOS_R35S_LAUNCHER_ONCE_LICENSE_FILES = LICENSE
MUOS_R35S_LAUNCHER_ONCE_DEPENDENCIES = muos-r35s-session

define MUOS_R35S_LAUNCHER_ONCE_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/libexec/muos-c25
	for name in policy native select session; do \
		$(INSTALL) -m 0755 $(@D)/$$name.sh $(TARGET_DIR)/usr/libexec/muos-c25/$$name.sh || exit 1; \
	done
	$(INSTALL) -m 0755 $(BR2_EXTERNAL_MUOS_R35S_PATH)/../device/rk-r35s-p0/linux-diagnostic/card-guard.sh $(TARGET_DIR)/usr/libexec/muos-c25/card-guard.sh
	cd $(TARGET_DIR)/usr/libexec/muos-c25 && sha256sum card-guard.sh native.sh policy.sh select.sh session.sh > payload.sha256
	chmod 644 $(TARGET_DIR)/usr/libexec/muos-c25/payload.sha256
	$(INSTALL) -D -m 0644 $(@D)/LICENSE $(TARGET_DIR)/usr/share/licenses/muos-r35s-launcher-once/LICENSE
endef

$(eval $(generic-package))
