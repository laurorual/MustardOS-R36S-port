#!/usr/bin/env bash
# Compile only original lifecycle code for the already pinned SDK.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
out="$work/init-services"
mkdir -p "$out/bin"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
 "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 sdk=/work/graphics-config/output/host
 cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 for pair in "utils/muos-ui-supervisor.c muos-ui-supervisor" "diagnostics/service-child.c service-child"; do
  set -- $pair
  "$cc" -std=c11 -D_GNU_SOURCE -O2 -mcpu=cortex-a35 -Wall -Wextra -Werror -fPIE \
    "/port/$1" -pie -Wl,-z,relro,-z,now -o "/work/init-services/bin/$2"
 done
 "$cc" -std=c11 -D_GNU_SOURCE -O2 -mcpu=cortex-a35 -Wall -Wextra -Werror -fPIE \
    /port/utils/muos-sdl-map.c $("$sdk/bin/pkg-config" --cflags --libs sdl2) \
    -pie -Wl,-z,relro,-z,now -o /work/init-services/bin/muos-sdl-map
 target=/work/graphics-config/output/target
 timeout 10 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   -E LD_BIND_NOW=1 /work/init-services/bin/muos-ui-supervisor --status && exit 1
 test "$?" = 3
 ' > "$out/build.log" 2>&1
python3 - "$repo" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
r,o=map(Path,sys.argv[1:]);names=['port/utils/muos-ui-supervisor.c','port/diagnostics/service-child.c',
 'port/device/rk-r35s-p0/S96muos-input-ready','port/device/rk-r35s-p0/S99muos-ui','port/scripts/build-phase4-init-services.sh',
 'port/device/rk-r35s-p0/S95muos-foundation-core','port/utils/muos-sdl-map.c']
m={'sdk':'build/phase4/graphics-config/output/host','qemu_status_without_runtime':3,
   'inputs':{p:hashlib.sha256((r/p).read_bytes()).hexdigest() for p in names},
   'bin_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (o/'bin').iterdir()},
   'native_tested':False,'boot_tested':False}
(o/'build-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Native init service binaries compiled; missing-runtime status3 verified under QEMU')
PY
