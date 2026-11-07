#!/usr/bin/env bash
# Stage a new, checked frontend diagnostic in RAM-ready form; never flash it.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/foundation/active" ]] || { echo "Foundation profile owns the mutable output; use its controllers." >&2; exit 1; }
menu="$work/menu"
[[ $(cat "$menu/build.exit") == 0 && $(cat "$menu/compile.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
stage=$(mktemp -d "$menu/staging.XXXXXX")
mkdir "$stage/rootfs"
printf '%s\n' "$stage" > "$menu/latest-staging-attempt"
python3 "$repo/port/scripts/verify-phase4-rootfs.py" "$work/graphics-config/output" > "$stage/base-rootfs-audit.json"
python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import hashlib,json,sys,zipfile
repo,work=map(Path,sys.argv[1:])
for name,h in json.loads((work/'menu/source-manifest.json').read_text())['port_inputs'].items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==h,name
z=work/'mali-r13/rk3326_r13p0_gbm_with_vulkan_and_cl.zip'
with z.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9'
with zipfile.ZipFile(z) as archive:data=archive.read('libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl')
assert hashlib.sha256(data).hexdigest()=='2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea'
(work/'menu/libmali-private-original.so').write_bytes(data)
PY
export MENU_STAGE_REL=${stage#"$work/"}
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -e MENU_STAGE_REL \
 -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 stage=/work/$MENU_STAGE_REL
 sdk=/work/graphics-config/output/host
 target=$stage/rootfs
 "$sdk/bin/fakeroot" -s "$stage/metadata.fakeroot" debugfs -R "rdump / $target" \
   /work/graphics-config/output/images/rootfs.ext4 > "$stage/image-extract.log" 2>&1
 cp -a /work/menu/assets/. "$target/"
 mkdir -p "$target/opt/muos/frontend" "$target/usr/share/licenses/menu-probe" "$target/opt/port-probes"
 cp /work/menu/phase4-menu "$target/opt/muos/frontend/"
 cp /work/menu/source/LICENSE "$target/usr/share/licenses/menu-probe/frontend-LICENSE"
 cp /work/menu/deps/mojibake-0.3.6/LICENSE "$target/usr/share/licenses/menu-probe/mojibake-LICENSE"
 # Explicit private replacement; its redistribution terms are not established.
 cp /work/menu/libmali-private-original.so "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
 chmod 755 "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
 "$sdk/bin/patchelf" --set-soname libmali.so.1 "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 "$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
   /port/probes/phase4-egl-context.c $("$sdk/bin/pkg-config" --cflags --libs egl glesv2 gbm) \
   -Wl,-z,relro,-z,now -o "$target/opt/port-probes/egl-context"
 timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   -E LD_BIND_NOW=1 "$target/opt/muos/frontend/phase4-menu" --info > "$stage/menu-info-qemu.txt" 2>&1
 e2fsck -fn /work/graphics-config/output/images/rootfs.ext4 > "$stage/base-e2fsck.txt" 2>&1
 ' > "$stage/prepare.log" 2>&1
python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import json,sys
repo,stage=map(Path,sys.argv[1:]);base=stage/'rootfs/opt/muos'
# Keep the tested RK817 service/sink profile after exporting common resources.
core=json.loads((repo/'port/device/rk-r35s-p0/core-config.json').read_text())
for ns,values in core.items():
 root=base/{'device':'device/config','global':'config','system':'config/system'}[ns]
 for name,value in values.items():
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value+'\n')
PY
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -e MENU_STAGE_REL -v "$work:/work:rw,z" \
 "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 stage=/work/$MENU_STAGE_REL
 /work/graphics-config/output/host/bin/fakeroot -i "$stage/metadata.fakeroot" \
   tar -C "$stage/rootfs" --exclude=./dev --exclude=./proc --exclude=./sys --exclude=./tmp --exclude=./run \
   -czf "$stage/menu-staging.tar.gz" .
 '
python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,stage=map(Path,sys.argv[1:])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
m={'scope':'private frontend/runtime overlay, not a firmware image',
   'base_rootfs':json.loads((stage/'base-rootfs-audit.json').read_text()),
   'staging_sha256':sha(stage/'menu-staging.tar.gz'),
   'menu_sha256':sha(stage/'rootfs/opt/muos/frontend/phase4-menu'),
   'mali_source_sha256':'2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea',
   'mali_runtime_sha256':sha(stage/'rootfs/usr/lib/libmali-bifrost-g31-rxp0-gbm.so'),
   'qemu_link_load_passed':True,'native_frontend_tested':False,
   'mali_redistribution_approved':False,'firmware_boot_tested':False}
(stage/'staging-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(repo/'build/phase4/menu/latest-staging').write_text(str(stage)+'\n')
PY
echo "Private menu staging checked: $stage"
