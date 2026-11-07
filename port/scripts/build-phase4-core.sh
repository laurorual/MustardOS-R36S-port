#!/usr/bin/env bash
# Continue the existing fixed sysroot with explicitly additive packages only.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work="$repo/build/phase4"
name=muos-r35s-phase4-core
case "${1:-status}" in
    prepare)
        for job in "$name" muos-r35s-phase4-rootfs muos-r35s-phase4-rootfs-legal muos-r35s-phase4-graphics muos-r35s-phase4-graphics-legal; do
            if podman container exists "$job"; then
                [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
            fi
        done
        [[ $(cat "$work/rootfs-build.exit") == 0 ]]
        [[ $(git -C "$work/buildroot" rev-parse HEAD) == 4f924fd52841608d68ac3dcb83fccee8b8c90316 ]]
        mkdir -p "$work/core"
        python3 "$repo/port/scripts/prepare-phase4-core.py"
        if [[ ! -f "$work/core/baseline.config" ]]; then
            cp "$work/rootfs-output/.config" "$work/core/baseline.config"
        fi
        cat "$repo/port/device/rk-r35s-p0/phase4-rootfs.defconfig" > "$work/core/core.defconfig"
        printf '\nBR2_PACKAGE_MUOS_CORE=y\n' >> "$work/core/core.defconfig"
        podman run --rm --network=none --read-only --cap-drop=all --userns=keep-id \
            --tmpfs /tmp:rw,nosuid,nodev -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
            -w /work/buildroot "$(cat "$work/rootfs-container.iid")" \
            make O=/work/rootfs-output BR2_EXTERNAL=/port/buildroot \
            BR2_DEFCONFIG=/work/core/core.defconfig defconfig > "$work/core/configure.log" 2>&1
        if rg -q 'error:|recursive dependency' "$work/core/configure.log"; then
            cat "$work/core/configure.log" >&2; exit 1
        fi
        python3 - "$work/core/baseline.config" "$work/rootfs-output/.config" <<'PY'
from pathlib import Path
import json, sys
def config(path):
    return dict(line.split('=',1) for line in Path(path).read_text().splitlines() if line.startswith('BR2_') and '=' in line)
a,b=map(config,sys.argv[1:])
changed={key:[a.get(key),b.get(key)] for key in a.keys()|b.keys() if a.get(key)!=b.get(key)}
allowed={'BR2_DEFCONFIG','BR2_PACKAGE_MUOS_CORE','BR2_PACKAGE_JQ','BR2_PACKAGE_PROCPS_NG',
         'BR2_EXTERNAL_NAMES','BR2_EXTERNAL_MUOS_R35S_PATH','BR2_EXTERNAL_MUOS_R35S_VERSION'}
assert not (changed.keys()-allowed), changed
assert all(b.get(k)=='y' for k in ['BR2_PACKAGE_MUOS_CORE','BR2_PACKAGE_JQ','BR2_PACKAGE_PROCPS_NG'])
Path(sys.argv[2]).parent.parent.joinpath('core/config-diff.json').write_text(json.dumps(changed,indent=2)+'\n')
print('Additive config verified: toolchain, headers, libc and filesystem settings unchanged')
PY
        touch "$work/core/active"
        ;;
    fetch|build)
        stage=$1
        [[ -f "$work/core/active" ]]
        for job in muos-r35s-phase4-rootfs muos-r35s-phase4-rootfs-legal muos-r35s-phase4-graphics muos-r35s-phase4-graphics-legal; do
            if podman container exists "$job"; then
                [[ $(podman inspect --format '{{.State.Running}}' "$job") == false ]]
            fi
        done
        if podman container exists "$name"; then
            [[ $(podman inspect --format '{{.State.Running}}' "$name") == false ]]
            podman rm "$name" >/dev/null
        fi
        python3 - "$repo" "$work/core/source-manifest.json" <<'PY'
from pathlib import Path
import json, hashlib, sys
repo=Path(sys.argv[1]);m=json.load(open(sys.argv[2]))
for name,sha in m['port_input_sha256'].items():
    assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha, name
PY
        network=none; target=all
        if [[ $stage == fetch ]]; then network=slirp4netns; target=source; fi
        if [[ $stage == build ]]; then [[ $(cat "$work/core/fetch.exit") == 0 ]]; fi
        rm -f "$work/core/$stage.exit"
        epoch=$(git -C "$work/buildroot" show -s --format=%ct HEAD)
        podman run --detach --name "$name" --network="$network" --read-only \
            --cap-drop=all --security-opt=no-new-privileges --userns=keep-id --memory=12g --pids-limit=2048 \
            --tmpfs /tmp:rw,nosuid,nodev,size=2g -v "$work:/work:rw,z" -v "$repo/port:/port:ro,z" \
            -w /work/buildroot -e CORE_STAGE="$stage" -e CORE_TARGET="$target" \
            -e SOURCE_DATE_EPOCH="$epoch" \
            "$(cat "$work/rootfs-container.iid")" sh -c '
            if [ "$CORE_STAGE" = build ]; then
                make O=/work/rootfs-output BR2_EXTERNAL=/port/buildroot \
                    muos-core-dirclean > /work/core/build.log 2>&1 || exit 1
            fi
            make O=/work/rootfs-output BR2_EXTERNAL=/port/buildroot BR2_DL_DIR=/work/rootfs-downloads \
                BR2_JLEVEL=8 BR2_WGET="wget -nd -t 3 --connect-timeout=10 --read-timeout=30" \
                "$CORE_TARGET" >> /work/core/"$CORE_STAGE".log 2>&1
            result=$?
            printf "%s\n" "$result" > /work/core/"$CORE_STAGE".exit
            exit "$result"
            '
        ;;
    status)
        if podman container exists "$name"; then
            podman inspect --format 'running={{.State.Running}} exit={{.State.ExitCode}}' "$name"
            for stage in fetch build; do
                if [[ -f "$work/core/$stage.log" ]]; then
                    echo "$stage:"
                    tail -3 "$work/core/$stage.log" | cut -c1-200
                fi
            done
        else echo 'No core build container; run prepare, fetch, build.'; fi
        ;;
    *) echo 'Usage: prepare|fetch|build|status' >&2; exit 2 ;;
esac
