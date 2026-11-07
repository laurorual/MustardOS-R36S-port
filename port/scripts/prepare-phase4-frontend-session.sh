#!/usr/bin/env bash
# Prepare a bounded full-UI session from the finalized private image.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
f="$work/frontend-session"
mkdir -p "$f"
[[ $(cat "$work/foundation/audit.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
python3 - "$work" <<'PY'
from pathlib import Path
import hashlib,json,sys
w=Path(sys.argv[1]);s=Path((w/'foundation/latest-staging').read_text().strip())
m=json.loads((s/'staging-manifest.json').read_text())
with (w/'graphics-config/output/images/rootfs.ext4').open('rb') as f:
 assert hashlib.file_digest(f,'sha256').hexdigest()==m['rootfs']['ext4']['sha256']
p=w/'foundation/core-manifest-upstream.json';b=p.read_bytes()
assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()=='016d9bdc27ff0389d3784e735385303aab0116e5'
assert isinstance(json.loads(b),dict)
scripts={'script/system/assign.sh':'be73840f57bf54ff2f389377294dcdcdeac191d2',
 'script/device/audio.sh':'1b1da45464ee74932f7712577888ea39fa08c70c',
 'script/device/bright.sh':'b0ac560cef5ef69460a5eaf15dfb7dd52f3c00af',
 'script/var/display.sh':'8046b335fa3f168d5bb352d8d2fae95013e54214',
 'script/var/governor.sh':'6c644a9e7af93c729d9583e97a750c56d5b2c624'}
for name,oid in scripts.items():
 data=(w.parents[1]/'refs/muos/internal'/name).read_bytes()
 assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()==oid,name
 p=w/'frontend-session/resources'/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(data);p.chmod(0o755)
(w/'frontend-session/resource-blobs.json').write_text(json.dumps(scripts,indent=2)+'\n')
PY
stage=$(mktemp -d "$f/staging.XXXXXX")
mkdir "$stage/rootfs"
export FRONTEND_STAGE_REL=${stage#"$work/"}
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
 --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -e FRONTEND_STAGE_REL \
 -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" "$(cat "$work/rootfs-container.iid")" sh -eu -c '
 stage=/work/$FRONTEND_STAGE_REL
 sdk=/work/graphics-config/output/host
 target=$stage/rootfs
 "$sdk/bin/fakeroot" -s "$stage/metadata.fakeroot" debugfs -R "rdump / $target" \
   /work/graphics-config/output/images/rootfs.ext4 > "$stage/image-extract.txt" 2>&1
 export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
 export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
 mkdir -p "$target/opt/port-probes" "$target/opt/muos/share/info/manifest"
 "$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
   /port/utils/muos-sdl-map.c $("$sdk/bin/pkg-config" --cflags --libs sdl2) \
   -Wl,-z,relro,-z,now -o "$target/opt/port-probes/muos-sdl-map"
 "$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
   /port/probes/phase4-egl-context.c $("$sdk/bin/pkg-config" --cflags --libs egl glesv2 gbm) \
   -Wl,-z,relro,-z,now -o "$target/opt/port-probes/egl-context"
 "$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
   /port/probes/phase4-frontend-contract.c -ldl -Wl,-z,relro,-z,now -o "$target/opt/port-probes/frontend-contract"
 cp /work/foundation/core-manifest-upstream.json "$target/opt/muos/share/info/manifest/core.json"
 cp -a /work/frontend-session/resources/script/. "$target/opt/muos/script/"
 # Native volume route fix under test; source delta and binaries are recorded.
 cp -a /work/foundation/frontend-bin/. "$target/opt/muos/frontend/"
 timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
   -E LD_BIND_NOW=1 "$target/opt/port-probes/muos-sdl-map" --info > "$stage/mapper-info-qemu.txt"
 "$sdk/bin/fakeroot" -i "$stage/metadata.fakeroot" tar -C "$target" --exclude=./dev --exclude=./proc \
   --exclude=./sys --exclude=./tmp --exclude=./run -czf "$stage/core-staging.tar.gz" .
 ' > "$stage/prepare.log" 2>&1
python3 - "$repo" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,s=map(Path,sys.argv[1:]);w=repo/'build/phase4'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=Path((w/'foundation/latest-staging').read_text().strip())
m={'scope':'bounded full UI from private foundation image; diagnostic helpers and pinned core manifest added',
   'base_foundation':json.loads((base/'staging-manifest.json').read_text()),
   'staging_sha256':sha(s/'core-staging.tar.gz'),
   'qemu_mapper_link_passed':True,'firmware_boot_tested':False,'redistribution_approved':False,
   'frontend_sha256':sha(s/'rootfs/opt/muos/frontend/muxfrontend'),
   'core_manifest_git_blob':'016d9bdc27ff0389d3784e735385303aab0116e5',
   'runtime_resource_blobs':json.loads((w/'frontend-session/resource-blobs.json').read_text()),
   'board_delta':'0006: normalized virtual volume only; raw PMIC index unchanged',
   'frontend_overlay_sha256':{str(p.relative_to(s/'rootfs/opt/muos/frontend')):sha(p)
      for p in (s/'rootfs/opt/muos/frontend').rglob('*') if p.is_file()},
   'helpers_sha256':{p.name:sha(p) for p in (s/'rootfs/opt/port-probes').iterdir()},
   'port_inputs':{p:sha(repo/p) for p in ['port/utils/muos-sdl-map.c','port/scripts/prepare-phase4-frontend-session.sh',
      'port/patches/0006-frontend-r35s-normalized-volume.patch','port/scripts/compile-phase4-frontend.sh']}}
(s/'staging-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(w/'frontend-session/latest-staging').write_text(str(s)+'\n')
print('Private full-UI staging prepared:',s)
PY
