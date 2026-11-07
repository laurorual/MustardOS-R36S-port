# Explicit private fork of the upstream recipe, loaded before package recipes.
# Override both sysroot and target with the same verified binary and API SDK.
override ROCKCHIP_MALI_VERSION = r13p0-private-2a067ea38256
override ROCKCHIP_MALI_SITE = /work/foundation/provider-source
override ROCKCHIP_MALI_SITE_METHOD = local
override ROCKCHIP_MALI_LICENSE = Proprietary (terms pending; private use only), MIT (API headers)
override ROCKCHIP_MALI_LICENSE_FILES = PRIVATE-NOTICE.txt
override ROCKCHIP_MALI_REDISTRIBUTE = NO
