#!/usr/bin/env bash
# Compile the same bounded menu harness against the completed new SDK.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/foundation/active" ]] || { echo "Foundation profile owns the mutable output; use its controllers." >&2; exit 1; }
[[ $(cat "$work/menu/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
python3 - "$repo" "$work/menu/source-manifest.json" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,manifest=map(Path,sys.argv[1:])
for p,h in json.loads(manifest.read_text())['port_inputs'].items():assert hashlib.sha256((repo/p).read_bytes()).hexdigest()==h,p
PY
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --memory=12g --pids-limit=2048 --tmpfs /tmp:rw,nosuid,nodev,size=2g \
 -v "$work:/work:rw,z" -w /work/menu/source "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 sdk=/work/graphics-config/output/host
 export PATH="$sdk/bin:$PATH"
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 cc=$sdk/bin/aarch64-buildroot-linux-gnu-gcc
 mkdir -p ../deps/objects
 for src in ../deps/mojibake-0.3.6/src/*.c; do
   "$cc" -std=c11 -O2 -mcpu=cortex-a35 -fPIE -I../deps/mojibake-0.3.6/src -c "$src" -o "../deps/objects/$(basename "$src" .c).o"
 done
 "$sdk/bin/aarch64-buildroot-linux-gnu-ar" rcs ../deps/libmojibake.a ../deps/objects/*.o
 make -f phase4-menu.mk -j8 CC="$cc" PKG_CONFIG="$sdk/bin/pkg-config" CFLAGS="-O2 -mcpu=cortex-a35"
 "$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -l -d -V ../phase4-menu > ../phase4-menu.elf.txt
 timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L /work/graphics-config/output/target \
   -E LD_BIND_NOW=1 ../phase4-menu --info > ../menu-info-qemu.txt 2>&1
 ' > "$work/menu/compile.log" 2>&1
printf '0\n' > "$work/menu/compile.exit"
echo 'Menu compiled against Buildroot; native input/display/audio still require a new test'
