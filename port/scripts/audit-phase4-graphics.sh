#!/usr/bin/env bash
# Host/QEMU audit of the separate candidate. No SSH or hardware access.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
python3 - "$work/graphics-config/audit.exit" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).unlink(missing_ok=True)
PY
[[ $(cat "$work/graphics-config/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
mkdir -p "$work/graphics-config/audit"
python3 "$repo/port/scripts/verify-phase4-rootfs.py" "$work/graphics-config/output" \
    > "$work/graphics-config/audit/rootfs.json"
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" \
    -v "$repo/port:/port:ro,z" "$(cat "$work/rootfs-container.iid")" sh -eu -c '
    out=/work/graphics-config/output
    target=$out/target
    audit=/work/graphics-config/audit
    prefix=$out/host/bin/aarch64-buildroot-linux-gnu-
    # The build image defaults pkg-config to native amd64 for host tools.
    # Override it explicitly when querying this target SDK outside make.
    export PKG_CONFIG_LIBDIR="$out/host/aarch64-buildroot-linux-gnu/sysroot/usr/lib/pkgconfig:$out/host/aarch64-buildroot-linux-gnu/sysroot/usr/share/pkgconfig"
    export PKG_CONFIG_SYSROOT_DIR="$out/host/aarch64-buildroot-linux-gnu/sysroot"
    "$out/host/bin/pkg-config" --modversion sdl2 egl glesv2 gbm libdrm > "$audit/pkgconfig-versions.txt"
    "$out/host/bin/pkg-config" --cflags --libs sdl2 egl glesv2 gbm libdrm > "$audit/link-flags.txt"
    "$out/host/bin/aarch64-buildroot-linux-gnu-gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
        /port/probes/phase4-gbm-contract.c $("$out/host/bin/pkg-config" --cflags --libs gbm) \
        -Wl,-z,relro,-z,now -o "$audit/gbm-contract"
    "${prefix}gcc" -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
        /port/probes/phase4-graphics-contract.c -Wl,--no-as-needed \
        $("$out/host/bin/pkg-config" --cflags --libs sdl2 egl glesv2 gbm libdrm) \
        -ldl -Wl,-z,relro,-z,now -o "$audit/graphics-contract"
    "${prefix}readelf" -h -l -d -V "$audit/graphics-contract" > "$audit/graphics-contract.elf.txt"
    # Rebuild the existing bounded physical probes for this sysroot; do not
    # execute their hardware paths in this host audit.
    "${prefix}gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
        /port/diagnostics/sdl-video-probe.c $("$out/host/bin/pkg-config" --cflags --libs sdl2) \
        -Wl,-z,relro,-z,now -o "$audit/sdl-video-probe"
    "${prefix}gcc" -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror -O2 -mcpu=cortex-a35 \
        /port/diagnostics/drm-mode-probe.c $("$out/host/bin/pkg-config" --cflags --libs libdrm) \
        -Wl,-z,relro,-z,now -o "$audit/drm-mode-probe"
    for probe in sdl-video-probe drm-mode-probe; do
        "${prefix}readelf" -h -l -d -V "$audit/$probe" > "$audit/$probe.elf.txt"
    done
    "${prefix}readelf" -h -d -V "$target/usr/lib/libmali-bifrost-g31-rxp0-gbm.so" > "$audit/libmali.elf.txt"
    timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
        -E LD_BIND_NOW=1 "$audit/graphics-contract" > "$audit/graphics-contract-qemu.txt" 2>&1
    timeout 30 env -i PATH=/usr/bin:/bin qemu-aarch64 -cpu cortex-a35 -L "$target" \
        -E LD_BIND_NOW=1 "$audit/gbm-contract" > "$audit/gbm-contract-qemu.txt" 2>&1
    e2fsck -fn "$out/images/rootfs.ext4" > "$audit/e2fsck.txt" 2>&1
    ' > "$work/graphics-config/audit/run.log" 2>&1
python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import hashlib, json, sys
repo,work=map(Path,sys.argv[1:])
inputs=['port/probes/phase4-graphics-contract.c','port/probes/phase4-gbm-contract.c','port/diagnostics/sdl-video-probe.c',
        'port/diagnostics/drm-mode-probe.c','port/scripts/audit-phase4-graphics.sh']
record={'scope':'host static and QEMU link/load only; no hardware runtime',
        'rootfs':json.loads((work/'graphics-config/audit/rootfs.json').read_text()),
        'input_sha256':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in inputs},
        'qemu_cpu':'cortex-a35','ld_bind_now':True,'gpu_devices_exposed':False,
        'qemu_link_load_passed':True,'native_graphics_tested':False}
(work/'graphics-config/audit/host-audit.json').write_text(json.dumps(record,indent=2)+'\n')
(work/'graphics-config/audit.exit').write_text('0\n')
PY
echo 'Graphics candidate static/link/load/QEMU audit passed; hardware runtime untested'
