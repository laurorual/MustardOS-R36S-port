# SPDX-License-Identifier: MIT
MUOS_R35S_SESSION_VERSION = 1
MUOS_R35S_SESSION_SITE = /work/runtime-session/source
MUOS_R35S_SESSION_SITE_METHOD = local
MUOS_R35S_SESSION_LICENSE = MIT
MUOS_R35S_SESSION_LICENSE_FILES = LICENSE
MUOS_R35S_SESSION_DEPENDENCIES = muos-r35s-profile libdrm util-linux

define MUOS_R35S_SESSION_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -Wall -Wextra -Werror -fPIE \
		$(@D)/muos-mount-namespace.c $(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now \
		-o $(@D)/mount-namespace
	for name in muos-run-bounded muos-rng-ready muos-root-writers muos-preferences; do \
		$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -Wall -Wextra -Werror -fPIE \
			$(@D)/$$name.c $(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now -o $(@D)/$$name || exit 1; \
	done
	$(TARGET_CC) $(TARGET_CFLAGS) -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -fPIE \
		-I$(STAGING_DIR)/usr/include/libdrm $(@D)/muos-drm-mode-probe.c \
		$(TARGET_LDFLAGS) -pie -Wl,-z,relro,-z,now -ldrm -o $(@D)/muos-drm-mode-probe
endef

define MUOS_R35S_SESSION_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/libexec/muos-session
	mkdir -p $(TARGET_DIR)/usr/libexec/muos-session/bin
	for name in muos-run-bounded muos-rng-ready muos-root-writers muos-drm-mode-probe muos-preferences; do \
		$(INSTALL) -m 0755 $(@D)/$$name $(TARGET_DIR)/usr/libexec/muos-session/bin/$$name || exit 1; \
	done
	cp -a $(@D)/service/. $(TARGET_DIR)/usr/libexec/muos-session/
	$(INSTALL) -m 0755 $(@D)/mount-namespace $(TARGET_DIR)/usr/libexec/muos-session/mount-namespace
	cd $(TARGET_DIR)/usr/libexec/muos-session && \
		find . -type f ! -name 'payload.sha256' -print | LC_ALL=C sort | \
		while IFS= read -r file; do sha256sum "$$file" || exit 1; done > payload.sha256
	$(INSTALL) -D -m 0644 $(@D)/muos-session.default $(TARGET_DIR)/etc/default/muos-session
	$(INSTALL) -D -m 0644 $(@D)/LICENSE $(TARGET_DIR)/usr/share/licenses/muos-r35s-session/LICENSE
endef

define MUOS_R35S_SESSION_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(@D)/S98muos-session $(TARGET_DIR)/etc/init.d/S98muos-session
endef

$(eval $(generic-package))
