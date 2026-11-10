################################################################################
# muos-r35s-batch -- original MIT helpers and exact qualified C120 shell bundle
################################################################################
MUOS_R35S_BATCH_VERSION = 122
MUOS_R35S_BATCH_SITE = $(if $(strip $(MUOS_R35S_BATCH_PAYLOAD)),$(MUOS_R35S_BATCH_PAYLOAD),/nonexistent/muos-r35s-batch-qualified-payload-required)
MUOS_R35S_BATCH_SITE_METHOD = local
MUOS_R35S_BATCH_LICENSE = MIT
MUOS_R35S_BATCH_LICENSE_FILES = LICENSE
MUOS_R35S_BATCH_DEPENDENCIES = muos-r35s-session
# Supply the public target prefix, separate export.sha256 and its expected digest.
# No host ROM, private provisioning, toolchain rebuild or full image is required.
MUOS_R35S_BATCH_FILES = functions.sh host.sh contract.json LICENSE payload.sha256 caller.sh resident-functions.sh resident.sha256 load.sh

define MUOS_R35S_BATCH_INSTALL_TARGET_CMDS
	test -n "$(MUOS_R35S_BATCH_PAYLOAD)" -a -n "$(MUOS_R35S_BATCH_MANIFEST)" -a -n "$(MUOS_R35S_BATCH_MANIFEST_SHA256)"
	printf '%s  %s\n' '$(MUOS_R35S_BATCH_MANIFEST_SHA256)' '$(MUOS_R35S_BATCH_MANIFEST)' | sha256sum -c -
	test "$$(find '$(MUOS_R35S_BATCH_PAYLOAD)' -mindepth 1 -maxdepth 1 -print | wc -l)" = 9
	test "$$(awk '{print $$2}' '$(MUOS_R35S_BATCH_MANIFEST)')" = "$$(printf '%s\n' $(MUOS_R35S_BATCH_FILES))"
	(cd '$(MUOS_R35S_BATCH_PAYLOAD)' && sha256sum -c '$(MUOS_R35S_BATCH_MANIFEST)')
	$(INSTALL) -d -m 0755 $(TARGET_DIR)/usr/libexec/muos-batch-v1
	for f in $(MUOS_R35S_BATCH_FILES); do $(INSTALL) -D -m 0644 '$(MUOS_R35S_BATCH_PAYLOAD)'/$$f '$(TARGET_DIR)'/usr/libexec/muos-batch-v1/$$f || exit 1; done
endef

$(eval $(generic-package))
