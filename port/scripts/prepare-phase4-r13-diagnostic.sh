#!/usr/bin/env bash
# User-supplied Hardkernel ZIP, verified before extraction. Diagnostic only.
# No firmware image, redistribution approval or installed-system changes.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
candidate="$work/graphics-config"
out="$work/mali-r13"
[[ $(cat "$candidate/audit.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
python3 - "$candidate" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys,zipfile
c,out=map(Path,sys.argv[1:])
archive=out/'rk3326_r13p0_gbm_with_vulkan_and_cl.zip'
with archive.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()=='ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9'
with zipfile.ZipFile(archive) as z:
 data=z.read('libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl')
assert hashlib.sha256(data).hexdigest()=='2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea'
assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()=='2083f5386c201abc8f2e697e8004a14e59524a86'
(out/'libmali-r13-original.so').write_bytes(data)
with (c/'output/images/rootfs.ext4').open('rb') as f:
 assert hashlib.file_digest(f,'sha256').hexdigest()==json.loads((c/'audit/host-audit.json').read_text())['rootfs']['ext4']['sha256']
assert not (out/'diagnostic-rootfs').exists(), 'Use fresh staging; do not mix variants'
(out/'diagnostic-rootfs').mkdir()
PY
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
    "$(cat "$work/rootfs-container.iid")" sh -eu -c '
    c=/work/graphics-config
    out=/work/mali-r13
    sdk=$c/output/host
    target=$out/diagnostic-rootfs
    "$sdk/bin/fakeroot" -s "$out/diagnostic.fakeroot" \
        debugfs -R "rdump / $target" "$c/output/images/rootfs.ext4" > "$out/image-extract.log" 2>&1
    # One explicit overlay on the audited image, not a new Buildroot image.
    cp "$out/libmali-r13-original.so" "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
    chmod 755 "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
    # Match the candidate library contract without altering the source blob.
    "$sdk/bin/patchelf" --set-soname libmali.so.1 "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so"
    mkdir -p "$target/opt/port-probes"
    cp "$c/audit/graphics-contract" "$c/audit/gbm-contract" "$c/audit/drm-mode-probe" \
       "$c/audit/sdl-video-probe" "$target/opt/port-probes/"
    export PKG_CONFIG_LIBDIR="$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$sdk/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
    export PKG_CONFIG_SYSROOT_DIR="$sdk/aarch64-buildroot-linux-gnu/sysroot"
    "$sdk/bin/aarch64-buildroot-linux-gnu-gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
        /port/probes/phase4-egl-context.c $("$sdk/bin/pkg-config" --cflags --libs egl glesv2 gbm) \
        -Wl,-z,relro,-z,now -o "$target/opt/port-probes/egl-context"
    "$sdk/bin/aarch64-buildroot-linux-gnu-readelf" -h -d -V "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so" > "$out/libmali.elf.txt"
    # Resolve against exactly this overlay, without GPU nodes or SDL_Init.
    for probe in graphics-contract gbm-contract; do
        timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
            -E LD_BIND_NOW=1 "$target/opt/port-probes/$probe" > "$out/$probe-qemu.txt" 2>&1
    done
    timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
        -E LD_BIND_NOW=1 "$target/lib/ld-linux-aarch64.so.1" --list /work/mali-r13/diagnostic-rootfs/opt/port-probes/egl-context \
        > "$out/egl-context-loader-qemu.txt" 2>&1
    "$sdk/bin/fakeroot" -i "$out/diagnostic.fakeroot" tar -C "$target" --exclude=./dev --exclude=./proc --exclude=./sys \
        --exclude=./tmp --exclude=./run -czf "$out/diagnostic-staging.tar.gz" .
    ' > "$out/prepare.log" 2>&1
python3 - "$repo" "$candidate" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,c,out=map(Path,sys.argv[1:])
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
m={'scope':'private diagnostic overlay; not a rebuilt firmware image',
   'base_rootfs_sha256':json.loads((c/'audit/host-audit.json').read_text())['rootfs']['ext4']['sha256'],
   'source_blob_sha256':sha(out/'libmali-r13-original.so'),
   'installed_blob_sha256':sha(out/'diagnostic-rootfs/usr/lib/libmali-bifrost-g31-rxp0-gbm.so'),
   'staging_sha256':sha(out/'diagnostic-staging.tar.gz'),
   'port_inputs':{n:sha(repo/n) for n in ['port/probes/phase4-egl-context.c','port/scripts/prepare-phase4-r13-diagnostic.sh']},
   'qemu_contract_passed':True,'license_in_zip':False,'redistribution_approved':False,
   'native_context_tested':False,'native_display_tested':False,'boot_tested':False}
(out/'diagnostic-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
PY
echo 'R13 diagnostic overlay passed QEMU loader/contracts; no GPU runtime or firmware integration approval'
