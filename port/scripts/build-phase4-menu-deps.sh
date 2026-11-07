#!/usr/bin/env bash
# Extend the existing SDK additively. Historical artifacts remain immutable.
# The built-in UK10.6 Mali is a link SDK only; native tests require R13 overlay.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
[[ ! -e "$work/foundation/active" ]] || { echo "Foundation profile owns the mutable output; use its controllers." >&2; exit 1; }
menu="$work/menu"
name=muos-r35s-phase4-graphics
case "${1:-status}" in
 configure)
    [[ $(cat "$work/graphics-config/build.exit") == 0 ]]
    for job in "$name" muos-r35s-phase4-core muos-r35s-phase4-rootfs-legal muos-r35s-phase4-graphics-legal; do
        if podman container exists "$job"; then [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]; fi
    done
    [[ ! -e "$menu/active" ]]
    mkdir -p "$menu"
    cp "$work/graphics-config/output/.config" "$menu/baseline.config"
    cp "$work/graphics-config/report.json" "$menu/graphics-report.json"
    cp "$work/core/source-manifest.json" "$menu/core-source-manifest.json"
    cat "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" \
        "$repo/port/device/rk-r35s-p0/phase4-graphics.fragment" \
        "$repo/port/device/rk-r35s-p0/phase4-menu.fragment" > "$menu/menu.defconfig"
    # Freeze older entry points before changing this mutable build output.
    touch "$menu/active"
    podman run --rm --network=none --read-only --cap-drop=all --security-opt=no-new-privileges \
      --userns=keep-id --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
      -w /work/buildroot "$(cat "$work/rootfs-container.iid")" \
      make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot \
      BR2_DEFCONFIG=/work/menu/menu.defconfig defconfig > "$menu/configure.log" 2>&1
    python3 - "$repo" "$work" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,work=map(Path,sys.argv[1:]);menu=work/'menu'
def config(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if l.startswith('BR2_') and '=' in l)
a=config(menu/'baseline.config');b=config(work/'graphics-config/output/.config')
for k,v in a.items():
 if k not in ('BR2_DEFCONFIG',):assert b.get(k)==v,(k,v,b.get(k))
for k in ['SDL2_IMAGE','SDL2_MIXER','SDL2_TTF','HARFBUZZ','LIBPNG','LIBCURL','LIBARCHIVE','FFMPEG']:
 assert b.get('BR2_PACKAGE_'+k)=='y',k
assert b['BR2_PACKAGE_PROVIDES_LIBEGL']=='"rockchip-mali"'
r={'scope':'frontend dependencies; private R13 overlay required for runtime',
   'config_diff':{k:[a.get(k),v] for k,v in b.items() if a.get(k)!=v},
   'config_sha256':hashlib.sha256((work/'graphics-config/output/.config').read_bytes()).hexdigest(),
   'fragment_sha256':hashlib.sha256((repo/'port/device/rk-r35s-p0/phase4-menu.fragment').read_bytes()).hexdigest(),
   'native_mali_from_image_approved':False,'firmware_boot_tested':False}
(menu/'config-report.json').write_text(json.dumps(r,indent=2)+'\n')
PY
    ;;
 fetch|build)
    stage=$1
    [[ -f "$menu/active" && -f "$menu/config-report.json" ]]
    for job in "$name" muos-r35s-phase4-core muos-r35s-phase4-rootfs-legal muos-r35s-phase4-graphics-legal; do
        if podman container exists "$job"; then [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]; fi
    done
    if podman container exists "$name"; then podman rm "$name" >/dev/null; fi
    python3 - "$repo" "$work" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,sys
repo,work=map(Path,sys.argv[1:3]);m=work/'menu';r=json.loads((m/'config-report.json').read_text())
assert hashlib.sha256((work/'graphics-config/output/.config').read_bytes()).hexdigest()==r['config_sha256']
assert hashlib.sha256((repo/'port/device/rk-r35s-p0/phase4-menu.fragment').read_bytes()).hexdigest()==r['fragment_sha256']
assert (work/'core/source-manifest.json').read_bytes()==(m/'core-source-manifest.json').read_bytes()
for n,h in json.loads((m/'core-source-manifest.json').read_text())['port_input_sha256'].items():assert hashlib.sha256((repo/n).read_bytes()).hexdigest()==h,n
for n,h in json.loads((m/'graphics-report.json').read_text())['global_patch_sha256'].items():assert hashlib.sha256((repo/n).read_bytes()).hexdigest()==h,n
(m/(sys.argv[3]+'.exit')).unlink(missing_ok=True)
PY
    target=source; network=slirp4netns
    if [[ $stage == build ]]; then [[ $(cat "$menu/fetch.exit") == 0 ]]; target=all; network=none; fi
    epoch=$(git -C "$work/buildroot" show -s --format=%ct HEAD)
    podman run --detach --name "$name" --network="$network" --read-only \
      --cap-drop=all --security-opt=no-new-privileges --userns=keep-id --memory=12g --pids-limit=2048 \
      --tmpfs /tmp:rw,nosuid,nodev,size=2g -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
      -w /work/buildroot -e MENU_STAGE="$stage" -e MENU_TARGET="$target" -e SOURCE_DATE_EPOCH="$epoch" \
      "$(cat "$work/rootfs-container.iid")" sh -c '
      trap '\''rc=$?; printf "%s\n" "$rc" > /work/menu/"$MENU_STAGE".exit'\'' EXIT
      unset PKG_CONFIG_LIBDIR PKG_CONFIG_SYSROOT_DIR PKG_CONFIG_PATH
      make O=/work/graphics-config/output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
        BR2_JLEVEL=8 BR2_WGET="wget -nd -t 3 --connect-timeout=10 --read-timeout=30" "$MENU_TARGET" \
        > /work/menu/"$MENU_STAGE".log 2>&1
      '
    ;;
 status)
    [[ ! -f "$menu/active" ]] || { podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$name"; tail -4 "$menu/build.log" 2>/dev/null || :; }
    ;;
 *) echo 'Usage: configure|fetch|build|status' >&2; exit 2 ;;
esac
