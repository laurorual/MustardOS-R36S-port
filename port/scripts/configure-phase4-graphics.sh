#!/usr/bin/env bash
# Resolve a separate candidate config. Never change the tested core output.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/menu/active" ]] || { echo "Menu profile owns the mutable graphics output; use its controllers." >&2; exit 1; }
[[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
[[ -f "$work/core/active" && $(cat "$work/core/build.exit") == 0 ]]
[[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-core) == false ]]
if podman container exists muos-r35s-phase4-graphics; then
    [[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics) == false ]]
fi
if podman container exists muos-r35s-phase4-graphics-legal; then
    [[ $(podman inspect --format '{{.State.Running}}' muos-r35s-phase4-graphics-legal) == false ]]
fi
mkdir -p "$work/graphics-config"
cat "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" \
    "$repo/port/device/rk-r35s-p0/phase4-graphics.fragment" > "$work/graphics-config/candidate.defconfig"
before=$(sha256sum "$work/rootfs-output/.config")
podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
    --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev \
    -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
    -w /work/buildroot "$(cat "$work/rootfs-container.iid")" \
    make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot \
        BR2_DEFCONFIG=/work/graphics-config/candidate.defconfig defconfig \
        > "$work/graphics-config/configure.log" 2>&1
[[ $before == "$(sha256sum "$work/rootfs-output/.config")" ]]
if rg -q 'error:|recursive dependency' "$work/graphics-config/configure.log"; then
    cat "$work/graphics-config/configure.log" >&2; exit 1
fi
python3 - "$work" <<'PY'
from pathlib import Path
import hashlib, json, sys
work=Path(sys.argv[1])
def config(path):
    return dict(line.split('=',1) for line in path.read_text().splitlines() if line.startswith('BR2_') and '=' in line)
base=config(work/'rootfs-output/.config')
candidate=config(work/'graphics-config/output/.config')
required=['BR2_PACKAGE_MUOS_CORE','BR2_PACKAGE_ROCKCHIP_MALI','BR2_PACKAGE_LIBDRM',
          'BR2_PACKAGE_HAS_LIBEGL','BR2_PACKAGE_HAS_LIBGLES','BR2_PACKAGE_HAS_LIBGBM',
          'BR2_PACKAGE_SDL2','BR2_PACKAGE_SDL2_KMSDRM','BR2_PACKAGE_SDL2_OPENGLES']
assert all(candidate.get(key)=='y' for key in required)
assert all(candidate.get('BR2_PACKAGE_PROVIDES_'+key)=='"rockchip-mali"' for key in ['LIBEGL','LIBGLES','LIBGBM'])
assert 'BR2_LINUX_KERNEL' not in candidate and 'BR2_PACKAGE_MALI_DRIVER' not in candidate
assert 'BR2_PACKAGE_SDL2_X11' not in candidate and 'BR2_PACKAGE_WAYLAND' not in candidate
for key in base.keys() | candidate.keys():
    if key.startswith(('BR2_TOOLCHAIN','BR2_GCC','BR2_BINUTILS','BR2_KERNEL_HEADERS','BR2_LINUX_KERNEL_CUSTOM','BR2_GLIBC')):
        assert base.get(key)==candidate.get(key), key
diff={key:[base.get(key),candidate.get(key)] for key in base.keys() | candidate.keys() if base.get(key)!=candidate.get(key)}
report={'scope':'Kconfig only; no package download, compilation, GPU access or firmware image',
        'core_config_preserved':True,'providers':{key:candidate['BR2_PACKAGE_PROVIDES_'+key] for key in ['LIBEGL','LIBGLES','LIBGBM']},
        'config_diff':diff,'graphics_runtime_tested':False,'candidate_kernel_tested':False}
repo=work.parents[1]
report['global_patch_sha256']={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((repo/'port/patches/phase4-graphics').rglob('*.patch'))}
(work/'graphics-config/report.json').write_text(json.dumps(report,indent=2)+'\n')
(work/'graphics-config/core-source-manifest.json').write_bytes((work/'core/source-manifest.json').read_bytes())
print('Graphics candidate Kconfig passed; tested core config preserved; no graphics build or runtime test')
PY
