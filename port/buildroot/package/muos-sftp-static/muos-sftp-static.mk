# SPDX-License-Identifier: MIT
# M4g: the SFTP jail's server (decision 6). Upstream web/service.sh runs the
# menu's SFTP as dropbear -G muos -c /opt/muos/frontend/musftpjail; the jail
# chroots into a tmpfs of bind mounts and fexecve()s
# /opt/muos/bin/aarch64/sftp-server, so that server must be static. Same
# source as Buildroot's gesftpserver (the unjailed /usr/libexec/sftp-server
# of the developer SSH stays), linked with -static.
# Also the jail's account (upstream: adduser muos, its fixed password hash
# = "muos") and modes: musftpjail (pinned input) root:muos 4750, the jail
# mount point /opt/muos/browse on the read-only root.
MUOS_SFTP_STATIC_VERSION = $(GESFTPSERVER_VERSION)
MUOS_SFTP_STATIC_SOURCE = $(GESFTPSERVER_SOURCE)
MUOS_SFTP_STATIC_SITE = $(GESFTPSERVER_SITE)
MUOS_SFTP_STATIC_DL_SUBDIR = gesftpserver
MUOS_SFTP_STATIC_LICENSE = GPL-2.0+
MUOS_SFTP_STATIC_LICENSE_FILES = COPYING
MUOS_SFTP_STATIC_DEPENDENCIES = gesftpserver $(if $(BR2_ENABLE_LOCALE),,libiconv)
MUOS_SFTP_STATIC_CONF_OPTS = --disable-warnings-as-errors
MUOS_SFTP_STATIC_CONF_ENV = \
	CFLAGS="$(TARGET_CFLAGS) -std=c99" \
	LDFLAGS="$(TARGET_LDFLAGS) -static" \
	LIBS=-lpthread \
	rjk_cv_python3=false

define MUOS_SFTP_STATIC_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/gesftpserver $(TARGET_DIR)/opt/muos/bin/aarch64/sftp-server
	$(TARGET_STRIP) $(TARGET_DIR)/opt/muos/bin/aarch64/sftp-server
	mkdir -p $(TARGET_DIR)/opt/muos/browse
endef

define MUOS_SFTP_STATIC_USERS
	muos 1000 muos 1000 $$6$$mustardos-sftp$$O1GeNl3WBlgGa8GMlPboh3sLE7FEYsKY28gu3kjDf9QAE8KWRcEXpKlVDlLqccFkS8y3CKfS7Hc8OTCb8LnJo/ - /bin/sh - muOS SFTP (jailed)
endef

define MUOS_SFTP_STATIC_PERMISSIONS
	/opt/muos/frontend/musftpjail f 4750 0 1000 - - - - -
	/opt/muos/browse d 755 0 0 - - - - -
endef

$(eval $(autotools-package))
